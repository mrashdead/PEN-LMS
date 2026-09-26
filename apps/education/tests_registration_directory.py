from django.test import TestCase
from rest_framework.test import APIClient

from apps.academics.models import AcademicTerm, ClassEnrollment, ClassGroup
from apps.education.models import Course, CourseOffering
from apps.education.services import (
    convert_offering_enrollment_to_class,
    create_offering_enrollment,
)
from apps.forms.tests.factories import UserFactory, make_person


class RegistrationDirectoryAPITests(TestCase):
    def setUp(self):
        self.manager = UserFactory(username="registration-directory-manager", roles=["manager"])
        self.student = make_person(first_name="آرمان", last_name="آموزگار")
        self.course = Course.objects.create(title="ریاضی", code="registration-math")
        self.offering = CourseOffering.objects.create(
            course=self.course,
            title="ریاضی پاییز",
            status=CourseOffering.Status.OPEN,
            capacity=20,
        )
        self.term = AcademicTerm.objects.create(
            title="پاییز آزمایشی",
            start_date="2026-09-01",
            end_date="2026-12-31",
        )
        self.class_group = ClassGroup.objects.create(
            term=self.term,
            offering=self.offering,
            code="math-a",
            name="ریاضی گروه الف",
            capacity=12,
        )
        self.enrollment = create_offering_enrollment(
            offering=self.offering,
            student=self.student,
            actor=self.manager,
        )
        self.membership = convert_offering_enrollment_to_class(
            enrollment=self.enrollment,
            class_group=self.class_group,
            actor=self.manager,
        )
        self.client = APIClient()
        self.client.force_login(self.manager)

    def test_linked_financial_and_class_rows_are_one_registration(self):
        response = self.client.get(
            "/api/education/registration-directory/",
            {"student": str(self.student.pk)},
        )

        self.assertEqual(response.status_code, 200, response.content)
        payload = response.json()
        self.assertEqual(len(payload["results"]), 1)
        self.assertEqual(payload["summary"]["total"], 1)
        self.assertEqual(payload["results"][0]["source"], "offering")
        self.assertEqual(payload["results"][0]["class_group"]["id"], str(self.class_group.pk))

    def test_person_and_class_context_expose_roster_and_capacity(self):
        person = self.client.get(
            f"/api/education/registration-directory/context/people/{self.student.pk}/"
        )
        class_page = self.client.get(
            f"/api/education/registration-directory/context/classes/{self.class_group.pk}/"
        )
        record = self.client.get(
            f"/api/education/registration-directory/records/offering/{self.enrollment.pk}/"
        )
        dashboard_page = self.client.get(
            f"/workspace/enrollments/people/{self.student.pk}/"
        )

        self.assertEqual(person.status_code, 200, person.content)
        self.assertEqual(person.json()["registrations"]["summary"]["total"], 1)
        self.assertEqual(class_page.status_code, 200, class_page.content)
        self.assertEqual(class_page.json()["capacity"]["enrolled"], 1)
        self.assertEqual(class_page.json()["capacity"]["remaining"], 11)
        self.assertEqual(record.status_code, 200, record.content)
        self.assertEqual(record.json()["capacity"]["total"], 12)
        self.assertEqual(dashboard_page.status_code, 200, dashboard_page.content)
        self.assertContains(dashboard_page, "registration-page-context")

    def test_repeated_service_submission_returns_the_existing_registration(self):
        duplicate = create_offering_enrollment(
            offering=self.offering,
            student=self.student,
            actor=self.manager,
        )

        self.assertEqual(duplicate.pk, self.enrollment.pk)
        self.assertEqual(self.offering.enrollments.filter(is_deleted=False).count(), 1)

    def test_cursor_paginates_across_offering_and_class_memberships(self):
        second_student = make_person(first_name="سارا", last_name="دانش‌آموز")
        class_membership = ClassEnrollment.objects.create(
            class_group=self.class_group,
            student=second_student,
        )

        first = self.client.get("/api/education/registration-directory/", {"page_size": 1})
        self.assertEqual(first.status_code, 200, first.content)
        first_payload = first.json()
        self.assertEqual(len(first_payload["results"]), 1)
        self.assertEqual(first_payload["summary"]["total"], 2)
        self.assertTrue(first_payload["next_cursor"])

        second = self.client.get(
            "/api/education/registration-directory/",
            {"page_size": 1, "cursor": first_payload["next_cursor"]},
        )
        second_payload = second.json()
        self.assertEqual(len(second_payload["results"]), 1)
        self.assertNotEqual(first_payload["results"][0]["id"], second_payload["results"][0]["id"])
        self.assertEqual({first_payload["results"][0]["source"], second_payload["results"][0]["source"]}, {"offering", "class"})
        self.assertTrue(second_payload["previous_cursor"])

        previous = self.client.get(
            "/api/education/registration-directory/",
            {"page_size": 1, "cursor": second_payload["previous_cursor"]},
        )
        self.assertEqual(previous.json()["results"][0]["id"], first_payload["results"][0]["id"])

    def test_invalid_registration_status_is_rejected(self):
        response = self.client.get(
            "/api/education/registration-directory/",
            {"status": "not-a-status"},
        )
        self.assertEqual(response.status_code, 400)

    def test_registration_directory_requires_a_read_role(self):
        user = UserFactory(username="registration-directory-outsider")
        self.client.force_login(user)

        response = self.client.get("/api/education/registration-directory/")

        self.assertEqual(response.status_code, 403)