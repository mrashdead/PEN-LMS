from __future__ import annotations

from django.test import TestCase

from apps.education.models import Course, CourseOffering, EnrollmentRefund
from apps.education.services import (
    convert_offering_enrollment_to_class,
    create_offering_enrollment,
    process_enrollment_refund,
    request_enrollment_refund,
)
from apps.forms.models import FormSchema, FormSubmission, Request, RequestType
from apps.forms.services import RequestService
from apps.forms.tests.factories import UserFactory, make_class_group, make_person, make_term
from apps.tasks.models import WorkflowTask
from apps.workflow.models import State, Transition, WorkflowDefinition
from apps.workflow.services import WorkflowEngineService


class UnifiedRequestDomainActionTests(TestCase):
    def setUp(self):
        self.employee = UserFactory(username="pipeline-employee", roles=["employee"])
        self.manager = UserFactory(username="pipeline-manager", roles=["manager"])
        self.student = make_person(
            user=UserFactory(username="pipeline-student", roles=["student"]),
            person_type="student",
        )
        self.course = Course.objects.create(code="pipeline-course", title="دوره تست")
        self.offering = CourseOffering.objects.create(
            course=self.course,
            code="pipeline-offering",
            title="برگزاری تست",
            capacity=2,
            status=CourseOffering.Status.OPEN,
        )

        self.workflow = WorkflowDefinition.objects.create(
            code="pipeline-registration",
            name="ثبت‌نام تست",
            is_active=True,
        )
        self.new = State.objects.create(
            workflow_definition=self.workflow,
            code="new",
            name="جدید",
            is_initial=True,
        )
        self.done = State.objects.create(
            workflow_definition=self.workflow,
            code="done",
            name="تکمیل",
            is_final=True,
        )
        self.approve = Transition.objects.create(
            workflow_definition=self.workflow,
            from_state=self.new,
            to_state=self.done,
            name="approve",
            kind="approve",
            allowed_role_codes=["manager"],
        )
        self.request_type = RequestType.objects.create(
            code="pipeline-registration",
            title="ثبت‌نام تست",
            workflow_definition=self.workflow,
            metadata={"domain_action": "student_registration"},
        )
        self.schema = FormSchema.objects.create(
            slug="pipeline-registration",
            title="ثبت‌نام تست",
            fields=[],
            metadata={"domain_action": "student_registration"},
            request_type=self.request_type,
            workflow_definition=self.workflow,
        )

    def test_approval_runs_idempotent_student_registration_action(self):
        submission = FormSubmission.objects.create(
            form_schema=self.schema,
            submitted_by=self.employee,
            data={"offering": str(self.offering.pk), "student": str(self.student.pk)},
            status=FormSubmission.Status.PROCESSING,
        )
        instance = WorkflowEngineService().create_instance(
            workflow_code=self.workflow.code,
            requester=self.employee,
            title="ثبت‌نام تست",
            subject_person=self.student,
        )
        submission.workflow_instance = instance
        submission.save(update_fields=["workflow_instance", "updated_at"])
        business_request = Request.objects.create(
            request_type=self.request_type,
            form_submission=submission,
            requester=self.employee,
            subject_person=self.student,
            status=Request.Status.IN_REVIEW,
        )

        result = RequestService().transition(
            business_request,
            actor=self.manager,
            transition_id=self.approve.pk,
            idempotency_key="pipeline-approve-1",
        )
        self.assertEqual(result.status, Request.Status.COMPLETED)
        self.assertEqual(self.offering.enrollments.count(), 1)

    def test_direct_form_creates_request_and_runs_domain_action_immediately(self):
        direct_type = RequestType.objects.create(
            code="direct-pipeline-registration",
            title="ثبت‌نام مستقیم",
            metadata={"domain_action": "student_registration"},
        )
        direct_schema = FormSchema.objects.create(
            slug="direct-pipeline-registration",
            title="ثبت‌نام مستقیم",
            request_type=direct_type,
            metadata={"domain_action": "student_registration"},
            workflow_config={
                "execution_mode": "direct", "allow_on_behalf": False,
                "eligible_initiator_roles": [], "routing_rules": [],
            },
            fields=[
                {"key": "offering", "type": "relation", "order": 1, "required": True,
                 "relation": {"registry_key": "academic.course_offering", "lookup": "id"}},
                {"key": "student", "type": "relation", "order": 2, "required": True,
                 "relation": {"registry_key": "persons.person", "lookup": "id",
                              "filter": {"person_type": "student", "is_active": True}}},
            ],
        )
        business_request = RequestService().create_draft(
            schema=direct_schema,
            requester=self.employee,
            data={"offering": str(self.offering.pk), "student": str(self.student.pk)},
        )
        result = RequestService().submit(business_request, actor=self.employee)
        self.assertEqual(result.status, Request.Status.COMPLETED)
        self.assertIsNone(result.workflow_instance)
        self.assertEqual(self.offering.enrollments.count(), 1)
        enrollment = self.offering.enrollments.get()
        self.assertEqual(enrollment.student_id, self.student.pk)

        # A direct request has no approval transition after its immediate action.
        self.assertEqual(self.offering.enrollments.count(), 1)


class AssignmentPolicyTests(TestCase):
    def test_direct_manager_policy_creates_one_actionable_task(self):
        requester = UserFactory(username="assignment-requester", roles=["employee"])
        manager = UserFactory(username="assignment-manager", roles=["manager"])
        requester.manager = manager
        requester.save(update_fields=["manager", "updated_at"])
        definition = WorkflowDefinition.objects.create(
            code="assignment-policy-test",
            name="سیاست تخصیص تست",
        )
        state = State.objects.create(
            workflow_definition=definition,
            code="review",
            name="بازبینی",
            is_initial=True,
            assignment_policy={"strategy": "direct_manager", "fallback_roles": ["manager"]},
        )
        final = State.objects.create(
            workflow_definition=definition,
            code="done",
            name="پایان",
            is_final=True,
        )
        Transition.objects.create(
            workflow_definition=definition,
            from_state=state,
            to_state=final,
            name="approve",
            kind="approve",
            allowed_role_codes=["manager"],
        )
        instance = WorkflowEngineService().create_instance(
            workflow_code=definition.code,
            requester=requester,
            title="تست تخصیص",
        )
        tasks = WorkflowTask.objects.filter(instance=instance, status=WorkflowTask.Status.PENDING)
        self.assertEqual(tasks.count(), 1)
        self.assertEqual(tasks.first().assignee_id, manager.pk)


class EnrollmentLedgerTests(TestCase):
    def setUp(self):
        self.manager = UserFactory(username="ledger-manager", roles=["manager"])
        self.student = make_person(person_type="student")
        self.course = Course.objects.create(code="ledger-course", title="دوره مالی")
        self.offering = CourseOffering.objects.create(
            course=self.course,
            code="ledger-offering",
            title="برگزاری مالی",
            capacity=2,
            tuition=100000,
            status=CourseOffering.Status.OPEN,
        )

    def test_conversion_and_refund_are_auditable_and_idempotent(self):
        enrollment = create_offering_enrollment(
            offering=self.offering,
            student=self.student,
            actor=self.manager,
            course_amount=100000,
        )
        self.offering.refresh_from_db()
        self.assertEqual(self.offering.enrolled_count, 1)
        class_group = make_class_group(term=make_term(), capacity=2)
        membership = convert_offering_enrollment_to_class(
            enrollment=enrollment,
            class_group=class_group,
            actor=self.manager,
        )
        self.assertEqual(membership.student_id, self.student.pk)
        self.assertEqual(
            convert_offering_enrollment_to_class(
                enrollment=enrollment,
                class_group=class_group,
                actor=self.manager,
            ).pk,
            membership.pk,
        )

        refund = request_enrollment_refund(
            enrollment=enrollment,
            amount=100000,
            requested_by=self.manager,
            reason="انصراف",
        )
        processed = process_enrollment_refund(
            refund=refund,
            processor=self.manager,
            reference="REF-1",
        )
        self.assertEqual(processed.status, EnrollmentRefund.Status.PROCESSED)
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.lifecycle_status, enrollment.LifecycleStatus.REFUNDED)
        self.assertFalse(enrollment.is_active)
