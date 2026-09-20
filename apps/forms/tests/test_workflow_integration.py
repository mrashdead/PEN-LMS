"""Workflow integration: auto-creation, transitions, ActionLog, status sync."""
from __future__ import annotations

from django.test import TestCase

from apps.forms.models import FormSubmission
from apps.forms.services import FormSubmissionService, WorkflowIntegrationError
from apps.forms.tests.factories import UserFactory, make_person, make_schema
from apps.workflow.models import (
    ActionLog,
    Instance,
    NotificationOutbox,
    State,
    Transition,
    WorkflowDefinition,
)


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


class SubjectPersonRoutingTests(TestCase):
    """
    Tests for subject_person unification: forms → workflow → notifications.

    When a form is submitted with a subject_person, that Person is set on
    the Instance and notified on transitions. This is the core of the
    forms-workflow unification (§forms-workflow unification).
    """

    def setUp(self):
        self.service = FormSubmissionService()
        self.employee = UserFactory(username="sp-employee", roles=["employee"])
        self.manager = UserFactory(username="sp-manager", roles=["manager"])
        self.definition = _approval_workflow()
        # Schema with subject_field pointing to a person relation field.
        self.schema = make_schema(
            slug="sp-form",
            workflow_definition=self.definition,
            fields=[
                {
                    "key": "student_id",
                    "type": "relation",
                    "relation": {"registry_key": "persons.person"},
                    "required": True,
                },
                {"key": "title", "type": "text", "required": True},
            ],
            metadata={"subject_field": "student_id"},
        )
        # Student with linked user (so they can receive notifications).
        self.student_user = UserFactory(username="sp-student")
        self.student = make_person(
            user=self.student_user, person_type="student",
            first_name="Ali", last_name="Student",
        )

    def _draft(self, data=None):
        return self.service.create_submission(
            schema=self.schema,
            user=self.employee,
            data=data or {"student_id": str(self.student.pk), "title": "Test"},
        )

    def test_submit_sets_subject_person_on_instance(self):
        """
        submit_submission extracts subject_person from form data and passes
        it to create_instance, so the Instance carries the target Person.
        """
        submission = self._draft()
        submitted = self.service.submit_submission(
            submission=submission, user=self.employee
        )
        instance = submitted.workflow_instance
        self.assertIsNotNone(instance)
        self.assertEqual(instance.subject_person_id, self.student.pk)
        self.assertEqual(instance.subject_person, self.student)

    def test_subject_person_notified_on_approve_transition(self):
        """
        When the manager approves, the subject_person (student) receives
        an IN_APP notification via NotificationOutbox.
        """
        submission = self._draft()
        submitted = self.service.submit_submission(
            submission=submission, user=self.employee
        )
        instance = submitted.workflow_instance
        transition = Transition.objects.get(
            workflow_definition=instance.workflow_definition, name="approve"
        )
        # _approval_workflow() uses get_or_create; if the definition already
        # existed from a prior test, get_or_create returns the old row without
        # the kind default. Normalise it so the template resolves to "approved".
        if not transition.kind:
            transition.kind = "approve"
            transition.save(update_fields=["kind"])
        from apps.workflow.services import WorkflowEngineService

        WorkflowEngineService().execute_transition(
            instance_id=instance.pk,
            transition_id=transition.pk,
            actor=self.manager,
            comment="تأیید شد",
        )
        # The student (subject_person) should have a notification.
        inbox = NotificationOutbox.objects.filter(
            recipient=self.student_user,
            instance=instance,
            channel=NotificationOutbox.Channel.IN_APP,
        )
        self.assertTrue(inbox.exists(), "subject_person should receive a notification")
        self.assertEqual(inbox.first().template, "approved")

    def test_subject_person_with_no_linked_user_still_creates_instance(self):
        """
        A person without a linked User account is still set on the Instance.
        Notifications are silently skipped for persons without accounts.
        """
        orphan_person = make_person(
            person_type="student", first_name="No", last_name="User",
        )
        submission = self.service.create_submission(
            schema=self.schema,
            user=self.employee,
            data={"student_id": str(orphan_person.pk), "title": "Orphan"},
        )
        submitted = self.service.submit_submission(
            submission=submission, user=self.employee
        )
        instance = submitted.workflow_instance
        self.assertEqual(instance.subject_person_id, orphan_person.pk)
        # No crash — orphan has no user, so no notification is queued.
        self.assertEqual(
            NotificationOutbox.objects.filter(
                instance=instance, recipient=orphan_person.user
            ).count(),
            0,
        )

    def test_form_without_subject_field_leaves_instance_subject_null(self):
        """
        Forms that do not declare subject_field in metadata create an
        Instance with subject_person = NULL (e.g. administrative forms).
        """
        plain_schema = make_schema(
            slug="sp-plain",
            workflow_definition=self.definition,
            fields=[{"key": "title", "type": "text", "required": True}],
        )
        submission = self.service.create_submission(
            schema=plain_schema, user=self.employee, data={"title": "No subject"},
        )
        submitted = self.service.submit_submission(
            submission=submission, user=self.employee
        )
        self.assertIsNone(submitted.workflow_instance.subject_person_id)
