from __future__ import annotations

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.forms.tests.factories import UserFactory, make_person
from apps.leads.models import Lead
from apps.leads.serializers import LeadCreateSerializer
from apps.persons.models import Person, PersonTypeAssignment


class LeadRoleSeparationTests(TestCase):
    def setUp(self):
        self.employee = UserFactory(username="lead-clerk", roles=["employee"])
        self.teacher = UserFactory(username="lead-teacher", roles=["teacher"])
        self.other_teacher = UserFactory(username="lead-other-teacher", roles=["teacher"])
        self.manager = UserFactory(username="lead-manager", roles=["manager"])

        self.teacher_person = make_person(
            user=self.teacher, person_type="teacher", first_name="استاد", last_name="اول"
        )
        self.other_teacher_person = make_person(
            user=self.other_teacher, person_type="teacher", first_name="استاد", last_name="دوم"
        )
        self.employee_person = make_person(
            user=self.employee, person_type="employee", first_name="کارمند", last_name="ثبت‌کننده"
        )
        self.multi_type_teacher = make_person(
            person_type="employee", first_name="همکار", last_name="مدرس"
        )
        PersonTypeAssignment.objects.create(
            person=self.multi_type_teacher,
            type=Person.Type.TEACHER,
            is_active=True,
        )

        self.own_lead = self._lead("لید استاد اول", self.teacher_person)
        self.other_lead = self._lead("لید استاد دوم", self.other_teacher_person)

    def _lead(self, name, assessor):
        return Lead.objects.create(
            student_name=name,
            age=10,
            phone="09123456789",
            neighborhood="قصردشت",
            assessment_date="2026-10-01",
            assessment_time="10:30",
            assessor=assessor,
            status=Lead.Status.SENT,
            created_by=self.employee,
        )

    def test_staff_and_teacher_pages_are_separate(self):
        self.client.force_login(self.employee)
        staff_page = self.client.get("/leads/")
        self.assertEqual(staff_page.status_code, 200)
        self.assertContains(staff_page, "ثبت لید جدید")

        self.client.force_login(self.teacher)
        self.assertEqual(self.client.get("/leads/").status_code, 404)
        teacher_page = self.client.get("/leads/assessments/")
        self.assertEqual(teacher_page.status_code, 200)
        self.assertContains(teacher_page, "جلسه‌ها و ارزیابی‌های من")
        self.assertNotContains(teacher_page, "ثبت لید جدید")
        self.assertContains(teacher_page, "لید استاد اول")
        self.assertNotContains(teacher_page, "لید استاد دوم")

    def test_teacher_api_is_limited_to_own_assignments_and_assessment_fields(self):
        self.client.force_login(self.teacher)
        response = self.client.get("/api/leads/teacher/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        rows = payload.get("results", payload) if isinstance(payload, dict) else payload
        self.assertEqual([row["id"] for row in rows], [str(self.own_lead.pk)])
        self.assertNotIn("created_by_name", rows[0])

        self.assertEqual(self.client.get(f"/api/leads/teacher/{self.other_lead.pk}/").status_code, 404)
        assessed = self.client.post(
            f"/api/leads/teacher/{self.own_lead.pk}/assess/",
            {"score": 82, "result": "سطح متوسط"},
            content_type="application/json",
        )
        self.assertEqual(assessed.status_code, 200)
        self.own_lead.refresh_from_db()
        self.assertEqual(self.own_lead.status, Lead.Status.ASSESSED)
        self.assertEqual(self.own_lead.assessment_score, 82)
        self.assertEqual(self.client.post(
            f"/api/leads/teacher/{self.other_lead.pk}/assess/",
            {"result": "نباید ثبت شود"},
            content_type="application/json",
        ).status_code, 404)

    def test_assessor_picker_only_returns_people_with_teacher_type(self):
        self.client.force_login(self.employee)
        response = self.client.get("/api/leads/assessors/")
        self.assertEqual(response.status_code, 200)
        rows = response.json()["results"]
        ids = {row["id"] for row in rows}
        self.assertEqual(ids, {str(self.teacher_person.pk), str(self.other_teacher_person.pk), str(self.multi_type_teacher.pk)})
        self.assertNotIn(str(self.employee_person.pk), ids)

        serializer = LeadCreateSerializer(data={
            "student_name": "دانش‌آموز آزمایشی",
            "age": 10,
            "phone": "09123456789",
            "neighborhood": "قصردشت",
            "assessment_date": (timezone.localdate() + timedelta(days=1)).isoformat(),
            "assessment_time": "10:30",
            "assessor": str(self.employee_person.pk),
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn("assessor", serializer.errors)

    def test_supervisor_page_reports_the_logged_in_lead_creator(self):
        self.client.force_login(self.manager)
        response = self.client.get("/leads/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "گزارش ثبت لید به تفکیک کارمند")
        self.assertContains(response, "کارمند ثبت‌کننده")
        self.assertContains(response, "ثبت‌کننده:")

    def test_qualified_lead_creates_and_links_a_student_person(self):
        self.client.force_login(self.employee)
        lead = self.own_lead
        lead.status = Lead.Status.RECOMMENDED
        lead.save(update_fields=["status", "updated_at"])
        response = self.client.post(
            f"/api/leads/{lead.pk}/create-person/",
            {"national_code": "0012345678", "student_code": "ST-1001", "father_name": "پدر آزمون"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        lead.refresh_from_db()
        self.assertIsNotNone(lead.enrolled_person_id)
        self.assertEqual(lead.enrolled_person.person_type, Person.Type.STUDENT)
        self.assertEqual(lead.enrolled_person.mobile, lead.phone)
        self.assertEqual(lead.enrolled_person.student_code, "ST-1001")
