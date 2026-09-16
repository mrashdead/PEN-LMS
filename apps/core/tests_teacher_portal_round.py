"""
Teacher panel + attendance / report-card portal round (Sept 2026).

Six areas, mirroring the task brief:

  A. RBAC — a pure teacher is 403/404 on every management page but the portal,
     is redirected off the admin dashboard, and the teacher role rides the
     portal write APIs (IsTeacherPortalUser) with row ownership.
  B. Attendance flow — record_session_attendance: one atomic create, refusal
     of duplicate session NUMBER or DATE, edit-by-session_id, bulk upsert
     counters, replace-semantics, invalid status, cancelled guard.
  C. Roster auto-load — the union of OfferingEnrollment + bridged
     ClassEnrollment rows; sheet endpoint merges saved statuses; withdrawn
     students kept flagged.
  D. Descriptive report cards — teacher prefill GET, bulk POST idempotency,
     failed ⇒ note rule, foreign teacher 403.
  E. Learner portal — student self-scope, guardian ward scope + switcher,
     hard 403 for a stranger student id, jalali-formatted session rows.
  F. teacher_classes payload — roster_size / stats / past+recorded session
     flags the dashboard and pickers render.

Conventions: rest_framework.test.APIClient for JSON posts, UserFactory roles
(seed_roles codes), SQLite-safe, Jalali date strings on the API edge.
"""
from __future__ import annotations

import datetime
import itertools

from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.education.models import (
    AttendanceRecord,
    ClassSession,
    Course,
    CourseOffering,
    GradeRecord,
    Lesson,
    Location,
    OfferingEnrollment,
)
from apps.education.services import (
    EducationServiceError,
    record_session_attendance,
    roster_students,
    teacher_classes,
)
from apps.forms.tests.factories import UserFactory, make_person

_codes = itertools.count(1)
_nc = iter(range(800000000, 899999999))


def _code(prefix):
    return f"{prefix}-tp{next(_codes)}"


def _next_nc():
    return str(next(_nc))


def _seed_roles():
    for code in ("manager", "teacher", "student", "guardian", "employee", "hr"):
        Role.objects.get_or_create(code=code, defaults={"name": code, "priority": 50})


class _PortalBase(TestCase):
    """Shared fixtures: teacher + offering with two active students."""

    def setUp(self):
        _seed_roles()
        self.client = APIClient()
        self.teacher_person = make_person(person_type="teacher")
        self.teacher = UserFactory(username="tp-teacher", roles=["teacher"])
        self.teacher_person.user = self.teacher
        self.teacher_person.save(update_fields=["user", "updated_at"])

        self.location = Location.objects.create(name="کلاس ۱۰۱", code=_code("loc"))
        self.course = Course.objects.create(title="دوره پنل", code=_code("cs"))
        self.lesson = Lesson.objects.create(title="درس پنل", code=_code("ls"))
        self.offering = CourseOffering.objects.create(
            course=self.course, title="برگزاری پنل",
            instructor=self.teacher_person, location=self.location,
            capacity=10, status=CourseOffering.Status.RUNNING,
            start_date=datetime.date(2026, 9, 1),
        )
        self.students = [
            make_person(person_type="student", first_name="شاگرد", last_name=f"اول{next(_codes)}")
            for _ in range(2)
        ]
        for s in self.students:
            OfferingEnrollment.objects.create(
                offering=self.offering, student=s,
                course_amount=0, final_amount=0, is_active=True,
            )

    def _record_payload(self, date="1404/06/25", number=None, rows=None, **extra):
        if rows is None:
            rows = [
                {"student": str(s.pk), "status": "present", "note": ""}
                for s in self.students
            ]
        payload = {
            "session_date": date,
            "start_time": "10:00",
            "end_time": "11:30",
            "rows": rows,
        }
        if number is not None:
            payload["session_number"] = number
        payload.update(extra)
        return payload


# ═════════════════════════════════════════════════════════════════════════
# A) RBAC — teacher sees the portal, nothing else
# ═════════════════════════════════════════════════════════════════════════

class TeacherAccessGuardTests(_PortalBase):
    def test_pure_teacher_blocked_from_management_pages(self):
        self.client.force_login(self.teacher)
        for url in (
            "/workspace/lessons/", "/workspace/courses/", "/workspace/offerings/",
            "/workspace/sessions/", "/workspace/locations/", "/workspace/enrollments/",
            "/workspace/reports/", "/workspace/persons/",
        ):
            code = self.client.get(url).status_code
            self.assertIn(code, (403, 404), f"{url} → {code}")

    def test_teacher_can_open_portal_pages(self):
        self.client.force_login(self.teacher)
        for url in (
            "/workspace/teacher/",
            "/workspace/teacher/attendance/",
            "/workspace/teacher/report-cards/",
            "/workspace/timetable/",
        ):
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_dashboard_redirects_pure_teacher_to_portal(self):
        self.client.force_login(self.teacher)
        r = self.client.get("/dashboard/")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/workspace/teacher/", r.url)

    def test_teacher_with_employee_role_keeps_dashboard(self):
        boss = UserFactory(username="tp-teacher-boss", roles=["teacher", "employee"])
        person = make_person(user=boss, person_type="teacher")
        self.client.force_login(boss)
        self.assertEqual(self.client.get("/dashboard/").status_code, 200)

    def test_student_has_no_teacher_portal(self):
        stu = UserFactory(username="tp-student-x", roles=["student"])
        make_person(user=stu, person_type="student")
        self.client.force_login(stu)
        self.assertEqual(self.client.get("/workspace/teacher/attendance/").status_code, 404)
        # but the learner portal is theirs
        self.assertEqual(self.client.get("/workspace/portal/").status_code, 200)

    def test_sessions_visible_to_is_scoped_to_own_teaching(self):
        from apps.academics.scoping import education_sessions_visible_to

        other_person = make_person(person_type="teacher")
        other = CourseOffering.objects.create(
            course=self.course, instructor=other_person, status=CourseOffering.Status.RUNNING,
        )
        ClassSession.objects.create(
            offering=other, session_number=1,
            session_date=datetime.date(2026, 9, 2),
            start_time=datetime.time(8), end_time=datetime.time(9),
            teacher=other_person,
        )
        mine = record_session_attendance(
            offering=self.offering, session_date=datetime.date(2026, 9, 2),
            start_time=datetime.time(10), end_time=datetime.time(11),
            rows=[{"student": self.students[0].pk, "status": "present"}],
            actor=self.teacher,
        )
        visible = education_sessions_visible_to(self.teacher)
        self.assertIn(mine["session_id"], [str(s.pk) for s in visible])
        self.assertEqual(visible.count(), 1)  # the other teacher's row is NOT visible


# ═════════════════════════════════════════════════════════════════════════
# B) Attendance flow — atomicity + duplicate refusal
# ═════════════════════════════════════════════════════════════════════════

class RecordSessionServiceTests(_PortalBase):
    def test_first_sheet_creates_numbered_session_and_rows(self):
        res = record_session_attendance(
            offering=self.offering,
            session_date=datetime.date(2026, 9, 16),
            start_time=datetime.time(10), end_time=datetime.time(11, 30),
            rows=[{"student": s.pk, "status": "present", "note": ""} for s in self.students],
            actor=self.teacher,
        )
        self.assertEqual(res["created"], 2)
        self.assertEqual(res["session_number"], 1)  # auto next-available
        session = ClassSession.objects.get(pk=res["session_id"])
        self.assertEqual(session.status, ClassSession.Status.HELD)
        self.assertEqual(session.teacher_id, self.teacher_person.pk)
        self.assertEqual(session.location_id, self.location.pk)

    def test_duplicate_number_and_duplicate_date_are_refused(self):
        record_session_attendance(
            offering=self.offering, session_date=datetime.date(2026, 9, 16),
            start_time=datetime.time(10), end_time=datetime.time(11),
            session_number=3,
            rows=[{"student": self.students[0].pk, "status": "present"}],
            actor=self.teacher,
        )
        with self.assertRaises(EducationServiceError) as ctx:
            record_session_attendance(
                offering=self.offering, session_date=datetime.date(2026, 9, 20),
                start_time=datetime.time(12), end_time=datetime.time(13),
                session_number=3,  # same number → refuse
                rows=[{"student": self.students[0].pk, "status": "present"}],
                actor=self.teacher,
            )
        self.assertIn("تکراری", str(ctx.exception))
        with self.assertRaises(EducationServiceError) as ctx:
            record_session_attendance(
                offering=self.offering, session_date=datetime.date(2026, 9, 16),
                start_time=datetime.time(14), end_time=datetime.time(15),
                session_number=9,  # same DATE as session #3 → refuse
                rows=[{"student": self.students[0].pk, "status": "present"}],
                actor=self.teacher,
            )
        self.assertIn("ثبت شده است", str(ctx.exception))
        self.assertEqual(ClassSession.objects.filter(offering=self.offering).count(), 1)

    def test_bad_row_status_rolls_back_whole_sheet(self):
        before = ClassSession.objects.filter(offering=self.offering).count()
        with self.assertRaises(EducationServiceError):
            record_session_attendance(
                offering=self.offering, session_date=datetime.date(2026, 9, 17),
                start_time=datetime.time(10), end_time=datetime.time(11),
                rows=[
                    {"student": self.students[0].pk, "status": "present"},
                    {"student": self.students[1].pk, "status": "nope"},
                ],
                actor=self.teacher,
            )
        # the session AND the first valid row are gone — atomic all-or-nothing
        self.assertEqual(ClassSession.objects.filter(offering=self.offering).count(), before)
        self.assertEqual(AttendanceRecord.objects.count(), 0)

    def test_unknown_student_is_a_friendly_error_not_a_500(self):
        import uuid

        before = ClassSession.objects.filter(offering=self.offering).count()
        with self.assertRaises(EducationServiceError):
            record_session_attendance(
                offering=self.offering, session_date=datetime.date(2026, 9, 21),
                start_time=datetime.time(10), end_time=datetime.time(11),
                rows=[{"student": str(uuid.uuid4()), "status": "present"}],
                actor=self.teacher,
            )
        self.assertEqual(ClassSession.objects.filter(offering=self.offering).count(), before)

    def test_edit_via_session_id_updates_instead_of_duplicating(self):
        res = record_session_attendance(
            offering=self.offering, session_date=datetime.date(2026, 9, 16),
            start_time=datetime.time(10), end_time=datetime.time(11),
            rows=[{"student": s.pk, "status": "present", "note": ""} for s in self.students],
            actor=self.teacher,
        )
        again = record_session_attendance(
            offering=self.offering, session_id=res["session_id"],
            session_date=datetime.date(2026, 9, 16),
            start_time=datetime.time(10), end_time=datetime.time(12),  # window corrected
            rows=[
                {"student": self.students[0].pk, "status": "present", "note": ""},
                {"student": self.students[1].pk, "status": "late", "note": "ترافیک"},
            ],
            actor=self.teacher,
        )
        self.assertEqual(again["session_id"], res["session_id"])
        self.assertEqual(again["created"], 0)
        self.assertEqual(again["updated"], 2)
        session = ClassSession.objects.get(pk=res["session_id"])
        self.assertEqual(session.end_time, datetime.time(12))
        rec = AttendanceRecord.objects.get(session=session, student=self.students[1])
        self.assertEqual((rec.status, rec.note), ("late", "ترافیک"))

    def test_replace_drops_missing_students_and_repost_revives(self):
        res = record_session_attendance(
            offering=self.offering, session_date=datetime.date(2026, 9, 18),
            start_time=datetime.time(10), end_time=datetime.time(11),
            rows=[{"student": s.pk, "status": "present", "note": ""} for s in self.students],
            actor=self.teacher, replace=True,
        )
        session = ClassSession.objects.get(pk=res["session_id"])
        record_session_attendance(
            offering=self.offering, session_id=str(session.pk),
            session_date=session.session_date,
            start_time=session.start_time, end_time=session.end_time,
            rows=[{"student": self.students[0].pk, "status": "absent", "note": ""}],
            actor=self.teacher, replace=True,
        )
        self.assertEqual(
            AttendanceRecord.objects.filter(session=session, is_deleted=False).count(), 1)
        # re-add the dropped student → fresh live row (soft-deleted twin ignored)
        record_session_attendance(
            offering=self.offering, session_id=str(session.pk),
            session_date=session.session_date,
            start_time=session.start_time, end_time=session.end_time,
            rows=[{"student": self.students[0].pk, "status": "present", "note": ""},
                  {"student": self.students[1].pk, "status": "excused", "note": "پزشکی"}],
            actor=self.teacher, replace=True,
        )
        self.assertEqual(
            AttendanceRecord.objects.filter(session=session, is_deleted=False).count(), 2)

    def test_cancelled_session_refused_and_time_window_validated(self):
        res = record_session_attendance(
            offering=self.offering, session_date=datetime.date(2026, 9, 19),
            start_time=datetime.time(10), end_time=datetime.time(11),
            rows=[{"student": self.students[0].pk, "status": "present"}],
            actor=self.teacher,
        )
        session = ClassSession.objects.get(pk=res["session_id"])
        session.status = ClassSession.Status.CANCELLED
        session.save(update_fields=["status", "updated_at"])
        with self.assertRaises(EducationServiceError):
            record_session_attendance(
                offering=self.offering, session_id=str(session.pk),
                session_date=session.session_date,
                start_time=session.start_time, end_time=session.end_time,
                rows=[{"student": self.students[0].pk, "status": "present"}],
                actor=self.teacher,
            )
        with self.assertRaises(EducationServiceError):
            record_session_attendance(
                offering=self.offering, session_date=datetime.date(2026, 9, 23),
                start_time=datetime.time(12), end_time=datetime.time(11),  # end < start
                rows=[{"student": self.students[0].pk, "status": "present"}],
                actor=self.teacher,
            )


class RecordSessionApiTests(_PortalBase):
    URL = "/api/education/offerings/{pk}/record-session/"

    def test_teacher_posts_full_sheet_jalali(self):
        self.client.force_login(self.teacher)
        r = self.client.post(
            self.URL.format(pk=self.offering.pk),
            self._record_payload(number=None), format="json",
        )
        self.assertEqual(r.status_code, 200, r.content)
        body = r.json()
        self.assertEqual(body["total"], 2)
        session = ClassSession.objects.get(pk=body["session_id"])
        # 1404/06/25 (jalali) → gregorian
        import jdatetime
        self.assertEqual(
            session.session_date,
            jdatetime.date(1404, 6, 25).togregorian(),
        )

    def test_foreign_teacher_cannot_record(self):
        stranger = UserFactory(username="tp-stranger", roles=["teacher"])
        make_person(user=stranger, person_type="teacher")
        self.client.force_login(stranger)
        r = self.client.post(
            self.URL.format(pk=self.offering.pk),
            self._record_payload(), format="json",
        )
        self.assertEqual(r.status_code, 403)
        self.assertEqual(ClassSession.objects.filter(offering=self.offering).count(), 0)

    def test_student_cannot_use_portal_write_api(self):
        stu = UserFactory(username="tp-stu-write", roles=["student"])
        make_person(user=stu, person_type="student")
        self.client.force_login(stu)
        r = self.client.post(
            self.URL.format(pk=self.offering.pk),
            self._record_payload(), format="json",
        )
        self.assertEqual(r.status_code, 403)

    def test_empty_rows_rejected_400(self):
        self.client.force_login(self.teacher)
        r = self.client.post(
            self.URL.format(pk=self.offering.pk),
            self._record_payload(rows=[]), format="json",
        )
        self.assertEqual(r.status_code, 400)


# ═════════════════════════════════════════════════════════════════════════
# C) Roster auto-load (union of both enrollment worlds) + sheet merge
# ═════════════════════════════════════════════════════════════════════════

class RosterUnionTests(_PortalBase):
    def _class_group_with(self, *students, term_start="2026-01-01"):
        from apps.academics.models import AcademicTerm, ClassEnrollment, ClassGroup

        term = AcademicTerm.objects.create(
            title="ترم تست پنل", start_date=term_start, end_date="2026-12-01",
        )
        group = ClassGroup.objects.create(
            term=term, code=_code("grp"), name="گروه کلاسی",
            teacher=self.teacher_person, is_active=True,
        )
        for s in students:
            ClassEnrollment.objects.create(
                class_group=group, student=s, is_active=True,
            )
        return group

    def test_roster_unions_offering_and_bridged_class_enrollments(self):
        bridged = make_person(person_type="student", last_name="پل زنده")
        group = self._class_group_with(bridged)
        # bridge: a session of THIS offering keys on that class group
        ClassSession.objects.create(
            offering=self.offering, class_group=group, session_number=1,
            session_date=datetime.date(2026, 9, 5),
            start_time=datetime.time(8), end_time=datetime.time(9),
            teacher=self.teacher_person,
        )
        ids = {r["id"] for r in roster_students(offering=self.offering)}
        self.assertEqual(
            ids, {str(s.pk) for s in self.students} | {str(bridged.pk)})
        # a second call for the SAME person through both tables is deduped
        OfferingEnrollment.objects.create(
            offering=self.offering, student=bridged, course_amount=0,
            final_amount=0, is_active=True,
        )
        ids2 = {r["id"] for r in roster_students(offering=self.offering)}
        self.assertEqual(len(ids2), 3)

    def test_inactive_enrollments_excluded(self):
        OfferingEnrollment.objects.filter(
            offering=self.offering, student=self.students[1]
        ).update(is_active=False)
        soft = self.students[1]
        ids = {r["id"] for r in roster_students(offering=self.offering)}
        self.assertNotIn(str(soft.pk), ids)

    def test_sheet_endpoint_prefills_saved_statuses(self):
        res = record_session_attendance(
            offering=self.offering, session_date=datetime.date(2026, 9, 16),
            start_time=datetime.time(10), end_time=datetime.time(11),
            rows=[
                {"student": self.students[0].pk, "status": "absent", "note": "بیماری"},
                {"student": self.students[1].pk, "status": "present", "note": ""},
            ],
            actor=self.teacher,
        )
        self.client.force_login(self.teacher)
        r = self.client.get(
            f"/api/education/offerings/{self.offering.pk}/sheet/",
            {"session": res["session_id"]},
        )
        self.assertEqual(r.status_code, 200, r.content)
        body = r.json()
        by_id = {row["id"]: row for row in body["rows"]}
        self.assertEqual(by_id[str(self.students[0].pk)]["status"], "absent")
        self.assertEqual(by_id[str(self.students[0].pk)]["note"], "بیماری")
        self.assertEqual(by_id[str(self.students[1].pk)]["status"], "present")
        self.assertEqual(len(body["sessions"]), 1)
        self.assertEqual(body["offering"]["id"], str(self.offering.pk))

    def test_sheet_keeps_withdrawn_students_flagged(self):
        res = record_session_attendance(
            offering=self.offering, session_date=datetime.date(2026, 9, 16),
            start_time=datetime.time(10), end_time=datetime.time(11),
            rows=[{"student": s.pk, "status": "present", "note": ""} for s in self.students],
            actor=self.teacher,
        )
        OfferingEnrollment.objects.filter(
            offering=self.offering, student=self.students[1]
        ).update(is_active=False)
        self.client.force_login(self.teacher)
        r = self.client.get(
            f"/api/education/offerings/{self.offering.pk}/sheet/",
            {"session": res["session_id"]},
        )
        rows = {x["id"]: x for x in r.json()["rows"]}
        self.assertNotIn(str(self.students[1].pk),
                         [x["id"] for x in rows.values() if not x.get("inactive")])
        self.assertTrue(rows[str(self.students[1].pk)]["inactive"])
        self.assertEqual(rows[str(self.students[1].pk)]["status"], "present")


# ═════════════════════════════════════════════════════════════════════════
# D) Descriptive report cards
# ═════════════════════════════════════════════════════════════════════════

class ReportCardTests(_PortalBase):
    URL = "/api/education/offerings/{pk}/report-cards/"

    def _post(self, user, rows):
        self.client.force_login(user)
        return self.client.post(
            self.URL.format(pk=self.offering.pk), {"rows": rows}, format="json")

    def test_bulk_save_then_get_prefills(self):
        r = self._post(self.teacher, [
            {"student": str(self.students[0].pk), "result": "passed",
             "teacher_note": "عملکرد خوب، مشارکت فعال"},
            {"student": str(self.students[1].pk), "result": "failed",
             "teacher_note": "غیبت‌های مکرر و تکالیف انجام‌نشده"},
        ])
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.json()["created"], 2)
        g = self.client.get(self.URL.format(pk=self.offering.pk))
        self.assertEqual(g.status_code, 200)
        body = g.json()
        self.assertEqual(len(body["roster"]), 2)
        cards = {c["student"]: c for c in body["cards"]}
        self.assertEqual(cards[str(self.students[1].pk)]["result"], "failed")

    def test_repost_updates_not_duplicates(self):
        self._post(self.teacher, [
            {"student": str(self.students[0].pk), "result": "failed",
             "teacher_note": "تلاش ناکافی"},
        ])
        r = self._post(self.teacher, [
            {"student": str(self.students[0].pk), "result": "passed",
             "teacher_note": "جبران در نوبت دوم"},
        ])
        self.assertEqual(r.json()["updated"], 1)
        self.assertEqual(GradeRecord.objects.filter(offering=self.offering).count(), 1)

    def test_failed_without_note_rejected(self):
        r = self._post(self.teacher, [
            {"student": str(self.students[0].pk), "result": "failed",
             "teacher_note": "  "},
        ])
        self.assertEqual(r.status_code, 400)
        self.assertEqual(GradeRecord.objects.count(), 0)

    def test_duplicate_student_rows_rejected_atomically(self):
        r = self._post(self.teacher, [
            {"student": str(self.students[0].pk), "result": "passed", "teacher_note": "خوب"},
            {"student": str(self.students[0].pk), "result": "failed", "teacher_note": "بد"},
        ])
        self.assertEqual(r.status_code, 400)
        self.assertEqual(GradeRecord.objects.count(), 0)

    def test_foreign_teacher_403_on_get_and_post(self):
        stranger = UserFactory(username="tp-stranger-rc", roles=["teacher"])
        make_person(user=stranger, person_type="teacher")
        self.client.force_login(stranger)
        self.assertEqual(self.client.get(self.URL.format(pk=self.offering.pk)).status_code, 403)
        self.assertEqual(
            self.client.post(self.URL.format(pk=self.offering.pk),
                             {"rows": [{"student": str(self.students[0].pk),
                                        "result": "passed", "teacher_note": "x"}]},
                             format="json").status_code, 403)


# ═════════════════════════════════════════════════════════════════════════
# E) Learner portal — student self, guardian wards, stranger denied
# ═════════════════════════════════════════════════════════════════════════

class LearnerPortalTests(_PortalBase):
    def setUp(self):
        super().setUp()
        # one recorded session for the students
        self.rec = record_session_attendance(
            offering=self.offering, session_date=datetime.date(2026, 9, 16),
            start_time=datetime.time(10), end_time=datetime.time(11, 30),
            rows=[
                {"student": self.students[0].pk, "status": "late", "note": "ترافیک صبح"},
                {"student": self.students[1].pk, "status": "absent", "note": "مذکور"},
            ],
            actor=self.teacher,
        )
        self.stu0 = UserFactory(username="tp-stu0", roles=["student"])
        p0 = self.students[0]
        p0.user = self.stu0
        p0.save(update_fields=["user", "updated_at"])
        self.guard_user = UserFactory(username="tp-guard", roles=["guardian"])
        self.guard_person = make_person(user=self.guard_user, person_type="guardian")
        from apps.persons.models import StudentGuardian
        StudentGuardian.objects.create(
            guardian=self.guard_person, student=self.students[0],
            relation="father", is_active=True,
        )

    def test_student_sees_only_own_rows(self):
        self.client.force_login(self.stu0)
        r = self.client.get("/api/education/portal/")
        self.assertEqual(r.status_code, 200, r.content)
        body = r.json()
        sess = body["attendance"]["sessions"]
        self.assertEqual(len(sess), 1)
        self.assertEqual(sess[0]["status"], "late")
        self.assertEqual(sess[0]["note"], "ترافیک صبح")
        self.assertIn("date_jalali", sess[0])
        self.assertRegex(sess[0]["date_jalali"], r"^[۰-۹]{4}/")
        self.assertEqual(body["attendance"]["totals"]["late"], 1)
        self.assertEqual(
            [s["id"] for s in body["students"]], [str(self.students[0].pk)])

    def test_student_cannot_open_another_student(self):
        self.client.force_login(self.stu0)
        r = self.client.get(
            "/api/education/portal/", {"student": str(self.students[1].pk)})
        self.assertEqual(r.status_code, 403)
        # the 403 payload only lists THIS caller's own scope — not the target
        self.assertEqual([s["id"] for s in r.json()["students"]],
                         [str(self.students[0].pk)])

    def test_guardian_switches_between_wards(self):
        from apps.persons.models import StudentGuardian
        StudentGuardian.objects.create(
            guardian=self.guard_person, student=self.students[1],
            relation="mother", is_active=True,
        )
        self.client.force_login(self.guard_user)
        r = self.client.get("/api/education/portal/")
        self.assertEqual(r.status_code, 403)   # ambiguous — must pick a ward
        self.assertEqual(len(r.json()["students"]), 2)
        r = self.client.get(
            "/api/education/portal/", {"student": str(self.students[1].pk)})
        self.assertEqual(r.status_code, 200, r.content)
        body = r.json()
        self.assertEqual(body["student"]["id"], str(self.students[1].pk))
        self.assertEqual(body["attendance"]["totals"]["absent"], 1)

    def test_guardian_outside_wards_denied(self):
        from apps.persons.models import Person
        stranger_student = make_person(person_type="student", last_name="بیگانه")
        self.client.force_login(self.guard_user)
        r = self.client.get(
            "/api/education/portal/", {"student": str(stranger_student.pk)})
        self.assertEqual(r.status_code, 403)

    def test_teacher_account_without_learner_role_denied(self):
        self.client.force_login(self.teacher)
        r = self.client.get("/api/education/portal/")
        self.assertEqual(r.status_code, 403)

    def test_report_cards_visible_to_student(self):
        from apps.education.services import save_report_cards
        save_report_cards(
            offering=self.offering,
            rows=[{"student": str(self.students[0].pk), "result": "passed",
                   "teacher_note": "عالی بود"}],
            actor=self.teacher,
        )
        self.client.force_login(self.stu0)
        r = self.client.get("/api/education/portal/")
        cards = r.json()["report_cards"]
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]["result_display"], "قبول")
        self.assertEqual(cards[0]["teacher_note"], "عالی بود")


# ═════════════════════════════════════════════════════════════════════════
# F) teacher_classes payload (dashboard + pickers)
# ═════════════════════════════════════════════════════════════════════════

class TeacherClassesTests(_PortalBase):
    def test_payload_carries_roster_size_stats_and_session_flags(self):
        old = record_session_attendance(
            offering=self.offering,
            session_date=datetime.date.today() - datetime.timedelta(days=3),
            start_time=datetime.time(10), end_time=datetime.time(11),
            rows=[{"student": s.pk, "status": "present", "note": ""} for s in self.students],
            actor=self.teacher,
        )
        ClassSession.objects.create(
            offering=self.offering, session_number=2,
            session_date=datetime.date.today() + datetime.timedelta(days=2),
            start_time=datetime.time(10), end_time=datetime.time(11),
            teacher=self.teacher_person,
        )
        rows = teacher_classes(self.teacher)
        self.assertEqual(len(rows), 1)
        c = rows[0]
        self.assertEqual(c["roster_size"], 2)
        self.assertEqual(c["stats"]["total"], 2)
        self.assertEqual(c["stats"]["held"], 1)      # only the recorded one is HELD
        self.assertEqual(c["stats"]["recorded"], 1)
        self.assertEqual(c["stats"]["not_recorded"], 1)
        self.assertEqual(c["stats"]["upcoming"], 1)
        past = [s for s in c["sessions"] if s["past"]]
        upcoming = [s for s in c["sessions"] if not s["past"]]
        self.assertEqual(len(past), 1)
        self.assertEqual(past[0]["recorded"], 2)
        self.assertEqual(len(upcoming), 1)
        self.assertIn("date_jalali", upcoming[0])

    def test_api_returns_own_classes_and_denies_students(self):
        self.client.force_login(self.teacher)
        r = self.client.get("/api/education/teacher/classes/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["results"]), 1)

        stu = UserFactory(username="tp-stu-classes", roles=["student"])
        make_person(user=stu, person_type="student")
        self.client.force_login(stu)
        # IsAcademicManager read_roles excludes students → 403
        self.assertEqual(self.client.get("/api/education/teacher/classes/").status_code, 403)
