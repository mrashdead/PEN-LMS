from __future__ import annotations

import logging
import uuid
from typing import Optional

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

from apps.workflow.models import ActionLog, Instance, State, Transition, WorkflowDefinition

logger = logging.getLogger(__name__)


class WorkflowEngineError(Exception):
    """Base exception for workflow engine errors."""


class InvalidTransitionError(WorkflowEngineError):
    """Transition not allowed from current state or by this actor."""


class WorkflowNotActiveError(WorkflowEngineError):
    """Workflow definition is not active."""


class InstanceNotRunningError(WorkflowEngineError):
    """Instance is not in running state."""


class WorkflowEngineService:
    """
    Core service for executing workflow transitions.
    Thread-safe: uses select_for_update inside transactions.
    """

    # ------------------------------------------------------------------
    # Create Instance
    # ------------------------------------------------------------------

    @transaction.atomic
    def create_instance(
        self,
        workflow_code: str,
        requester: settings.AUTH_USER_MODEL,  # type: ignore[valid-type]
        title: str,
        description: str = "",
    ) -> Instance:
        """
        Create a new workflow instance and an initial task for the first state.

        Steps:
          1. Load + lock the WorkflowDefinition
          2. Find the initial State
          3. Create the Instance
          4. Create the first ActionLog
          5. Create a WorkflowTask for the initial state's assignee pool
        """
        wf = (
            WorkflowDefinition.objects.select_for_update()
            .filter(code=workflow_code.strip().lower())
            .first()
        )
        if not wf:
            raise WorkflowEngineError(f"Workflow '{workflow_code}' not found.")
        if not wf.is_active:
            raise WorkflowNotActiveError(f"Workflow '{workflow_code}' is not active.")

        initial_state = (
            State.objects.select_for_update()
            .filter(workflow_definition=wf, is_initial=True)
            .first()
        )
        if not initial_state:
            raise WorkflowEngineError(
                f"Workflow '{workflow_code}' has no initial state."
            )

        instance = Instance.objects.create(
            workflow_definition=wf,
            current_state=initial_state,
            requester=requester,
            title=title,
            description=description,
            status=Instance.Status.RUNNING,
        )

        # Log the creation action
        ActionLog.objects.create(
            instance=instance,
            from_state=None,
            to_state=initial_state,
            action="create",
            actor=requester,
            comment="Instance created",
        )

        # Create the first task for the initial state
        self._create_tasks_for_state(instance, initial_state, assigned_by=requester)

        logger.info(
            "Instance %s created for workflow '%s' by %s",
            instance.id,
            workflow_code,
            requester,
        )
        return instance

    # ------------------------------------------------------------------
    # Get Available Transitions
    # ------------------------------------------------------------------

    def get_available_transitions(
        self,
        instance: Instance,
        actor: settings.AUTH_USER_MODEL,  # type: ignore[valid-type]
    ) -> list[Transition]:
        """
        Return transitions the actor can perform on this instance.
        Checks:
          - Instance is running
          - Transition from current state
          - Actor has required role (via role_codes)
        """
        if instance.status != Instance.Status.RUNNING:
            return []

        if not instance.current_state_id:
            return []

        transitions = list(
            Transition.objects.filter(
                workflow_definition=instance.workflow_definition,
                from_state=instance.current_state,
            ).select_related("to_state")
        )

        actor_roles = actor.role_codes()
        allowed: list[Transition] = []
        for t in transitions:
            if not t.allowed_role_codes:
                allowed.append(t)
                continue
            if any(role in actor_roles for role in t.allowed_role_codes):
                allowed.append(t)

        return allowed

    # ------------------------------------------------------------------
    # Execute Transition
    # ------------------------------------------------------------------

    @transaction.atomic
    def execute_transition(
        self,
        instance_id: uuid.UUID,
        transition_id: uuid.UUID,
        actor: settings.AUTH_USER_MODEL,  # type: ignore[valid-type]
        comment: str = "",
        metadata: Optional[dict] = None,
    ) -> Instance:
        """
        Execute a transition atomically.

        Steps:
          1. Lock the Instance row (select_for_update)
          2. Load the Transition
          3. Validate instance is running
          4. Validate transition belongs to the same workflow
          5. Validate transition is from current state
          6. Validate actor has required role
          7. Update instance state
          8. Create ActionLog
          9. Mark pending tasks for the old state as completed
          10. Create tasks for the new state (if not final)
          11. If final state -> mark instance completed/rejected
        """
        # 1. Lock instance
        instance = (
            Instance.objects.select_for_update()
            .filter(pk=instance_id)
            .first()
        )
        if not instance:
            raise WorkflowEngineError(f"Instance {instance_id} not found.")

        # Reload with related objects for display
        if instance:
            instance.current_state  # touch lazy load
            instance.workflow_definition

        # 2. Load transition
        try:
            transition = Transition.objects.select_for_update().get(pk=transition_id)
        except Transition.DoesNotExist:
            raise WorkflowEngineError(f"Transition {transition_id} not found.")

        # 3. Validate instance is running
        if instance.status != Instance.Status.RUNNING:
            raise InstanceNotRunningError(
                f"Instance {instance_id} is '{instance.status}', not running."
            )

        # 4. Validate transition belongs to the same workflow
        if transition.workflow_definition_id != instance.workflow_definition_id:
            raise InvalidTransitionError(
                "Transition does not belong to the instance's workflow."
            )

        # 5. Validate transition is from current state
        if transition.from_state_id != instance.current_state_id:
            raise InvalidTransitionError(
                f"Transition '{transition.name}' is not from current state "
                f"'{instance.current_state.code if instance.current_state else '?'}'."
            )

        # 6. Validate actor has required role
        if transition.allowed_role_codes:
            actor_roles = actor.role_codes()
            if not any(role in actor_roles for role in transition.allowed_role_codes):
                raise InvalidTransitionError(
                    f"Actor '{actor}' does not have required role(s): "
                    f"{transition.allowed_role_codes}."
                )

        # 7. Update instance state
        old_state = instance.current_state
        new_state = transition.to_state
        instance.current_state = new_state

        # 8. Determine next status
        if new_state.is_final:
            if transition.name.lower() in ("reject", "rejected", "cancel", "cancelled"):
                instance.status = Instance.Status.REJECTED
            else:
                instance.status = Instance.Status.COMPLETED

        instance.save(update_fields=["current_state", "status", "updated_at"])

        # 9. Create ActionLog
        ActionLog.objects.create(
            instance=instance,
            from_state=old_state,
            to_state=new_state,
            action=transition.name,
            actor=actor,
            comment=comment,
            metadata=metadata or {},
        )

        # 10. Mark pending tasks for old state as completed
        from apps.tasks.models import WorkflowTask

        WorkflowTask.objects.filter(
            instance=instance,
            state=old_state,
            status=WorkflowTask.Status.PENDING,
        ).update(
            status=WorkflowTask.Status.COMPLETED,
            completed_at=timezone.now(),
            updated_at=timezone.now(),
        )

        # 11. Create tasks for new state (if not final)
        if not new_state.is_final:
            self._create_tasks_for_state(instance, new_state, assigned_by=actor)

        logger.info(
            "Instance %s: transition '%s' by %s -> %s",
            instance_id,
            transition.name,
            actor,
            instance.status,
        )
        return instance

    # ------------------------------------------------------------------
    # Cancel Instance
    # ------------------------------------------------------------------

    @transaction.atomic
    def cancel_instance(
        self,
        instance_id: uuid.UUID,
        actor: settings.AUTH_USER_MODEL,  # type: ignore[valid-type]
        reason: str = "",
    ) -> Instance:
        """Cancel a running instance (only the requester or workflow_admin)."""
        instance = (
            Instance.objects.select_for_update()
            .filter(pk=instance_id)
            .first()
        )
        if not instance:
            raise WorkflowEngineError(f"Instance {instance_id} not found.")
        instance.current_state  # touch lazy load
        if instance.status != Instance.Status.RUNNING:
            raise InstanceNotRunningError(
                f"Instance {instance_id} is '{instance.status}', cannot cancel."
            )

        actor_roles = actor.role_codes()
        is_requester = instance.requester_id == actor.pk
        is_admin = "workflow_admin" in actor_roles

        if not (is_requester or is_admin):
            raise InvalidTransitionError(
                "Only the requester or workflow_admin can cancel an instance."
            )

        instance.status = Instance.Status.CANCELLED
        instance.save(update_fields=["status", "updated_at"])

        ActionLog.objects.create(
            instance=instance,
            from_state=instance.current_state,
            to_state=None,
            action="cancel",
            actor=actor,
            comment=reason or "Cancelled",
        )

        from apps.tasks.models import WorkflowTask

        WorkflowTask.objects.filter(
            instance=instance,
            status=WorkflowTask.Status.PENDING,
        ).update(
            status=WorkflowTask.Status.SKIPPED,
            updated_at=timezone.now(),
        )

        return instance

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _create_tasks_for_state(
        self,
        instance: Instance,
        state: State,
        assigned_by: Optional[settings.AUTH_USER_MODEL] = None,  # type: ignore[valid-type]
    ) -> None:
        """
        Create WorkflowTask for each user who has the role(s) required
        to perform outgoing transitions from this state.
        """
        from apps.accounts.models import UserRole
        from apps.tasks.models import WorkflowTask

        # Find all outgoing transitions from this state
        outgoing = Transition.objects.filter(
            workflow_definition=instance.workflow_definition,
            from_state=state,
        )

        # Collect all unique role codes allowed
        role_codes: set[str] = set()
        for t in outgoing:
            if t.allowed_role_codes:
                role_codes.update(t.allowed_role_codes)

        if not role_codes:
            logger.warning(
                "No role codes defined for transitions from state %s; "
                "no tasks created.",
                state.code,
            )
            return

        # Find users with valid assignments for any of these roles
        now = timezone.now()
        user_ids = list(
            UserRole.objects.filter(
                role__code__in=role_codes,
                is_active=True,
                role__is_active=True,
                role__is_deleted=False,
                user__is_active=True,
                user__is_deleted=False,
            )
            .filter(
                models.Q(valid_from__isnull=True) | models.Q(valid_from__lte=now)
            )
            .filter(models.Q(valid_to__isnull=True) | models.Q(valid_to__gte=now))
            .values_list("user_id", flat=True)
            .distinct()
        )

        tasks: list[WorkflowTask] = []
        for uid in user_ids:
            tasks.append(
                WorkflowTask(
                    instance=instance,
                    state=state,
                    assignee_id=uid,
                    assigned_by=assigned_by,
                    status=WorkflowTask.Status.PENDING,
                )
            )

        if tasks:
            WorkflowTask.objects.bulk_create(tasks)
            logger.info(
                "Created %d task(s) for instance %s at state %s",
                len(tasks),
                instance.id,
                state.code,
            )
        else:
            logger.warning(
                "No eligible users found for roles %s at state %s",
                role_codes,
                state.code,
            )
