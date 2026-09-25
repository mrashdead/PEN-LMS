"""
«برگزاری دوره» + «تشکیل کلاس» + session-generator round (Sept 16 2026).

Covers the redesign per the task brief:

  A. CourseOffering.code — auto (of-0001), alive-unique, exact-case preserved.
  B. formation_prefill — the auto-fill read-model for form 2 (lessons filtered
     to the offering, proposed place/hours/teacher/start, suggested class code).
  C. The formula — تعداد جلسات = مدت ÷ طول جلسه (ceil).
  D. form_class / ClassSessionGeneratorService — exactly N numbered sessions per
     (offering, class_code), lesson/teacher/location overrides, two independent
     classes in one offering.
  E. Conflict semantics — push-forward a week (default) vs strict abort+rollback;
     holiday jumping without consuming a number; re-form guard.
  F. update_session — manual single-session move/retune, conflict-excl-self.
  G. HTTP surface — prefill GET, formation POST, preview POST, session PATCH,
     and the role gates.

Conventions match the repo: rest_framework.test.APIClient for JSON posts,
UserFactory roles from seed_roles, plain date objects (engine is gregorian;
the API edge converts jalali).
"""
from __future__ import annotations

import datetime

from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.forms.tests.factories import UserFactory, make_person
from apps.education.models import (
    AcademicHoliday,
    ClassSession,
    Course,
    CourseLesson,
    CourseOffering,
    Lesson,
    Location,
)

_today = datetime.date.today()
_days_to_saturday = (5 - _today.weekday()) % 7
_SAT = _today + datetime.timedelta(days=_days_to_saturday + 7)

def _seed_roles():
    for code in ("manager", "workflow_admin", "employee", "teacher", "student", "hr"):
        Role.objects.get_or_create(code=code, defaults={"name": code, "priority": 50})


# ─────────────────────────────────────────────────────────────────────────────
# shared fixture builder
# ─────────────────────────────────────────────────────────────────────────────

def make_curriculum(*, course_code="cs-py", titles=("python",), hours=20):
    """A course with N lessons (each ``hours`` long) wired through CourseLesson."""
    course = Course.objects.create(title=f"دوره {course_code}", code=course_code)
    lessons = []
    for i, t in enumerate(titles, start=1):
        lesson = Lesson.objects.create(title=t, duration_hours=hours)
        CourseLesson.objects.create(course=course, lesson=lesson, order=i, hours=hours)
        lessons.append(lesson)
    return course, lessons


def make_offering(course, **kw):
    defaults = dict(
        course=course, title="برگزاری پاییز",
        capacity=25, start_date=_SAT,
        schedule={"days": ["sat", "wed"], "start": "16:00", "end": "18:00"},
        auto_skip_holidays=True, status="open",
    )
    defaults.update(kw)
    return CourseOffering.objects.create(**defaults)


def _live_sessions(offering, class_code=""):
    return ClassSession.objects.filter(
        offering=offering, class_code=class_code, is_deleted=False
    ).order_by("session_number")


# ═════════════════════════════════════════════════════════════════════════
# A) offering code
# ═════════════════════════════════════════════════════════════════════════

class OfferingCodeTests(TestCase):
    def setUp(self):
        _seed_roles()
        self.course, _ = make_curriculum()

    def test_code_autofills_when_empty(self):
        off = make_offering(self.course, code="")
        self.assertRegex(off.code, r"^of-\d{4}$")

    def test_user_supplied_case_is_preserved(self):
        off = make_offering(self.course, code="OFFERING-1403-PY01")
        off.refresh_from_db()
        self.assertEqual(off.code, "OFFERING-1403-PY01")

    def test_codes_never_reused_across_offerings(self):
        a = make_offering(self.course, code="")
        b = make_offering(self.course, code="")
        self.assertNotEqual(a.code, b.code)

    def test_serializer_rejects_duplicate_code(self):
        from apps.education.serializers import CourseOfferingSerializer

        make_offering(self.course, code="OFF-1")
        ser = CourseOfferingSerializer(
            data={"course": str(self.course.pk), "code": "OFF-1"}
        )
        self.assertFalse(ser.is_valid())
        self.assertIn("code", ser.errors)


# ═════════════════════════════════════════════════════════════════════════
# B) prefill read-model
# ═════════════════════════════════════════════════════════════════════════

class FormationPrefillTests(TestCase):
    def setUp(self):
        from apps.education.class_formation import formation_prefill

        self.formation_prefill = formation_prefill
        self.course, self.lessons = make_curriculum(
            titles=("python", "data"), hours=20
        )
        self.room = Location.objects.create(name="کلاس ۱", capacity=30)
        self.teacher = make_person(person_type="teacher", first_name="استاد",
                                   last_name="رضایی")
        self.offering = make_offering(
            self.course, location=self.room, instructor=self.teacher,
        )

    def test_prefill_carries_proposed_values(self):
        p = self.formation_prefill(self.offering)
        self.assertEqual(p.offering_id, str(self.offering.pk))
        self.assertEqual(p.location_id, str(self.room.pk))
        self.assertEqual(p.teacher_id, str(self.teacher.pk))
        self.assertEqual(p.schedule["days"], ["sat", "wed"])
        from apps.core.utils import jalali_date_str, persian_numbers

        self.assertEqual(
            p.start_date,
            persian_numbers(jalali_date_str(self.offering.start_date)),
        )
        self.assertEqual(p.total_hours, 40)  # 20+20

    def test_lessons_are_the_offering_curriculum(self):
        p = self.formation_prefill(self.offering)
        self.assertEqual({l.title for l in p.lessons}, {"python", "data"})
        self.assertTrue(all(l.hours == 20 for l in p.lessons))

    def test_suggested_class_code_increments(self):
        from apps.education.class_formation import suggest_class_code

        first = suggest_class_code(self.offering)
        self.assertTrue(first.startswith("CLS-CS-PY-"))
        # a formed class consumes the suggestion → next call offers the next one
        ClassSession.objects.create(
            offering=self.offering, class_code=first, lesson=self.lessons[0],
            session_number=1, session_date=_SAT,
            start_time=datetime.time(16), end_time=datetime.time(18),
        )
        nxt = suggest_class_code(self.offering)
        self.assertNotEqual(nxt, first)
        self.assertTrue(nxt.endswith("-02"))


# ═════════════════════════════════════════════════════════════════════════
# C) the formula
# ═════════════════════════════════════════════════════════════════════════

class SessionCountFormulaTests(TestCase):
    def test_two_hour_sessions_over_twenty_hours(self):
        from apps.education.class_formation import derive_session_count

        n = derive_session_count(
            total_hours=20,
            schedule={"days": ["sat"], "start": "16:00", "end": "18:00"},
        )
        self.assertEqual(n, 10)

    def test_rounds_up_for_uneven_slots(self):
        from apps.education.class_formation import derive_session_count

        n = derive_session_count(
            total_hours=20,
            schedule={"days": ["sat"], "start": "16:00", "end": "17:30"},  # 1.5h
        )
        self.assertEqual(n, 14)  # ceil(20 / 1.5)

    def test_zero_when_inputs_missing(self):
        from apps.education.class_formation import derive_session_count

        self.assertEqual(derive_session_count(total_hours=20, schedule={}), 0)
        self.assertEqual(
            derive_session_count(total_hours=0,
                                 schedule={"start": "16:00", "end": "18:00"}),
            0,
        )


# ═════════════════════════════════════════════════════════════════════════
# D) class formation → sessions
# ═════════════════════════════════════════════════════════════════════════

class ClassFormationEngineTests(TestCase):
    def setUp(self):
        self.course, self.lessons = make_curriculum(titles=("python",), hours=20)
        self.room = Location.objects.create(name="کلاس ۱", capacity=30)
        self.teacher = make_person(person_type="teacher")
        self.offering = make_offering(
            self.course, location=self.room, instructor=self.teacher,
        )

    def test_forms_exactly_ten_numbered_sessions(self):
        from apps.education.class_formation import form_class

        result = form_class(
            offering=self.offering, class_code="CLS-PY-01",
            lesson=self.lessons[0], start_date=_SAT,
        )
        self.assertEqual(result["created"], 10)
        rows = list(_live_sessions(self.offering, "CLS-PY-01"))
        self.assertEqual([s.session_number for s in rows], list(range(1, 11)))
        self.assertTrue(all(s.class_code == "CLS-PY-01" for s in rows))
        self.assertTrue(all(s.lesson_id == self.lessons[0].pk for s in rows))
        self.assertTrue(all(s.teacher_id == self.teacher.pk for s in rows))
        self.assertTrue(all(s.location_id == self.room.pk for s in rows))
        # sat + wed only, 16:00-18:00, first session on the start date
        self.assertTrue(all(s.session_date.weekday() in (5, 2) for s in rows))
        self.assertEqual(rows[0].session_date, _SAT)
        self.assertEqual(rows[0].start_time, datetime.time(16))
        self.assertEqual(rows[0].end_time, datetime.time(18))
        self.assertTrue(all(
            s.status == ClassSession.Status.SCHEDULED for s in rows
        ))

    def test_count_override_wins_over_formula(self):
        from apps.education.class_formation import form_class

        result = form_class(
            offering=self.offering, class_code="CLS-PY-02",
            lesson=self.lessons[0], start_date=_SAT, count=4,
        )
        self.assertEqual(result["created"], 4)
        self.assertEqual(_live_sessions(self.offering, "CLS-PY-02").count(), 4)

    def test_two_classes_in_one_offering_are_independent(self):
        from apps.education.class_formation import form_class

        # second lesson joins the SAME course curriculum (offering-2)
        web = Lesson.objects.create(title="web", duration_hours=4)
        CourseLesson.objects.create(course=self.course, lesson=web, order=2, hours=4)
        offering2 = make_offering(self.course, title="دوم", location=self.room,
                                  instructor=None)
        room2 = Location.objects.create(name="کلاس ۲", capacity=30)

        a = form_class(offering=offering2, class_code="CLS-A",
                       lesson=self.lessons[0], location=room2, start_date=_SAT)
        b = form_class(offering=offering2, class_code="CLS-B",
                       lesson=web, location=self.room, start_date=_SAT)
        self.assertEqual(a["created"], 10)   # 20h / 2h
        self.assertEqual(b["created"], 2)    # 4h  / 2h
        # both start numbering at 1 — per (offering, class_code)
        self.assertEqual(list(_live_sessions(offering2, "CLS-A"))[0].session_number, 1)
        self.assertEqual(list(_live_sessions(offering2, "CLS-B"))[0].session_number, 1)

    def test_lesson_must_belong_to_offering(self):
        from apps.education.class_formation import form_class
        from apps.education.services import EducationServiceError

        other = Lesson.objects.create(title="ناشناس", duration_hours=10)
        with self.assertRaises(EducationServiceError):
            form_class(offering=self.offering, class_code="CLS-X",
                       lesson=other, start_date=_SAT)


# ═════════════════════════════════════════════════════════════════════════
# E) conflicts, holidays, re-form guard
# ═════════════════════════════════════════════════════════════════════════

class FormationConflictTests(TestCase):
    def setUp(self):
        self.course, self.lessons = make_curriculum(titles=("python",), hours=20)
        self.room = Location.objects.create(name="کلاس ۱", capacity=30)
        self.offering = make_offering(self.course, location=self.room)

    def _book_rival(self, day):
        """A foreign class occupying THIS room on ``day`` 16-18."""
        rival = make_offering(self.course, title="رقیب", location=self.room)
        return ClassSession.objects.create(
            offering=rival, class_code="RIVAL", lesson=self.lessons[0],
            session_date=day, start_time=datetime.time(16),
            end_time=datetime.time(18), location=self.room,
        )

    def test_room_conflict_pushes_forward_not_aborts(self):
        from apps.education.class_formation import form_class

        self._book_rival(_SAT)
        result = form_class(offering=self.offering, class_code="CLS-P",
                            lesson=self.lessons[0], start_date=_SAT, count=1)
        self.assertEqual(result["created"], 1)
        self.assertEqual(result["pushed"], [{"from": _SAT.isoformat()}])
        s = _live_sessions(self.offering, "CLS-P").first()
        self.assertEqual(s.session_date, _SAT + datetime.timedelta(days=7))
        self.assertEqual(s.session_date.weekday(), 5)  # still a Saturday

    def test_strict_aborts_and_rolls_back_everything(self):
        from apps.education.class_formation import form_class
        from apps.education.services import ScheduleConflictError

        self._book_rival(_SAT)
        with self.assertRaises(ScheduleConflictError):
            form_class(offering=self.offering, class_code="CLS-S",
                       lesson=self.lessons[0], start_date=_SAT,
                       count=3, strict=True)
        # atomic: nothing landed
        self.assertFalse(ClassSession.objects.filter(
            offering=self.offering, class_code="CLS-S").exists())

    def test_holiday_jumped_without_consuming_number(self):
        from apps.education.class_formation import form_class

        AcademicHoliday.objects.create(
            name="مراسه", scope="institute", date_from=_SAT, date_to=_SAT,
        )
        result = form_class(offering=self.offering, class_code="CLS-H",
                            lesson=self.lessons[0], start_date=_SAT, count=3)
        self.assertEqual(result["created"], 3)
        rows = list(_live_sessions(self.offering, "CLS-H"))
        self.assertEqual([s.session_number for s in rows], [1, 2, 3])
        dates = [s.session_date for s in rows]
        self.assertNotIn(_SAT, dates)
        self.assertEqual(dates[0], _SAT + datetime.timedelta(days=4))  # next wed

    def test_reform_same_code_needs_regenerate(self):
        from apps.education.class_formation import form_class
        from apps.education.services import EducationServiceError

        form_class(offering=self.offering, class_code="CLS-R",
                   lesson=self.lessons[0], start_date=_SAT, count=2)
        with self.assertRaises(EducationServiceError):
            form_class(offering=self.offering, class_code="CLS-R",
                       lesson=self.lessons[0], start_date=_SAT, count=2)
        # with regenerate → back to exactly 2 numbered from 1 again
        r = form_class(offering=self.offering, class_code="CLS-R",
                       lesson=self.lessons[0], start_date=_SAT,
                       count=2, regenerate=True)
        self.assertEqual(r["created"], 2)
        self.assertEqual([s.session_number for s in _live_sessions(self.offering, "CLS-R")],
                         [1, 2])


# ═════════════════════════════════════════════════════════════════════════
# F) manual single-session adjustment
# ═════════════════════════════════════════════════════════════════════════

class ManualSessionEditTests(TestCase):
    def setUp(self):
        self.course, self.lessons = make_curriculum(titles=("python",), hours=20)
        self.room = Location.objects.create(name="کلاس ۱", capacity=30)
        self.offering = make_offering(self.course, location=self.room)
        from apps.education.class_formation import form_class
        form_class(offering=self.offering, class_code="CLS-M",
                   lesson=self.lessons[0], start_date=_SAT, count=3)
        # dates: Sep 19 (sat), Sep 23 (wed), Sep 26 (sat) — 16..18 in room
        self.sessions = list(_live_sessions(self.offering, "CLS-M"))

    def test_move_one_session_to_free_date(self):
        from apps.education.services import update_session

        moved = update_session(session=self.sessions[0],
                               session_date=datetime.date(2026, 11, 28))
        self.assertEqual(moved.session_date, datetime.date(2026, 11, 28))
        self.assertEqual(
            _live_sessions(self.offering, "CLS-M").count(), 3  # nothing lost
        )

    def test_move_onto_another_session_of_the_class_is_refused(self):
        from apps.education.services import ScheduleConflictError, update_session

        second = self.sessions[1]
        with self.assertRaises(ScheduleConflictError):
            update_session(session=self.sessions[0], session_date=second.session_date)

    def test_move_into_free_slot_no_self_conflict(self):
        # exclude-pk matters: the moved row must not collide with itself.
        from apps.education.services import update_session

        kept = update_session(session=self.sessions[0],
                              session_date=datetime.date(2026, 10, 3))  # a free Sat
        self.assertEqual(kept.session_date, datetime.date(2026, 10, 3))

    def test_change_room_checked_against_new_room(self):
        from apps.education.services import ScheduleConflictError, update_session

        other_room = Location.objects.create(name="سالن", capacity=100)
        # someone books the hall exactly on session #2's window
        rival_off = make_offering(self.course, title="سالن‌گیر", location=other_room)
        second = self.sessions[1]
        ClassSession.objects.create(
            offering=rival_off, class_code="H", lesson=self.lessons[0],
            session_date=second.session_date,
            start_time=second.start_time, end_time=second.end_time,
            location=other_room,
        )
        with self.assertRaises(ScheduleConflictError):
            update_session(session=second, location=other_room)
        # a free room is fine
        ok = update_session(session=second, location=other_room,
                            session_date=datetime.date(2026, 12, 5))
        self.assertEqual(ok.location_id, other_room.pk)


# ═════════════════════════════════════════════════════════════════════════
# G) HTTP surface + gates
# ═════════════════════════════════════════════════════════════════════════

class ClassFormationAPITests(TestCase):
    def setUp(self):
        _seed_roles()
        self.client = APIClient()
        self.course, self.lessons = make_curriculum(titles=("python",), hours=20)
        self.room = Location.objects.create(name="کلاس ۱", capacity=30)
        self.teacher = make_person(person_type="teacher")
        self.offering = make_offering(
            self.course, location=self.room, instructor=self.teacher,
        )
        self.mgr = UserFactory(username="cf-mgr", roles=["manager"])

    def test_prefill_endpoint(self):
        self.client.force_login(self.mgr)
        r = self.client.get(f"/api/education/offerings/{self.offering.pk}/formation/")
        self.assertEqual(r.status_code, 200, r.content)
        data = r.json()
        self.assertEqual(data["location"], str(self.room.pk))
        self.assertEqual(data["teacher"], str(self.teacher.pk))
        self.assertEqual(len(data["lessons"]), 1)
        self.assertTrue(data["suggested_class_code"].startswith("CLS-"))
        self.assertEqual(data["schedule"]["days"], ["sat", "wed"])

    def test_preview_endpoint_writes_nothing(self):
        self.client.force_login(self.mgr)
        r = self.client.post(
            "/api/education/class-formation/preview/",
            {"offering": str(self.offering.pk), "lesson": str(self.lessons[0].pk)},
            format="json",
        )
        self.assertEqual(r.status_code, 200, r.content)
        data = r.json()
        self.assertEqual(data["count"], 10)
        self.assertEqual(len(data["sessions"]), 10)
        self.assertTrue(data["complete"])
        self.assertFalse(ClassSession.objects.filter(offering=self.offering).exists())

    def test_formation_post_creates_sessions(self):
        self.client.force_login(self.mgr)
        r = self.client.post(
            "/api/education/class-formation/",
            {"offering": str(self.offering.pk), "lesson": str(self.lessons[0].pk),
             "class_code": "CLS-PY-01"},
            format="json",
        )
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.json()["created"], 10)
        self.assertEqual(_live_sessions(self.offering, "CLS-PY-01").count(), 10)

    def test_formation_rejects_lesson_outside_offering(self):
        self.client.force_login(self.mgr)
        other = Lesson.objects.create(title="بیرون", duration_hours=10)
        r = self.client.post(
            "/api/education/class-formation/",
            {"offering": str(self.offering.pk), "lesson": str(other.pk),
             "class_code": "CLS-BAD"},
            format="json",
        )
        self.assertEqual(r.status_code, 400, r.content)

    def test_student_cannot_form_a_class(self):
        student = UserFactory(username="cf-stu", roles=["student"])
        self.client.force_login(student)
        r = self.client.post(
            "/api/education/class-formation/",
            {"offering": str(self.offering.pk), "lesson": str(self.lessons[0].pk)},
            format="json",
        )
        self.assertEqual(r.status_code, 403)

    def test_session_patch_moves_date(self):
        from django.contrib.auth.models import Permission

        self.mgr.user_permissions.add(
            Permission.objects.get(codename="change_classsession")
        )
        self.client.force_login(self.mgr)
        create = self.client.post(
            "/api/education/class-formation/",
            {"offering": str(self.offering.pk), "lesson": str(self.lessons[0].pk),
             "class_code": "CLS-API"},
            format="json",
        )
        self.assertEqual(create.status_code, 201, create.content)
        first = _live_sessions(self.offering, "CLS-API").first()
        self.assertEqual(first.session_date, _SAT)
        r = self.client.patch(
            f"/api/education/sessions/{first.pk}/",
            {"session_date": "۱۴۰۵/۰۹/۱۵"},  # jalali = 2026-12-06, a free Saturday
            format="json",
        )
        self.assertEqual(r.status_code, 200, r.content)
        first.refresh_from_db()
        self.assertEqual(first.session_date, datetime.date(2026, 12, 6))
