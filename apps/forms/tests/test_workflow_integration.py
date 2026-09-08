"""Workflow integration: auto-creation, transitions, ActionLog, status sync."""
from __future__ import annotations

from django.test import TestCase

from apps.forms.models import FormSubmission
from apps.forms.services import FormSubmissionService, WorkflowIntegrationError
from apps.forms.tests.factories import UserFactory, make_schema
from apps.workflow.models import ActionLog, Instance, State, Transition, WorkflowDefinition


def _approval_workflow(code="form-approval"):
    definition, _ = WorkflowDefinition.objects.get_or_create(
        code=code, defaults={"name": "فرم تأیید", "is_active": True, "version": 1}
    )
    initial, _ = State.objects.get_or_create(
        workflow_definition=definition, code="new",
        defaults={"name": "جدید", "is_initial": True, "is_final": False},
    )
    final, _ = State.objects.get_or_create(
        workflow_definition=definition, code="done",
        defaults={"name": "پایان", "is_initial": False, "is_final": True},
    )
    Transition.objects.get_or_create(
        workflow_definition=definition,
        from_state=initial, to_state=final, name="approve",
        defaults={"allowed_role_codes": ["manager"], "guard_expression": {}},
    )
    return definition


class WorkflowAutoCreationTests(TestCase):
    def setUp(self):
        self.service = FormSubmissionService()
        self.employee = UserFactory(username="wf-employee", roles=["employee"])
        self.manager = UserFactory(username="wf-manager", roles=["manager"])
        self.definition = _approval_workflow()
        self.schema = make_schema(
            slug="wf-form", workflow_definition=self.definition,
            fields=[{"key": "title", "type": "text", "order": 1, "required": True}],
        )

    def _draft(self):
        return self.service.create_submission(
            schema=self.schema, user=self.employee, data={"title": "سلام"},
        )

    def test_submit_without_workflow_stays_submitted(self):
        schema = make_schema(slug="plain-form")  # no workflow
        submission = self.service.create_submission(
            schema=schema, user=self.employee, data={"title": "بدون فرآیند"},
        )
        submitted = self.service.submit_submission(submission=submission, user=self.employee)
        self.assertEqual(submitted.status, FormSubmission.Status.SUBMITTED)
        self.assertIsNone(submitted.workflow_instance)

    def test_submit_starts_workflow_and_links_entity(self):
        submission = self._draft()
        submitted = self.service.submit_submission(submission=submission, user=self.employee)
        self.assertIsNotNone(submitted.workflow_instance)
        self.assertEqual(submitted.workflow_instance.status, Instance.Status.RUNNING)
        # EntityWorkflow link exists (GenericForeignKey to the submission).
        link = submitted.workflow_instance.entity_links.first()
        self.assertIsNotNone(link)
        self.assertEqual(str(link.object_id), str(submitted.pk))
        # Engine logged creation.
        self.assertTrue(
            ActionLog.objects.filter(
                instance=submitted.workflow_instance, action="create", actor=self.employee
            ).exists()
        )
        # Forms service appended its own audit entry too.
        self.assertTrue(
            ActionLog.objects.filter(
                instance=submitted.workflow_instance, action="form_submit", actor=self.employee
            ).exists()
        )

    def test_transition_through_engine_syncs_status(self):
        submission = self._draft()
        submission = self.service.submit_submission(submission=submission, user=self.employee)
        instance = submission.workflow_instance
        transition = Transition.objects.get(
            workflow_definition=instance.workflow_definition, name="approve"
        )
        from apps.workflow.services import WorkflowEngineService

        WorkflowEngineService().execute_transition(
            instance_id=instance.pk, transition_id=transition.pk,
            actor=self.manager, comment="تایید",
        )
        synced = self.service.sync_status_from_workflow(
            FormSubmission.objects.get(pk=submission.pk), actor=self.manager
        )
        instance.refresh_from_db()
        self.assertEqual(instance.status, Instance.Status.COMPLETED)
        self.assertEqual(synced.status, FormSubmission.Status.APPROVED)
        self.assertEqual(synced.reviewed_by_id, self.manager.pk)

    def test_non_authorized_transition_is_rejected_by_engine(self):
        submission = self._draft()
        submission = self.service.submit_submission(submission=submission, user=self.employee)
        instance = submission.workflow_instance
        transition = Transition.objects.get(
            workflow_definition=instance.workflow_definition, name="approve"
        )
        from apps.workflow.services import InvalidTransitionError, WorkflowEngineService

        with self.assertRaises(InvalidTransitionError):
            WorkflowEngineService().execute_transition(
                instance_id=instance.pk, transition_id=transition.pk,
                actor=self.employee,  # lacks the manager role
            )
        submission.refresh_from_db()
        self.assertEqual(submission.status, FormSubmission.Status.SUBMITTED)

    def test_schema_without_active_workflow_definition_fails_at_submit(self):
        inactive = WorkflowDefinition.objects.create(
            code="dead-wf", name="غیرفعال", is_active=False
        )
        schema = make_schema(slug="wf-dead", workflow_definition=inactive)
        # Valid data so submit reaches the workflow-start step (not validation).
        submission = self.service.create_submission(
            schema=schema, user=self.employee, data={"title": "فرم معیوب"},
        )
        with self.assertRaises(WorkflowIntegrationError):
            self.service.submit_submission(submission=submission, user=self.employee)

    def test_workflow_state_never_written_directly_by_forms(self):
        submission = self._draft()
        submitted = self.service.submit_submission(submission=submission, user=self.employee)
        # The forms service only maps status FROM the engine; it never mutates
        # Instance.status itself.
        instance = submitted.workflow_instance
        before = instance.status
        self.service.sync_status_from_workflow(submitted)
        instance.refresh_from_db()
        self.assertEqual(instance.status, before)
