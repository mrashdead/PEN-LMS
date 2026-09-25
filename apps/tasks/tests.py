from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.tasks.models import WorkflowTask

# Create your tests here.


class PendingTaskUniquenessTests(TestCase):
    def test_same_instance_state_assignee_cannot_have_two_pending_tasks(self):
        from apps.forms.tests.factories import UserFactory
        from apps.workflow.models import Instance, State, WorkflowDefinition

        user = UserFactory(username="unique-task-user")
        workflow = WorkflowDefinition.objects.create(code="unique-task-wf", name="Task")
        state = State.objects.create(
            workflow_definition=workflow, code="review", name="Review",
        )
        instance = Instance.objects.create(
            workflow_definition=workflow, current_state=state,
            requester=user, title="Test",
        )
        WorkflowTask.objects.create(instance=instance, state=state, assignee=user)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                WorkflowTask.objects.create(
                    instance=instance, state=state, assignee=user,
                )
