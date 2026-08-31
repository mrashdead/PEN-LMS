from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from django.conf import settings

if TYPE_CHECKING:
    from apps.workflow.models import Instance, Transition


@dataclass
class TransitionValidationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)


class TransitionValidator:
    """
    Pure validation — no side-effects, no DB writes.
    Makes execute_transition() testable without mocking DB.
    """

    def validate(
        self,
        instance: Instance,
        transition: Transition,
        actor: settings.AUTH_USER_MODEL,  # type: ignore[valid-type]
    ) -> TransitionValidationResult:
        errors: list[str] = []

        # --- 1. Instance is running ---
        if instance.status != instance.Status.RUNNING:
            errors.append(
                f"Instance is '{instance.status}', not 'running'."
            )

        # --- 2. Transition belongs to the same workflow ---
        if transition.workflow_definition_id != instance.workflow_definition_id:
            errors.append(
                "Transition does not belong to the instance's workflow."
            )

        # --- 3. Transition is from current state ---
        if transition.from_state_id != instance.current_state_id:
            current_code = (
                instance.current_state.code if instance.current_state else "?"
            )
            errors.append(
                f"Transition '{transition.name}' is not from "
                f"current state '{current_code}'."
            )

        # --- 4. Actor has at least one required role ---
        if transition.allowed_role_codes:
            actor_roles = actor.role_codes()
            if not any(role in actor_roles for role in transition.allowed_role_codes):
                errors.append(
                    f"Actor does not have required role(s): "
                    f"{transition.allowed_role_codes}."
                )

        # --- 5. Guard condition (if any) ---
        if transition.guard_expression and transition.guard_expression != {}:
            from apps.workflow.guards import GuardEvaluator

            guard_ok, guard_msg = GuardEvaluator().evaluate(
                guard=transition.guard_expression,
                instance=instance,
                actor=actor,
            )
            if not guard_ok:
                errors.append(guard_msg or "Guard condition denied this transition.")

        return TransitionValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
        )