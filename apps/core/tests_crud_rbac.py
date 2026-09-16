from __future__ import annotations

from django.test import TestCase
from rest_framework.test import APIClient

from apps.core.crud import crud_actions
from apps.core.models import AuditEvent
from apps.education.models import Course, CourseLesson, Department, Lesson
from apps.education.serializers import CourseSerializer
from apps.forms.tests.factories import UserFactory, make_person


class CRUDRBACContractTests(TestCase):
    def setUp(self):
        self.manager = UserFactory(username="crud-manager", roles=["manager"])
        self.teacher = UserFactory(username="crud-teacher", roles=["teacher"])
        self.department = Department.objects.create(code="crud", name="CRUD")
        self.client = APIClient()

    def test_row_capabilities_are_server_authoritative(self):
        self.assertTrue(crud_actions(self.manager, self.department)["edit"])
        self.assertTrue(crud_actions(self.manager, self.department)["delete"])
        self.assertFalse(crud_actions(self.teacher, self.department)["edit"])
        self.assertFalse(crud_actions(self.teacher, self.department)["delete"])

    def test_delete_is_post_only_soft_delete_and_audited(self):
        self.client.force_authenticate(self.manager)
        response = self.client.post(f"/api/education/departments/{self.department.pk}/delete/", {})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Department.objects.filter(pk=self.department.pk).exists())
        deleted = Department.all_objects.get(pk=self.department.pk)
        self.assertTrue(deleted.is_deleted)
        self.assertTrue(AuditEvent.objects.filter(object_id=str(deleted.pk)).exists())

    def test_teacher_cannot_delete_an_unrelated_row(self):
        self.client.force_authenticate(self.teacher)
        response = self.client.post(f"/api/education/departments/{self.department.pk}/delete/", {})
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Department.objects.filter(pk=self.department.pk).exists())

    def test_national_code_is_immutable_on_update(self):
        person = make_person(person_type="student", national_code="1234567890")
        from apps.core.tests_pyramid import grant_model_perms
        from apps.persons.models import Person

        grant_model_perms(self.manager, Person)
        self.client.force_authenticate(self.manager)
        response = self.client.patch(
            f"/api/persons/{person.pk}/",
            {"national_code": "0987654321", "first_name": "تغییر"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        person.refresh_from_db()
        self.assertEqual(person.national_code, "1234567890")
        self.assertEqual(person.first_name, "تغییر")

    def test_course_edit_payload_contains_lesson_ids_for_prefill(self):
        lesson = Lesson.objects.create(title="درس CRUD")
        course = Course.objects.create(title="دوره CRUD")
        CourseLesson.objects.create(course=course, lesson=lesson, order=1)
        output = CourseSerializer(course).data
        self.assertEqual(output["lessons"], [str(lesson.pk)])

    def test_form_submission_delete_uses_the_same_post_contract(self):
        from apps.forms.models import FormSchema, FormSubmission

        schema = FormSchema.objects.create(slug="crud-submit", title="فرم CRUD", version=1, fields=[])
        submission = FormSubmission.objects.create(
            form_schema=schema, submitted_by=self.manager, data={}, status=FormSubmission.Status.DRAFT
        )
        self.client.force_authenticate(self.manager)
        response = self.client.post(f"/api/forms/submissions/{submission.pk}/delete/", {})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(FormSubmission.all_objects.get(pk=submission.pk).is_deleted)

    def test_workflow_request_delete_is_scoped_and_soft(self):
        from apps.workflow.models import Instance, State, WorkflowDefinition

        workflow = WorkflowDefinition.objects.create(code="crud-wf", name="CRUD")
        state = State.objects.create(workflow_definition=workflow, code="new", name="جدید", is_initial=True)
        instance = Instance.objects.create(
            workflow_definition=workflow, current_state=state, requester=self.manager,
            title="درخواست CRUD",
        )
        self.client.force_authenticate(self.manager)
        response = self.client.post(f"/api/workflow/instances/{instance.pk}/delete/", {})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Instance.all_objects.get(pk=instance.pk).is_deleted)
