from django.test import TestCase
from django.db.models.deletion import ProtectedError
from django.db import IntegrityError, transaction

from apps.accounts.models import User
from apps.workflow.models import (
    ActionLog,
    ApprovalRecord,
    EntityWorkflow,
    Instance,
    State,
    Transition,
    WorkflowDefinition,
)


class WorkflowConstraintTests(TestCase):
    def setUp(self):
        self.actor = User.objects.create_user(username="workflow-model-actor", password="x")
        self.definition = WorkflowDefinition.objects.create(
            code="workflow-model", name="Workflow", version=1,
        )
        self.start = State.objects.create(
            workflow_definition=self.definition, code="start", name="Start",
            is_initial=True,
        )
        self.review = State.objects.create(
            workflow_definition=self.definition, code="review", name="Review",
        )
        self.done = State.objects.create(
            workflow_definition=self.definition, code="done", name="Done",
        )
        self.instance = Instance.objects.create(
            workflow_definition=self.definition, current_state=self.start,
            requester=self.actor, title="History",
        )

    def test_workflow_code_version_and_active_version_constraints(self):
        WorkflowDefinition.objects.create(
            code=self.definition.code, name="Archived", version=2, is_active=False,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                WorkflowDefinition.objects.create(
                    code=self.definition.code, name="Duplicate version", version=1,
                    is_active=False,
                )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                WorkflowDefinition.objects.create(
                    code=self.definition.code, name="Two active", version=3,
                    is_active=True,
                )

    def test_only_one_initial_state_per_definition(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                State.objects.create(
                    workflow_definition=self.definition, code="other-start",
                    name="Other start", is_initial=True,
                )

    def test_transition_name_and_kind_are_unique_from_state(self):
        Transition.objects.create(
            workflow_definition=self.definition, from_state=self.start,
            to_state=self.review, name="submit", kind="submit",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Transition.objects.create(
                    workflow_definition=self.definition, from_state=self.start,
                    to_state=self.done, name="submit", kind="different",
                )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Transition.objects.create(
                    workflow_definition=self.definition, from_state=self.start,
                    to_state=self.done, name="another-name", kind="submit",
                )

    def test_entity_workflow_can_retain_soft_deleted_history(self):
        from django.contrib.contenttypes.models import ContentType

        content_type = ContentType.objects.get_for_model(self.instance)
        old = EntityWorkflow.objects.create(
            instance=self.instance, content_type=content_type,
            object_id=self.instance.pk,
        )
        old.soft_delete()
        EntityWorkflow.objects.create(
            instance=self.instance, content_type=content_type,
            object_id=self.instance.pk,
        )
        self.assertEqual(
            EntityWorkflow.all_objects.filter(
                content_type=content_type, object_id=self.instance.pk,
            ).count(),
            2,
        )


class ProtectedWorkflowHistoryTests(TestCase):
    def setUp(self):
        self.actor = User.objects.create_user(username="workflow-history-actor", password="x")
        self.definition = WorkflowDefinition.objects.create(
            code="protected-history", name="Protected",
        )
        self.state = State.objects.create(
            workflow_definition=self.definition, code="start", name="Start",
            is_initial=True,
        )
        self.instance = Instance.objects.create(
            workflow_definition=self.definition, current_state=self.state,
            requester=self.actor, title="Protected history",
        )
        self.action = ActionLog.objects.create(
            instance=self.instance, actor=self.actor, action="create",
        )
        self.approval = ApprovalRecord.objects.create(
            instance=self.instance, approver=self.actor, action="approve",
        )

    def test_action_log_and_approval_reject_instance_soft_delete(self):
        with self.assertRaises(ProtectedError):
            self.action.delete()
        with self.assertRaises(ProtectedError):
            self.action.soft_delete()
        with self.assertRaises(ProtectedError):
            self.approval.delete()
        with self.assertRaises(ProtectedError):
            ActionLog.objects.filter(pk=self.action.pk).delete()
        with self.assertRaises(ProtectedError):
            ApprovalRecord.objects.filter(pk=self.approval.pk).delete()

    def test_hard_deleting_instance_is_blocked_by_preserved_history(self):
        with self.assertRaises(ProtectedError):
            self.instance.hard_delete()
