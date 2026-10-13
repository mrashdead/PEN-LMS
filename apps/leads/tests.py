from __future__ import annotations

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.education.models import Course, CourseLesson, CourseOffering, Lesson, OfferingEnrollment
from apps.forms.tests.factories import UserFactory, make_person
from apps.leads.models import Lead
from apps.leads.permissions import is_lead_operator
from apps.leads.serializers import LeadCreateSerializer
from apps.org.models import PersonACLEntry
from apps.persons.models import Person, PersonTypeAssignment


class LeadRoleSeparationTests(TestCase):
    def setUp(self):
        self.employee = UserFactory(username="lead-clerk", roles=["employee"])
        PersonACLEntry.objects.create(user=self.employee, resource_type="page", resource_key="leads-dashboard", verbs=["view"])
        self.teacher = UserFactory(username="lead-teacher", roles=["teacher"])
        self.other_teacher = UserFactory(username="lead-other-teacher", roles=["teacher"])
        self.manager = UserFactory(username="lead-manager", roles=["manager"])

        self.teacher_person = make_person(
            user=self.teacher, person_type="teacher", first_name="استاد", last_name="اول", can_assess_leads=True
        )
        self.other_teacher_person = make_person(
            user=self.other_teacher, person_type="teacher", first_name="استاد", last_name="دوم", can_assess_leads=True
        )
        self.employee_person = make_person(
            user=self.employee, person_type="employee", first_name="کارمند", last_name="ثبت‌کننده"
        )
        self.multi_type_teacher = make_person(
            person_type="employee", first_name="همکار", last_name="مدرس", can_assess_leads=True
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
        self.assertContains(teacher_page, "تعیین سطح‌های ارجاع‌شده به من")
        self.assertNotContains(teacher_page, "ثبت لید جدید")
        self.assertContains(teacher_page, "لید استاد اول")
        self.assertNotContains(teacher_page, "لید استاد دوم")

    def test_teacher_api_is_limited_to_own_assignments_and_assessment_fields(self):
        self.client.force_login(self.teacher)
        response = self.client.get("/api/leads/assessments/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        rows = payload.get("results", payload) if isinstance(payload, dict) else payload
        self.assertEqual([row["id"] for row in rows], [str(self.own_lead.pk)])
        self.assertNotIn("created_by_name", rows[0])

        self.assertEqual(self.client.get(f"/api/leads/assessments/{self.other_lead.pk}/").status_code, 404)
        assessed = self.client.post(
            f"/api/leads/assessments/{self.own_lead.pk}/assess/",
            {"result": "سطح متوسط"},
            content_type="application/json",
        )
        self.assertEqual(assessed.status_code, 200)
        self.own_lead.refresh_from_db()
        self.assertEqual(self.own_lead.status, Lead.Status.ASSESSED)
        self.assertEqual(self.own_lead.assessment_result, "سطح متوسط")
        self.assertEqual(self.client.post(
            f"/api/leads/assessments/{self.other_lead.pk}/assess/",
            {"result": "نباید ثبت شود"},
            content_type="application/json",
        ).status_code, 404)

    def test_assessor_picker_requires_explicit_capability(self):
        unqualified_teacher = make_person(person_type="teacher")
        self.client.force_login(self.employee)
        response = self.client.get("/api/leads/assessors/")
        self.assertEqual(response.status_code, 200)
        rows = response.json()["results"]
        ids = {row["id"] for row in rows}
        self.assertEqual(ids, {str(self.teacher_person.pk), str(self.other_teacher_person.pk), str(self.multi_type_teacher.pk)})
        self.assertNotIn(str(self.employee_person.pk), ids)
        self.assertNotIn(str(unqualified_teacher.pk), ids)

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

    def test_manager_page_shows_creator_column(self):
        self.client.force_login(self.manager)
        response = self.client.get("/leads/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ثبت‌کننده")

    def test_qualified_lead_creates_and_links_a_student_person(self):
        self.client.force_login(self.employee)
        lead = self.own_lead
        lead.status = Lead.Status.RECOMMENDED
        lead.save(update_fields=["status", "updated_at"])
        response = self.client.post(
            f"/api/leads/{lead.pk}/create-person/",
            {"national_code": "0012345679", "father_name": "پدر آزمون"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        lead.refresh_from_db()
        self.assertIsNotNone(lead.enrolled_person_id)
        self.assertEqual(lead.enrolled_person.person_type, Person.Type.STUDENT)
        self.assertEqual(lead.enrolled_person.mobile, lead.phone)
        self.assertEqual(lead.enrolled_person.national_code, "0012345679")
        self.assertIsNone(lead.enrolled_person.student_code)
        lead.enrolled_person.full_clean()

    def test_lead_links_existing_student_by_national_code_without_creating_duplicate(self):
        existing = make_person(person_type="student", national_code="0012345679", student_code="LEGACY-1")
        self.client.force_login(self.employee)
        self.own_lead.status = Lead.Status.RECOMMENDED
        self.own_lead.save(update_fields=["status", "updated_at"])
        response = self.client.post(
            f"/api/leads/{self.own_lead.pk}/create-person/",
            {"national_code": "۰۰۱۲۳۴۵۶۷۹"}, content_type="application/json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.own_lead.refresh_from_db()
        existing.refresh_from_db()
        self.assertEqual(self.own_lead.enrolled_person_id, existing.pk)
        self.assertEqual(existing.student_code, "LEGACY-1")
        self.assertEqual(Person.objects.filter(national_code="0012345679").count(), 1)
        response = self.client.post(f"/api/leads/{self.own_lead.pk}/create-person/", {}, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["already_linked"])

    def test_invalid_national_code_cannot_create_student_file(self):
        self.client.force_login(self.employee)
        self.own_lead.status = Lead.Status.RECOMMENDED
        self.own_lead.save(update_fields=["status", "updated_at"])
        response = self.client.post(
            f"/api/leads/{self.own_lead.pk}/create-person/",
            {"national_code": "0012345678"}, content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("national_code", response.json())
        self.own_lead.refresh_from_db()
        self.assertIsNone(self.own_lead.enrolled_person_id)


class LeadAccessPolicyTests(TestCase):
    def setUp(self):
        self.manager = UserFactory(username="lead-access-manager", roles=["manager"])
        self.operator = UserFactory(username="lead-access-operator", roles=[])
        self.assessor = UserFactory(username="lead-access-assessor", roles=["employee"])
        self.assessor_person = make_person(user=self.assessor, person_type="employee", can_assess_leads=True)
        self.other_person = make_person(person_type="employee", can_assess_leads=True)
        self.course = Course.objects.create(title="دوره تعیین سطح")
        self.lesson = Lesson.objects.create(title="درس تعیین سطح")
        CourseLesson.objects.create(course=self.course, lesson=self.lesson)
        self.lead = Lead.objects.create(student_name="لید خودم", phone="09123456789", assessor=self.assessor_person,
                                        created_by=self.manager, status=Lead.Status.SENT)
        self.other_lead = Lead.objects.create(student_name="لید دیگر", phone="09123456788", assessor=self.other_person,
                                              created_by=self.manager, status=Lead.Status.SENT)

    def _grant(self, user, key="leads-dashboard", verbs=None, resource_type="page"):
        return PersonACLEntry.objects.create(user=user, resource_type=resource_type, resource_key=key,
                                             verbs=["view"] if verbs is None else verbs)

    def _post(self, lead, action, data=None):
        return self.client.post(f"/api/leads/{lead.pk}/{action}/", data or {}, content_type="application/json")

    def _complete_placement(self, user):
        self.client.force_login(user)
        self.assertEqual(self._post(self.other_lead, "assess", {"result": "سطح پایه"}).status_code, 200)
        response = self._post(self.other_lead, "recommend", {"course": str(self.course.pk), "lesson": str(self.lesson.pk)})
        self.assertEqual(response.status_code, 200, response.content)
        self.other_lead.refresh_from_db()
        self.assertEqual(self.other_lead.status, Lead.Status.RECOMMENDED)
        self.assertEqual(self.other_lead.assessor_id, self.other_person.pk)
        self.assertEqual(self.other_lead.assessments.get().recorded_by_id, user.pk)
        recommendation = self.other_lead.recommendations.get()
        self.assertEqual(recommendation.assessor_id, self.other_person.pk)
        self.assertEqual(recommendation.recorded_by_id, user.pk)

    def test_manager_without_assessor_profile_can_complete_placement(self):
        self._complete_placement(self.manager)

    def test_manager_with_non_assessor_profile_can_complete_placement(self):
        make_person(user=self.manager, person_type="employee", can_assess_leads=False)
        self._complete_placement(self.manager)

    def test_superuser_without_roles_can_complete_placement(self):
        self._complete_placement(UserFactory(username="lead-superuser", roles=[], is_superuser=True))

    def test_page_grant_allows_full_lead_management(self):
        self._grant(self.operator)
        self.client.force_login(self.operator)
        response = self.client.get("/leads/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_lead_operator"])
        self.assertTrue(response.context["sidebar_visibility"]["leads_dashboard"])
        self.assertEqual(self.client.get("/api/leads/").json()["count"], 2)
        self._complete_placement(self.operator)

    def test_full_model_grant_allows_full_lead_management(self):
        self._grant(self.operator, key="leads.lead", verbs=["view", "add", "change", "delete"], resource_type="model")
        self._complete_placement(self.operator)

    def test_assessor_with_explicit_management_grant_gets_full_access(self):
        self._grant(self.assessor)
        self._complete_placement(self.assessor)

    def test_management_grant_allows_intake_referral_edit_archive_delete_and_enrollment(self):
        self._grant(self.operator)
        self.client.force_login(self.operator)
        self.assertEqual(self.client.get("/api/leads/assessors/").status_code, 200)
        response = self.client.post("/api/leads/", {
            "student_name": "لید جدید", "age": 10, "phone": "09123456789", "neighborhood": "محله",
            "assessment_date": (timezone.localdate() + timedelta(days=1)).isoformat(), "assessment_time": "10:30",
            "assessor": str(self.other_person.pk),
        }, content_type="application/json")
        self.assertEqual(response.status_code, 201, response.content)
        created = Lead.objects.get(student_name="لید جدید")
        self.assertEqual(created.created_by_id, self.operator.pk)
        self.assertEqual(self.client.patch(f"/api/leads/{created.pk}/", {"neighborhood": "محله جدید"},
                                          content_type="application/json").status_code, 200)
        self.assertEqual(self._post(created, "send", {"assessor": str(self.assessor_person.pk)}).status_code, 200)
        created.refresh_from_db()
        self.assertEqual(created.assessor_id, self.assessor_person.pk)
        self.assertEqual(self._post(created, "archive").status_code, 200)
        self.assertEqual(self._post(created, "delete").status_code, 200)
        self.assertFalse(Lead.objects.filter(pk=created.pk).exists())
        student = make_person(person_type="student")
        self.assertEqual(self._post(self.lead, "enroll", {"enrolled_person": str(student.pk)}).status_code, 200)
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.enrolled_person_id, student.pk)

    def test_hiding_sidebar_link_does_not_revoke_management_grant(self):
        from apps.org.models import SidebarVisibilityRule

        self._grant(self.operator)
        SidebarVisibilityRule.objects.create(user=self.operator, item_key="leads-dashboard", is_visible=False)
        self.client.force_login(self.operator)
        response = self.client.get("/leads/")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["sidebar_visibility"]["leads_dashboard"])

    def test_employee_role_alone_does_not_grant_lead_management(self):
        employee = UserFactory(username="lead-ordinary-employee", roles=["employee"])
        self.assertFalse(is_lead_operator(employee))
        self.client.force_login(employee)
        self.assertEqual(self.client.get("/leads/").status_code, 404)
        self.assertEqual(self.client.get("/api/leads/").status_code, 403)

    def test_partial_model_grant_does_not_grant_management(self):
        self._grant(self.operator, key="leads.lead", resource_type="model")
        self.assertFalse(is_lead_operator(self.operator))
        self.client.force_login(self.operator)
        self.assertEqual(self._post(self.lead, "archive").status_code, 403)

    def test_explicit_denial_restricts_role_baseline(self):
        self._grant(self.manager, verbs=[])
        self.assertFalse(is_lead_operator(self.manager))
        self.client.force_login(self.manager)
        self.assertEqual(self.client.get("/leads/").status_code, 404)
        self.assertEqual(self._post(self.lead, "assess", {"result": "سطح پایه"}).status_code, 403)

    def test_revoked_management_grant_no_longer_allows_access(self):
        self._grant(self.operator).soft_delete()
        self.assertFalse(is_lead_operator(self.operator))

    def test_non_teacher_assessor_can_finish_own_placement(self):
        self.client.force_login(self.assessor)
        self.assertEqual(self.client.get("/leads/assessments/").status_code, 200)
        self.assertEqual(self._post(self.lead, "assess", {"result": "سطح پایه"}).status_code, 200)
        response = self._post(self.lead, "recommend", {"course": str(self.course.pk)})
        self.assertEqual(response.status_code, 200, response.content)
        self.assertNotIn("created_by_name", response.json())
        self.assertNotIn("enrolled_person", response.json())

    def test_assessor_cannot_read_or_assess_another_assignment(self):
        self.client.force_login(self.assessor)
        for prefix in ("/api/leads/", "/api/leads/assessments/"):
            self.assertEqual(self.client.get(f"{prefix}{self.other_lead.pk}/").status_code, 404)
            self.assertEqual(self.client.post(f"{prefix}{self.other_lead.pk}/assess/", {"result": "سطح پایه"},
                                             content_type="application/json").status_code, 404)
        self.assertEqual(self._post(self.other_lead, "recommend", {"course": str(self.course.pk)}).status_code, 404)
        self.other_lead.refresh_from_db()
        self.assertEqual(self.other_lead.status, Lead.Status.SENT)
        self.assertFalse(self.other_lead.assessments.exists())

    def test_assessor_cannot_manage_leads_or_register_students(self):
        self.client.force_login(self.assessor)
        self.assertEqual(self.client.get("/leads/").status_code, 404)
        self.assertEqual(self.client.post("/api/leads/", {}, content_type="application/json").status_code, 403)
        self.assertEqual(self.client.patch(f"/api/leads/{self.lead.pk}/", {}, content_type="application/json").status_code, 403)
        for action in ("send", "delete", "archive", "enroll", "create-person"):
            with self.subTest(action=action):
                self.assertEqual(self._post(self.lead, action).status_code, 403)
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.status, Lead.Status.SENT)

    def test_assessor_reads_only_placement_fields_on_both_list_routes(self):
        self.client.force_login(self.assessor)
        for route in ("/api/leads/", "/api/leads/assessments/"):
            data = self.client.get(route).json()
            rows = data["results"] if isinstance(data, dict) else data
            self.assertEqual([row["id"] for row in rows], [str(self.lead.pk)])
            self.assertNotIn("created_by_name", rows[0])
            self.assertNotIn("father_job", rows[0])
        self.assertNotIn("created_by_name", self.client.get(f"/api/leads/{self.lead.pk}/").json())

    def test_course_choices_do_not_require_education_management_permissions(self):
        Course.objects.create(title="دوره غیرفعال", is_active=False)
        deleted_lesson = Lesson.objects.create(title="درس حذف‌شده")
        CourseLesson.objects.create(course=self.course, lesson=deleted_lesson, order=2)
        deleted_lesson.soft_delete()
        self.client.force_login(self.assessor)
        response = self.client.get("/api/leads/courses/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"], [{"id": str(self.course.pk), "title": self.course.title,
                                                       "lesson_titles": [{"id": str(self.lesson.pk), "title": self.lesson.title}]}])
        self.client.force_login(self.operator)
        self.assertEqual(self.client.get("/api/leads/courses/").status_code, 403)

    def test_capability_revocation_removes_queue_and_action_access(self):
        self.assessor_person.can_assess_leads = False
        self.assessor_person.save(update_fields=["can_assess_leads", "updated_at"])
        self.client.force_login(self.assessor)
        self.assertEqual(self.client.get("/leads/assessments/").status_code, 404)
        self.assertEqual(self.client.get("/api/leads/assessments/").status_code, 403)
        self.assertEqual(self._post(self.lead, "assess", {"result": "سطح پایه"}).status_code, 403)

    def test_inactive_or_deleted_profile_loses_assessor_access(self):
        self.client.force_login(self.assessor)
        for changes in ({"is_active": False}, {"is_active": True, "is_deleted": True}):
            self.assessor_person.__class__.all_objects.filter(pk=self.assessor_person.pk).update(**changes)
            self.assertEqual(self.client.get("/api/leads/assessments/").status_code, 403)
            self.assertEqual(self._post(self.lead, "assess", {"result": "سطح پایه"}).status_code, 403)

    def test_management_grant_does_not_allow_inactive_or_deleted_accounts(self):
        self._grant(self.operator)
        self.operator.is_active = False
        self.assertFalse(is_lead_operator(self.operator))
        self.operator.is_active = True
        self.operator.is_deleted = True
        self.assertFalse(is_lead_operator(self.operator))

    def test_existing_workflow_rules_still_require_assessment_before_recommendation(self):
        self.client.force_login(self.manager)
        self.assertEqual(self._post(self.lead, "recommend", {"course": str(self.course.pk)}).status_code, 400)
        self.assertFalse(self.lead.recommendations.exists())

    def test_legacy_scheduled_lead_can_be_assessed(self):
        self.lead.status = "scheduled"
        self.lead.save(update_fields=["status", "updated_at"])
        self.client.force_login(self.assessor)
        response = self.client.post(f"/api/leads/assessments/{self.lead.pk}/assess/", {"result": "سطح پایه"},
                                     content_type="application/json")
        self.assertEqual(response.status_code, 200)

    def _prepare_financial_enrollment(self):
        self._grant(self.operator)
        self.client.force_login(self.operator)
        self.student = make_person(person_type="student")
        self.lead.status = Lead.Status.RECOMMENDED
        self.lead.course = self.course
        self.lead.enrolled_person = self.student
        self.lead.save(update_fields=["status", "course", "enrolled_person", "updated_at"])
        self.offering = CourseOffering.objects.create(course=self.course, title="برگزاری لید", status=CourseOffering.Status.OPEN, capacity=5)
        return {"offering": str(self.offering.pk), "student": str(self.student.pk), "course_amount": 100000,
                "payments": [{"method": "cash", "amount": 100000}]}

    def test_operator_can_finish_financial_enrollment_without_education_roles(self):
        payload = self._prepare_financial_enrollment()
        response = self.client.get(f"/leads/{self.lead.pk}/enrollment/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "window.__LEAD_ENROLLMENT_API__")
        self.assertNotContains(response, "enr-lead-student-code")
        self.assertNotContains(response, "دفتر پرداخت")
        response = self.client.post(f"/api/leads/{self.lead.pk}/enrollments/", payload, content_type="application/json")
        self.assertEqual(response.status_code, 201, response.content)
        self.lead.refresh_from_db()
        self.offering.refresh_from_db()
        self.assertEqual(self.lead.status, Lead.Status.ENROLLED)
        self.assertEqual(self.offering.enrolled_count, 1)
        enrollment = OfferingEnrollment.objects.get(pk=response.json()["id"])
        self.assertEqual(enrollment.student_id, self.student.pk)
        self.assertEqual(enrollment.payments.get().amount, 100000)

    def test_lead_enrollment_offering_lookup_is_limited_to_recommended_course(self):
        self._prepare_financial_enrollment()
        unrelated = CourseOffering.objects.create(course=Course.objects.create(title="دوره دیگر"))
        response = self.client.get(f"/api/leads/{self.lead.pk}/offerings/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["id"] for row in response.json()["results"]], [str(self.offering.pk)])
        self.assertEqual(self.client.get(f"/api/leads/{self.lead.pk}/offerings/{self.offering.pk}/").status_code, 200)
        self.assertEqual(self.client.get(f"/api/leads/{self.lead.pk}/offerings/{unrelated.pk}/").status_code, 404)

    def test_financial_enrollment_cannot_substitute_student_course_or_lead(self):
        payload = self._prepare_financial_enrollment()
        unrelated_student = make_person(person_type="student")
        unrelated_offering = CourseOffering.objects.create(course=Course.objects.create(title="دوره دیگر"))
        for change in ({"student": str(unrelated_student.pk)}, {"offering": str(unrelated_offering.pk)}, {"lead": str(self.other_lead.pk)}):
            response = self.client.post(f"/api/leads/{self.lead.pk}/enrollments/", {**payload, **change}, content_type="application/json")
            self.assertEqual(response.status_code, 400, response.content)
        self.assertFalse(OfferingEnrollment.objects.exists())

    def test_assessor_cannot_access_lead_enrollment_page_or_apis(self):
        self._prepare_financial_enrollment()
        self.client.force_login(self.assessor)
        self.assertEqual(self.client.get(f"/leads/{self.lead.pk}/enrollment/").status_code, 404)
        for path in ("offerings/", f"offerings/{self.offering.pk}/", "enrollments/"):
            self.assertEqual(self.client.get(f"/api/leads/{self.lead.pk}/{path}").status_code, 403)
        self.assertEqual(self.client.post(f"/api/leads/{self.lead.pk}/enrollments/", {}, content_type="application/json").status_code, 403)

    def test_lead_enrollment_preserves_capacity_waitlist_behavior(self):
        payload = self._prepare_financial_enrollment()
        self.offering.enrolled_count = self.offering.capacity
        self.offering.save(update_fields=["enrolled_count", "updated_at"])
        response = self.client.post(f"/api/leads/{self.lead.pk}/enrollments/", payload, content_type="application/json")
        self.assertEqual(response.status_code, 202, response.content)
        self.assertTrue(response.json()["waitlisted"])
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.status, Lead.Status.RECOMMENDED)
        self.assertFalse(OfferingEnrollment.objects.exists())
