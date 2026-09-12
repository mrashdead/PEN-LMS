"""Capacity enforcement + attendance/education integrity tests (B4/B5).

Run with the project's test settings. Uses the shared forms test factories
(UserFactory, make_person, make_class_group, make_enrollment) so scenarios
mirror the rest of the suite.
"""
from __future__ import annotations

import itertools
import datetime

from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.academics.models import ClassEnrollment, ClassGroup
from apps.education.models import (
    AttendanceRecord,
    ClassSession,
    Course,
    CourseOffering,
    Location,
)
from apps.education.services import (
    CapacityExceededError,
    EducationServiceError,
    ScheduleConflictError,
    bulk_attendance,
    create_session,
    enroll_student,
)

_lesson_seq = itertools.count(1)


def _unique_code(prefix: str) -> str:
    return f"{prefix}-{next(_lesson_seq)}"


class _EnrollmentBase(TestCase):
    def setUp(self):
        from apps.accounts.models import Role

        for code in ("manager", "workflow_admin", "employee", "teacher",
                     "student", "parent", "hr"):
            Role.objects.get_or_create(code=code, defaults={"name": code, "priority": 50})

    @staticmethod
    def _student(**kw):
        from apps.forms.tests.factories import make_person

        defaults = dict(first_name="دانش", last_name=_unique_code("s"))
        defaults.update(kw)
        return make_person(None, "student", **defaults)


class CapacityLockTests(_EnrollmentBase):
    """B4: capacity must be enforced, not display-only."""

    def _group(self, capacity=2):
        from apps.forms.tests.factories import make_class_group

        return make_class_group(capacity=capacity)

    def test_enroll_until_capacity_then_reject(self):
        group = self._group(capacity=2)
        from apps.academics.services import EnrollmentError, enrollment_service

        enrollment_service.enroll(class_group_id=group.pk, student_id=self._student().pk)
        enrollment_service.enroll(class_group_id=group.pk, student_id=self._student().pk)
        with self.assertRaises(EnrollmentError) as ctx:
            enrollment_service.enroll(
                class_group_id=group.pk, student_id=self._student().pk
            )
        self.assertIn("ظرفیت", str(ctx.exception))

    def test_api_enroll_returns_400_when_full(self):
        from apps.forms.tests.factories import UserFactory, make_class_group

        manager = UserFactory(username="cap-manager", roles=["manager", "workflow_admin"])
        group = make_class_group(capacity=1)
        student_a, student_b = self._student(), self._student()
        # Model perms: manager group normally carries them; grant directly.
        self._grant_classgroup_perms(manager)
        self.client.force_login(manager)

        response = self.client.post(
            "/api/academics/enrollments/",
            {"class_group": str(group.pk), "student": str(student_a.pk)},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        response = self.client.post(
            "/api/academics/enrollments/",
            {"class_group": str(group.pk), "student": str(student_b.pk)},
            format="json",
        )
        self.assertEqual(response.status_code, 400, response.content)
        self.assertIn("ظرفیت", response.json()["error"])

    def test_zero_capacity_is_unlimited(self):
        from apps.academics.services import enrollment_service

        group = self._group(capacity=0)
        for _ in range(5):
            enrollment_service.enroll(
                class_group_id=group.pk, student_id=self._student().pk
            )
        self.assertEqual(group.enrollments.filter(is_active=True).count(), 5)

    @staticmethod
    def _grant_classgroup_perms(user):
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType

        from apps.academics import models as ac_models

        perms = []
        for model in (ac_models.AcademicTerm, ac_models.ClassGroup, ac_models.ClassEnrollment):
            perms += list(
                Permission.objects.filter(content_type=ContentType.objects.get_for_model(model))
            )
        user.user_permissions.set(perms)
        for attr in ("_user_perm_cache", "_group_perm_cache", "_perm_cache"):
            if hasattr(user, attr):
                delattr(user, attr)


class EducationSessionAttendanceTests(_EnrollmentBase):
    """education tables: unique attendance, conflict detection, capacity."""

    def _offering(self, capacity=10):
        course = Course.objects.create(
            title="دوره تست", code=_unique_code("course"),
        )
        return CourseOffering.objects.create(
            course=course, title="برگزاری تست", capacity=capacity,
            status=CourseOffering.Status.OPEN,
        )

    def test_attendance_unique_per_session_student(self):
        offering = self._offering()
        session = ClassSession.objects.create(
            offering=offering,
            session_date=datetime.date(2026, 9, 10),
            start_time="08:00", end_time="09:30",
        )
        student = self._student()
        AttendanceRecord.objects.create(session=session, student=student)
        # The live-only UNIQUE(session, student) must refuse a second row.
        # On PostgreSQL an IntegrityError aborts the surrounding transaction,
        # so the expected failure runs inside its own savepoint.
        with self.assertRaises(IntegrityError), transaction.atomic():
            AttendanceRecord.objects.create(session=session, student=student)

    def test_bulk_attendance_is_idempotent_on_repost(self):
        offering = self._offering()
        session = ClassSession.objects.create(
            offering=offering,
            session_date=datetime.date(2026, 9, 10),
            start_time="08:00", end_time="09:30",
        )
        students = [self._student() for _ in range(3)]
        rows = [{"student": s.pk, "status": "present"} for s in students]
        first = bulk_attendance(session=session, rows=rows)
        self.assertEqual(first["created"], 3)
        # Re-post the same roster (double-click / corrected sheet):
        rows[0]["status"] = "absent"
        second = bulk_attendance(session=session, rows=rows)
        self.assertEqual(second["created"], 0)
        self.assertEqual(second["updated"], 3)
        self.assertEqual(
            AttendanceRecord.objects.filter(session=session).count(), 3
        )
        self.assertEqual(
            AttendanceRecord.objects.get(session=session, student=students[0]).status,
            "absent",
        )

    def test_teacher_double_booking_rejected(self):
        from apps.forms.tests.factories import make_person

        teacher = make_person(None, "teacher")
        offering_a = self._offering()
        offering_b = self._offering()
        create_session(
            offering=offering_a, session_date=datetime.date(2026, 9, 10),
            start_time="08:00", end_time="09:30", teacher=teacher,
        )
        with self.assertRaises(ScheduleConflictError):
            create_session(
                offering=offering_b, session_date=datetime.date(2026, 9, 10),
                start_time="09:00", end_time="10:30", teacher=teacher,
            )
        # Non-overlapping window is fine.
        create_session(
            offering=offering_b, session_date=datetime.date(2026, 9, 10),
            start_time="10:00", end_time="11:30", teacher=teacher,
        )

    def test_room_double_booking_rejected(self):
        room = Location.objects.create(name="سالن ۱", code=_unique_code("loc"))
        offering = self._offering()
        create_session(
            offering=offering, session_date=datetime.date(2026, 9, 11),
            start_time="08:00", end_time="09:30", location=room,
        )
        other = self._offering()
        with self.assertRaises(ScheduleConflictError):
            create_session(
                offering=other, session_date=datetime.date(2026, 9, 11),
                start_time="09:00", end_time="10:00", location=room,
            )

    def test_offering_capacity_enforced(self):
        offering = self._offering(capacity=1)
        enroll_student(offering=offering, student=self._student())
        with self.assertRaises(CapacityExceededError):
            enroll_student(offering=offering, student=self._student())
        # DB-level guard too.
        offering.refresh_from_db()
        self.assertEqual(offering.enrolled_count, 1)

    def test_session_time_window_validated(self):
        offering = self._offering()
        with self.assertRaises(IntegrityError), transaction.atomic():
            ClassSession.objects.create(
                offering=offering,
                session_date=datetime.date(2026, 9, 12),
                start_time="10:00", end_time="09:00",
            )

    def test_grade_failure_requires_note(self):
        from django.core.exceptions import ValidationError

        from apps.education.models import GradeRecord

        offering = self._offering()
        student = self._student()
        record = GradeRecord(
            student=student, offering=offering,
            result=GradeRecord.Result.FAILED, teacher_note="   ",
        )
        with self.assertRaises(ValidationError):
            record.clean()
        record.teacher_note = "علت مردود: غیبت‌های مکرر"
        record.clean()  # no raise

    # ── attendance form → table projection (B4 closure) ─────────────────

    def test_attendance_form_projection_is_idempotent(self):
        from apps.education.services import project_attendance_submission

        from apps.forms.tests.factories import make_class_group

        group = make_class_group(capacity=0)
        students = [self._student() for _ in range(2)]
        rows = [
            {"student": s.pk, "status": "present", "note": ""}
            for s in students
        ]
        first = project_attendance_submission(
            class_group_id=group.pk,
            session_date="2026-09-09",
            session_number=3,
            session_start="08:00",
            session_end="09:30",
            rows=rows,
        )
        self.assertEqual(first["created"], 2)
        # Re-post the SAME sheet: must update, not duplicate (B4's original
        # failure mode: two submissions → two rows for one student/session).
        rows[1]["status"] = "absent"
        second = project_attendance_submission(
            class_group_id=group.pk,
            session_date="2026-09-09",
            session_number=3,
            session_start="08:00",
            session_end="09:30",
            rows=rows,
        )
        self.assertEqual(second["created"], 0)
        self.assertEqual(second["updated"], 2)
        self.assertEqual(ClassSession.objects.filter(
            class_group=group, session_date="2026-09-09", session_number=3,
        ).count(), 1)
        self.assertEqual(
            AttendanceRecord.objects.filter(
                session_id=first["session_id"]).count(), 2,
        )
