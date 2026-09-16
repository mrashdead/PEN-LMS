"""
Onboarding / workflow-tracking / session-engine / calendars round (Sept 2026).

Five areas, mirroring the task statement:

  A. Hierarchy onboarding matrix + dynamic schema endpoint (service guard).
  B. Atomic student onboarding with guardians (تکفل) — full-or-nothing.
  C. Workflow Tracking ID: allocation, uniqueness, forms exposure.
  D. generate_sessions count-mode: exact N, numbered 1..N, holiday jump,
     conflict push-forward / strict abort.
  E. Role calendars: teacher (attendance links), student (enrolled-only),
     guardian (wards only), resource (staff-only).

Conventions: rest_framework.test.APIClient for JSON posts (repo gotcha),
UserFactory roles from seed_roles (guardian added this round), SQLite-safe.
"""
from __future__ import annotations

import datetime

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.forms.tests.factories import UserFactory, make_person
from apps.persons.models import (
    Person,
    StaffProfile,
    StudentGuardian,
    StudentProfile,
)

_nc = iter(range(700000000, 799999999))

def _next_nc() -> str:
    return str(next(_nc))

def _seed_roles():
    for code in ("employee", "supervisor", "manager", "hr", "workflow_admin",
                 "student", "teacher", "guardian"):
        Role.objects.get_or_create(code=code, defaults={"name": code, "priority": 50})


# ═════════════════════════════════════════════════════════════════════════
# A) hierarchy matrix + dynamic schema
# ═════════════════════════════════════════════════════════════════════════

class HierarchyMatrixTests(TestCase):
    def setUp(self):
        _seed_roles()
        self.client = APIClient()

    def test_matrix_matches_task_spec(self):
        from apps.persons import hierarchy

        sa = {"workflow_admin"}
        self.assertEqual(
            hierarchy.allowed_targets(sa),
            {"manager", "supervisor", "employee", "teacher", "student", "guardian"},
        )
        self.assertEqual(
            hierarchy.allowed_targets({"manager"}),
            {"supervisor", "employee", "teacher", "student", "guardian"},
        )
        self.assertEqual(
            hierarchy.allowed_targets({"supervisor"}),
            {"teacher", "student", "guardian"},
        )
        self.assertEqual(hierarchy.allowed_targets({"employee"}), {"student", "guardian"})
        # students/teachers create nothing
        self.assertEqual(hierarchy.allowed_targets({"student"}), set())
        self.assertEqual(hierarchy.allowed_targets({"teacher"}), set())
        # supervisor+employee composes (union), and supervisor cannot grant manager
        self.assertTrue(hierarchy.can_grant_role({"manager"}, "supervisor"))
        self.assertFalse(hierarchy.can_grant_role({"manager"}, "manager"))
        self.assertTrue(hierarchy.can_grant_role({"workflow_admin"}, "manager"))
        self.assertFalse(hierarchy.can_grant_role({"supervisor"}, "supervisor"))

    def test_targets_endpoint_filters_by_actor(self):
        emp = UserFactory(username="h-emp", roles=["employee"])
        sup = UserFactory(username="h-sup", roles=["supervisor"])
        self.client.force_login(emp)
        r = self.client.get("/api/persons/onboarding/targets/")
        self.assertEqual(r.status_code, 200)
        vals = {t["value"] for t in r.json()["targets"]}
        self.assertEqual(vals, {"student", "guardian"})
        self.client.force_login(sup)
        vals = {t["value"] for t in self.client.get("/api/persons/onboarding/targets/").json()["targets"]}
        self.assertEqual(vals, {"teacher", "student", "guardian"})

    def test_schema_endpoint_dynamic_fields_and_403(self):
        emp = UserFactory(username="h-emp2", roles=["employee"])
        self.client.force_login(emp)
        # step 2 for student → guardians repeater present, REQUIRED
        r = self.client.get("/api/persons/onboarding/schema/?target=student")
        self.assertEqual(r.status_code, 200)
        sections = {s["key"]: s for s in r.json()["sections"]}
        self.assertIn("guardians", sections)
        self.assertTrue(sections["guardians"]["repeatable"])
        self.assertGreaterEqual(sections["guardians"]["min_items"], 1)
        # employee/teacher target → contract/expertise sections, NO guardians
        self.client.force_login(UserFactory(username="h-sup2", roles=["supervisor"]))
        r = self.client.get("/api/persons/onboarding/schema/?target=teacher")
        self.assertEqual(r.status_code, 200)
        keys = {s["key"] for s in r.json()["sections"]}
        self.assertIn("contract", keys)
        self.assertNotIn("guardians", keys)
        # ordinary employee asking for a teacher form → 403, not a leaked shape
        self.client.force_login(emp)
        self.assertEqual(
            self.client.get("/api/persons/onboarding/schema/?target=teacher").status_code,
            403,
        )

    def test_supervisor_without_account_is_refused(self):
        """Roles live on the User — an account-less 'supervisor' would really
        be a plain employee, so the service must refuse instead of half-creating."""
        mgr = UserFactory(username="h-mgr", roles=["manager"])
        self.client.force_login(mgr)
        r = self.client.post("/api/persons/onboarding/create/", {
            "target": "supervisor", "data": {
                "first_name": "س", "last_name": "P", "national_code": _next_nc(),
                "father_name": "x", "mobile": "09123334455",
                "employee_code": "SV-" + _next_nc()[:7],
                "auto_create_user": False,
            }}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("auto_create_user", r.json())
        # with an account it succeeds AND carries the leadership role
        r2 = self.client.post("/api/persons/onboarding/create/", {
            "target": "supervisor", "data": {
                "first_name": "س", "last_name": "P", "national_code": _next_nc(),
                "father_name": "x", "mobile": "09123334466",
                "employee_code": "SV2-" + _next_nc()[:7],
                "auto_create_user": True,
            }}, format="json")
        self.assertEqual(r2.status_code, 201, r2.content)
        self.assertIn("supervisor", Person.objects.get(
            pk=r2.json()["person"]["id"]).user.role_codes())

    def test_service_guard_blocks_direct_call(self):
        from apps.persons.onboarding import OnboardingPermissionError, PersonOnboardingService

        emp = UserFactory(username="h-emp3", roles=["employee"])
        svc = PersonOnboardingService()
        with self.assertRaises(OnboardingPermissionError):
            svc.assert_can_create(emp, "teacher")
        svc.assert_can_create(emp, "student")  # must not raise


# ═════════════════════════════════════════════════════════════════════════
# B) atomic onboarding with guardians
# ═════════════════════════════════════════════════════════════════════════

class StudentOnboardingAtomicTests(TestCase):
    def setUp(self):
        _seed_roles()
        self.client = APIClient()
        self.clerk = UserFactory(username="ob-clerk", roles=["employee"])

    def _payload(self, **over):
        p = {
            "first_name": "زهرا", "last_name": "راهنما",
            "national_code": _next_nc(), "father_name": "رضا",
            "birth_date": "1392/05/10", "gender": "female",
            "mobile": "09122223344", "student_code": "ST-" + _next_nc()[:7],
            "auto_create_user": True,
            "guardians": [
                {"relation": "father", "first_name": "رضا", "last_name": "راهنما",
                 "national_code": _next_nc(), "mobile": "09121110001",
                 "custody_status": "full_guardian", "is_primary": True,
                 "can_receive_billing": True},
                {"relation": "mother", "first_name": "مریم", "last_name": "صادقی",
                 "national_code": _next_nc(), "mobile": "09121110002",
                 "custody_status": "under_custody"},
            ],
        }
        p.update(over)
        return {"target": "student", "data": p}

    def test_full_success_creates_everything(self):
        self.client.force_login(self.clerk)
        r = self.client.post("/api/persons/onboarding/create/", self._payload(), format="json")
        self.assertEqual(r.status_code, 201, r.content)
        body = r.json()
        self.assertEqual(len(body["guardians"]), 2)
        student = Person.objects.get(pk=body["person"]["id"])
        self.assertEqual(student.person_type, Person.Type.STUDENT)
        self.assertTrue(hasattr(student, "student_profile"))
        self.assertTrue(student.user_id)          # account provisioned
        self.assertIn("student", student.user.role_codes())
        self.assertEqual(StudentGuardian.objects.filter(student=student).count(), 2)
        father = student.guardians.filter(relation="father").first().guardian
        self.assertEqual(father.person_type, Person.Type.GUARDIAN)
        self.assertTrue(father.guardian_profile.is_primary)
        self.assertIsNone(father.user)  # guardians get login later, not here
        # a non-standard custody status flagged the student profile, and the
        # chosen custody value landed on the link itself
        self.assertTrue(student.student_profile.is_custody_case)
        self.assertTrue(StudentGuardian.objects.filter(
            student=student, guardian=father, custody_status="full_guardian"
        ).exists())

    def test_missing_guardians_rolls_back_everything(self):
        self.client.force_login(self.clerk)
        payload = self._payload()
        payload["data"]["guardians"] = []
        before = Person.objects.count()
        r = self.client.post("/api/persons/onboarding/create/", payload, format="json")
        self.assertEqual(r.status_code, 400)
        # the atomicity promise: not even the student row survived
        self.assertEqual(Person.objects.count(), before)
        self.assertEqual(StudentProfile.objects.count(), 0)

    def test_existing_guardian_is_linked_not_duplicated(self):
        from apps.persons.services import PersonService

        father = PersonService().create_person(
            national_code=_next_nc(), first_name="رضا", last_name="راهنما",
            person_type="guardian", mobile="09121110001",
        )
        self.client.force_login(self.clerk)
        payload = self._payload()
        payload["data"]["guardians"] = [{
            "relation": "father", "first_name": "رضا", "last_name": "راهنما",
            "national_code": father.national_code, "mobile": "09121110001",
        }]
        r = self.client.post("/api/persons/onboarding/create/", payload, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(
            Person.objects.filter(national_code=father.national_code).count(), 1
        )

    def test_teacher_onboarding_writes_staff_profile(self):
        sup = UserFactory(username="ob-sup", roles=["supervisor"])
        self.client.force_login(sup)
        # teacher step 2 requires employee_code — check the 400 first
        bad = {"target": "teacher", "data": {
            "first_name": "ک", "last_name": "L", "national_code": _next_nc(),
            "father_name": "x", "mobile": "09129990000",
        }}
        r = self.client.post("/api/persons/onboarding/create/", bad, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("employee_code", r.json())
        good = {"target": "teacher", "data": {
            "first_name": "ک", "last_name": "L", "national_code": _next_nc(),
            "father_name": "x", "mobile": "09129990000",
            "employee_code": "TC-" + _next_nc()[:7],
            "contract_type": "حق‌التدریس", "hourly_rate": 250000,
            "weekly_max_hours": 12, "specialization": "ریاضی",
            "experience_years": 5, "staff_kind": "teaching",
            "auto_create_user": True,
        }}
        r = self.client.post("/api/persons/onboarding/create/", good, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        person = Person.objects.get(pk=r.json()["person"]["id"])
        sp = person.staff_profile
        self.assertEqual(sp.kind, StaffProfile.Kind.TEACHING)
        self.assertEqual(sp.weekly_max_hours, 12)
        self.assertIn("teacher", person.user.role_codes())

    def test_clerk_cannot_onboard_teacher(self):
        self.client.force_login(self.clerk)
        r = self.client.post("/api/persons/onboarding/create/", {"target": "teacher", "data": {
            "first_name": "a", "last_name": "b", "national_code": _next_nc(),
            "father_name": "x", "mobile": "09120001111",
            "employee_code": "T-" + _next_nc()[:7],
        }}, format="json")
        self.assertEqual(r.status_code, 403)

    def test_replay_returns_existing_instead_of_second_person(self):
        self.client.force_login(self.clerk)
        payload = self._payload()
        first = self.client.post("/api/persons/onboarding/create/", payload, format="json")
        self.assertEqual(first.status_code, 201)
        second = self.client.post("/api/persons/onboarding/create/", payload, format="json")
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.json().get("replayed"))
        self.assertEqual(
            first.json()["person"]["id"], second.json()["person"]["id"]
        )


# ═════════════════════════════════════════════════════════════════════════
# C) workflow tracking id
# ═════════════════════════════════════════════════════════════════════════

class TrackingNumberTests(TestCase):
    def setUp(self):
        _seed_roles()
        from apps.workflow.models import State, Transition, WorkflowDefinition
        from apps.workflow.tests.test_services import _definition

        self.definition = _definition(code="track-wf")
        self.employee = UserFactory(username="trk-emp", roles=["employee"])
        self.manager = UserFactory(username="trk-mgr", roles=["manager"])
        from apps.workflow.services import WorkflowEngineService
        self.engine = WorkflowEngineService()

    def test_create_instance_allocates_sequential_ids(self):
        a = self.engine.create_instance("track-wf", self.employee, "تست ۱")
        b = self.engine.create_instance("track-wf", self.employee, "تست ۲")
        year = a.created_at.year
        self.assertEqual(a.tracking_number, f"REQ-{year}-000001")
        self.assertEqual(b.tracking_number, f"REQ-{year}-000002")

    def test_rolled_back_create_does_not_consume_number(self):
        from django.db import transaction

        from apps.workflow.models import RequestSequence
        from django.utils import timezone as tz

        year = tz.now().year
        # One counter row per year (global): the number carries no process code.
        base = (
            RequestSequence.objects.filter(year=year)
            .values_list("last_value", flat=True).first() or 0
        )
        with self.assertRaises(RuntimeError), transaction.atomic():
            self.engine.create_instance("track-wf", self.employee, "x")
            raise RuntimeError("boom")
        a = self.engine.create_instance("track-wf", self.employee, "پس از رول‌بک")
        self.assertEqual(a.tracking_number, f"REQ-{year}-{base + 1:06d}")

    def test_forms_detail_exposes_tracking(self):
        from apps.forms.models import FormSchema, FormSubmission
        from apps.forms.serializers import FormSubmissionDetailSerializer

        schema = FormSchema.objects.create(
            slug="track-form", title="فرم پیگیری", version=1,
            fields=[{"key": "title", "type": "text", "order": 1,
                     "label": "عنوان", "required": True}],
        )
        sub = FormSubmission.objects.create(
            form_schema=schema, submitted_by=self.employee,
            submission_number="TRK-0001", data={},
        )
        instance = self.engine.create_instance("track-wf", self.employee, sub.submission_number)
        sub.workflow_instance = instance
        sub.save(update_fields=["workflow_instance"])
        data = FormSubmissionDetailSerializer(sub).data
        self.assertEqual(data["tracking_number"], instance.tracking_number)
        self.assertEqual(data["workflow_status"], "running")


# ═════════════════════════════════════════════════════════════════════════
# D) session generation engine (count mode)
# ═════════════════════════════════════════════════════════════════════════

class SessionEngineTests(TestCase):
    def setUp(self):
        from apps.education.models import Course, CourseOffering, Location

        self.client = APIClient()
        self.course = Course.objects.create(title="هندسه", code="CRS-TR")
        self.room = Location.objects.create(name="کلاس ۱", capacity=30)
        self.offering = CourseOffering.objects.create(
            course=self.course, title="هندسه ۱",
            start_date=datetime.date(2026, 9, 19),          # a Saturday
            location=self.room,
            schedule={"days": ["sat", "tue"], "start": "16:00", "end": "17:30"},
        )

    def _sessions(self):
        from apps.education.models import ClassSession

        return ClassSession.objects.filter(
            offering=self.offering, is_deleted=False
        ).order_by("session_number")

    def test_exactly_20_contiguous_numbered_sessions(self):
        from apps.education.services import generate_sessions

        result = generate_sessions(offering=self.offering, count=20)
        self.assertEqual(result["created"], 20)
        rows = list(self._sessions())
        self.assertEqual([s.session_number for s in rows], list(range(1, 21)))
        self.assertTrue(all(s.location_id == self.room.pk for s in rows))
        self.assertTrue(all(s.start_time.hour == 16 for s in rows))
        # sat + tue only
        self.assertTrue(all(s.session_date.weekday() in (5, 1) for s in rows))

    def test_holidays_are_jumped_without_consuming_numbers(self):
        from apps.education.models import AcademicHoliday
        from apps.education.services import generate_sessions

        # institute closure over the FIRST scheduled Saturday (2026-09-19)
        AcademicHoliday.objects.create(
            name="مراسه", scope="institute",
            date_from=datetime.date(2026, 9, 19), date_to=datetime.date(2026, 9, 20),
        )
        result = generate_sessions(offering=self.offering, count=4)
        self.assertEqual(result["created"], 4)
        dates = [s.session_date for s in self._sessions()]
        self.assertNotIn(datetime.date(2026, 9, 19), dates)
        self.assertEqual([s.session_number for s in self._sessions()], [1, 2, 3, 4])
        self.assertEqual(dates[0], datetime.date(2026, 9, 22))  # next tue

    def test_room_conflict_strict_raises_and_keeps_nothing(self):
        from apps.education.models import ClassSession, CourseOffering
        from apps.education.services import ScheduleConflictError, generate_sessions

        # another class holds the room on the first slot (different offering)
        other = CourseOffering.objects.create(
            course=self.course, title="دیگر", location=self.room,
            start_date=datetime.date(2026, 9, 19),
        )
        ClassSession.objects.create(
            offering=other, session_date=datetime.date(2026, 9, 19),
            start_time="16:00", end_time="17:30", location=self.room,
            session_number=1,
        )
        with self.assertRaises(ScheduleConflictError):
            generate_sessions(offering=self.offering, count=3, strict=True)
        self.assertEqual(self._sessions().count(), 0)   # transactional: all-or-nothing

    def test_non_strict_pushes_to_next_week_slot(self):
        from apps.education.models import ClassSession, CourseOffering
        from apps.education.services import generate_sessions

        other = CourseOffering.objects.create(
            course=self.course, title="دیگر", location=self.room,
            start_date=datetime.date(2026, 9, 19),
        )
        ClassSession.objects.create(
            offering=other, session_date=datetime.date(2026, 9, 19),
            start_time="16:00", end_time="17:30", location=self.room,
            session_number=1,
        )
        result = generate_sessions(offering=self.offering, count=3)
        self.assertEqual(result["created"], 3)
        self.assertEqual(len(result["pushed"]), 1)
        dates = [s.session_date for s in self._sessions()]
        self.assertIn(datetime.date(2026, 9, 26), dates)   # pushed +7d, same weekday
        self.assertNotIn(datetime.date(2026, 9, 19), dates)

    def test_regenerate_is_idempotent_rerun(self):
        from apps.education.services import generate_sessions

        generate_sessions(offering=self.offering, count=5)
        result = generate_sessions(offering=self.offering, count=5, regenerate=True)
        self.assertEqual(result["created"], 5)
        rows = list(self._sessions())
        self.assertEqual([s.session_number for s in rows], [1, 2, 3, 4, 5])

    def test_total_sessions_persisted_from_offering(self):
        from apps.education.services import generate_sessions

        self.offering.total_sessions = 6
        self.offering.save(update_fields=["total_sessions"])
        result = generate_sessions(offering=self.offering)   # count from model
        self.assertEqual(result["created"], 6)

    def test_api_accepts_count_and_strict(self):
        from django.contrib.auth.models import Permission

        from apps.education.services import generate_sessions

        # pre-book this offering's OWN first slot is what makes strict fail;
        # with a free calendar both calls must succeed. Counting is per-offering
        # so the two runs add up (regenerate=True on the second).
        admin = UserFactory(username="eng-admin", roles=["workflow_admin"])
        admin.user_permissions.add(
            Permission.objects.get(codename="change_courseoffering")
        )
        self.client.force_login(admin)
        r = self.client.post(
            f"/api/education/offerings/{self.offering.pk}/generate-sessions/",
            {"count": 3}, format="json",
        )
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.json()["created"], 3)
        # second call without regenerate → collides with its own first three
        # slots → strict is off, so it pushes forward a week and still lands 3.
        r2 = self.client.post(
            f"/api/education/offerings/{self.offering.pk}/generate-sessions/",
            {"count": 2}, format="json",
        )
        self.assertEqual(r2.status_code, 200, r2.content)
        self.assertEqual(r2.json()["created"], 2)
        self.assertEqual(self._sessions().count(), 5)

    def test_api_rejects_bad_count(self):
        admin = UserFactory(username="eng-admin2", roles=["workflow_admin"])
        from django.contrib.auth.models import Permission
        admin.user_permissions.add(
            Permission.objects.get(codename="change_courseoffering")
        )
        self.client.force_login(admin)
        r = self.client.post(
            f"/api/education/offerings/{self.offering.pk}/generate-sessions/",
            {"count": 0}, format="json",
        )
        self.assertEqual(r.status_code, 400)
        r = self.client.post(
            f"/api/education/offerings/{self.offering.pk}/generate-sessions/",
            {"count": "abc"}, format="json",
        )
        self.assertEqual(r.status_code, 400)


# ═════════════════════════════════════════════════════════════════════════
# E) role calendars
# ═════════════════════════════════════════════════════════════════════════

class RoleCalendarTests(TestCase):
    def setUp(self):
        _seed_roles()
        self.client = APIClient()
        from apps.education.models import (
            ClassSession, Course, CourseOffering, Location, OfferingEnrollment,
        )

        self.room_a = Location.objects.create(name="سالن A")
        self.room_b = Location.objects.create(name="کلاس B")
        course = Course.objects.create(title="فیزیک", code="CAL-C")
        self.instr_user = UserFactory(username="cal-teacher", roles=["teacher"])
        self.teacher_person = make_person(
            user=self.instr_user, person_type="teacher", first_name="استاد"
        )
        self.offering = CourseOffering.objects.create(
            course=course, title="فیزیک ۱", location=self.room_a,
            instructor=self.teacher_person, capacity=10,
        )
        self.s1 = ClassSession.objects.create(
            offering=self.offering, session_number=1,
            session_date=datetime.date(2026, 10, 3), start_time="09:00",
            end_time="10:30", teacher=self.teacher_person, location=self.room_a,
        )
        self.s2 = ClassSession.objects.create(
            offering=self.offering, session_number=2,
            session_date=datetime.date(2026, 10, 6), start_time="09:00",
            end_time="10:30", teacher=self.teacher_person, location=self.room_a,
        )
        # another teacher's session in another room (must not leak anywhere)
        other_person = make_person(person_type="teacher", first_name="غریبه")
        other = CourseOffering.objects.create(
            course=course, title="شیمی", location=self.room_b,
            instructor=other_person, capacity=10,
        )
        self.other_session = ClassSession.objects.create(
            offering=other, session_number=1,
            session_date=datetime.date(2026, 10, 3), start_time="09:00",
            end_time="10:30", teacher=other_person, location=self.room_b,
        )
        # enrolled student + enrolled ward of a guardian + unenrolled student
        self.student_user = UserFactory(username="cal-student", roles=["student"])
        self.student = make_person(
            user=self.student_user, person_type="student", first_name="ثبت‌نامی"
        )
        OfferingEnrollment.objects.create(offering=self.offering, student=self.student)
        self.ward = make_person(person_type="student", first_name="فرزند")
        OfferingEnrollment.objects.create(offering=self.offering, student=self.ward)
        self.guardian_user = UserFactory(username="cal-guardian", roles=["guardian"])
        self.guardian = make_person(
            user=self.guardian_user, person_type="guardian", first_name="ولی"
        )
        StudentGuardian.objects.create(
            student=self.ward, guardian=self.guardian, relation="mother"
        )
        self.stranger_user = UserFactory(username="cal-stranger", roles=["student"])
        self.stranger_student = make_person(
            user=self.stranger_user, person_type="student", first_name="بیگانه"
        )

    def test_teacher_schedule_has_attendance_links(self):
        self.client.force_login(self.instr_user)
        r = self.client.get(
            "/api/education/calendar/me/?from=2026-10-01&to=2026-10-31"
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("teacher", body["perspectives"])
        sessions = body["teacher"]["sessions"]
        self.assertEqual({s["id"] for s in sessions}, {str(self.s1.pk), str(self.s2.pk)})
        for s in sessions:
            self.assertIn("/workspace/teacher/attendance/", s["attendance_url"])
            self.assertIn(str(s["id"]), s["attendance_url"])

    def test_student_sees_only_enrolled(self):
        self.client.force_login(self.student_user)
        r = self.client.get("/api/education/calendar/me/?from=2026-10-01&to=2026-10-31")
        days = r.json()["learner"]["days"]
        ids = {s["id"] for d in days for s in d["sessions"]}
        self.assertEqual(ids, {str(self.s1.pk), str(self.s2.pk)})
        # the stranger sees NOTHING
        self.client.force_login(self.stranger_user)
        r = self.client.get("/api/education/calendar/me/?from=2026-10-01&to=2026-10-31")
        days = r.json()["learner"]["days"]
        self.assertEqual({s["id"] for d in days for s in d["sessions"]}, set())

    def test_guardian_sees_ward_sessions_labelled(self):
        self.client.force_login(self.guardian_user)
        r = self.client.get("/api/education/calendar/me/?from=2026-10-01&to=2026-10-31")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("learner", body["perspectives"])
        rows = [s for d in body["learner"]["days"] for s in d["sessions"]]
        self.assertEqual({s["id"] for s in rows}, {str(self.s1.pk), str(self.s2.pk)})
        self.assertTrue(all(s["ward"] for s in rows))   # every row tagged with the ward

    def test_resource_calendar_is_staff_gated(self):
        # student → 403
        self.client.force_login(self.student_user)
        self.assertEqual(
            self.client.get("/api/education/calendar/resources/?date=2026-10-03").status_code,
            403,
        )
        # employee (staff) → rooms as rows, both rooms, teacher name attached
        staff = UserFactory(username="cal-clerk", roles=["employee"])
        self.client.force_login(staff)
        r = self.client.get("/api/education/calendar/resources/?date=2026-10-03")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        names = {loc["name"] for loc in body["locations"]}
        self.assertEqual(names, {"سالن A", "کلاس B"})
        room_a = next(l for l in body["locations"] if l["name"] == "سالن A")
        self.assertEqual(room_a["sessions"][0]["teacher"], self.teacher_person.display_name)

    def test_holiday_api_and_scoping(self):
        from django.contrib.auth.models import Permission

        from apps.education.models import AcademicHoliday

        mgr = UserFactory(username="cal-mgr", roles=["manager"])
        # StrictDjangoModelPermissions needs the model perms (seed_groups grants
        # them to the گروه مدیر مؤسسه; unit tests create users without groups).
        mgr.user_permissions.set(
            Permission.objects.filter(
                content_type=ContentType.objects.get_for_model(AcademicHoliday)
            )
        )
        self.client.force_login(mgr)
        r = self.client.post("/api/education/holidays/", {
            "name": "جمعه‌ها", "scope": "weekly", "weekday": 4,
            "date_from": "1405-06-10", "date_to": "1405-06-10",
        }, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        # weekly scope REQUIRES a weekday
        r = self.client.post("/api/education/holidays/", {
            "name": "بدون روز", "scope": "weekly",
            "date_from": "1405-06-10", "date_to": "1405-06-10",
        }, format="json")
        self.assertEqual(r.status_code, 400)
        # student cannot write
        self.client.force_login(self.student_user)
        self.assertEqual(
            self.client.post("/api/education/holidays/", {
                "name": "x", "scope": "institute",
                "date_from": "1405-06-10", "date_to": "1405-06-11",
            }, format="json").status_code,
            403,
        )

    def test_guardian_persons_visible_to_own_wards_only(self):
        from apps.persons.services import persons_visible_to

        visible = persons_visible_to(self.guardian_user)
        self.assertIn(self.ward.pk, [p.pk for p in visible])
        self.assertNotIn(self.student.pk, [p.pk for p in visible])
        self.assertNotIn(self.stranger_student.pk, [p.pk for p in visible])

    def test_guardian_full_pii_of_ward(self):
        from apps.persons.services import can_view_full_person_detail

        self.assertTrue(can_view_full_person_detail(self.guardian_user, self.ward))
        self.assertFalse(can_view_full_person_detail(self.guardian_user, self.student))
