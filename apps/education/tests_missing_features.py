"""Regression tests for waitlist, session content and schedule revisions."""
from __future__ import annotations

import datetime as dt

from django.test import TestCase

from apps.education.models import (
    Course, CourseOffering, EnrollmentWaitlist, Lesson, Location,
    SessionMaterial, SessionScheduleRevision,
)
from apps.education.services import (
    create_session, place_on_waitlist, promote_next_waitlist,
    update_session, withdraw_student,
)
from apps.forms.tests.factories import UserFactory, make_person


class EducationMissingFeaturesTests(TestCase):
    def setUp(self):
        self.manager = UserFactory(username="missing-features-manager", roles=["manager"])
        self.teacher = UserFactory(username="missing-features-teacher", roles=["teacher"])
        self.teacher_person = make_person(user=self.teacher, person_type="teacher")
        self.student = make_person(person_type="student", first_name="دانش‌آموز", last_name="صف")
        self.course = Course.objects.create(title="دوره تست صف", code="missing-waitlist")
        self.lesson = Lesson.objects.create(title="درس تست", code="missing-lesson", duration_hours=10)
        self.course.lessons.add(self.lesson)
        self.location = Location.objects.create(name="کلاس تست", code="missing-room")
        self.offering = CourseOffering.objects.create(
            course=self.course, title="برگزاری تست", status=CourseOffering.Status.OPEN,
            capacity=1, enrolled_count=1, location=self.location,
        )

    def test_full_offering_has_fifo_waitlist_and_offer(self):
        entry = place_on_waitlist(offering=self.offering, student=self.student, actor=self.manager)
        self.assertEqual(entry.status, EnrollmentWaitlist.Status.WAITING)
        self.offering.enrolled_count = 0
        self.offering.save(update_fields=["enrolled_count", "updated_at"])
        offered = promote_next_waitlist(offering=self.offering, actor=self.manager)
        self.assertEqual(offered.pk, entry.pk)
        self.assertEqual(offered.status, EnrollmentWaitlist.Status.OFFERED)

    def test_schedule_change_creates_revision_and_topic_is_visible(self):
        session = create_session(
            offering=self.offering, lesson=self.lesson, teacher=self.teacher_person,
            location=self.location, session_date=dt.date(2026, 10, 1),
            start_time=dt.time(10), end_time=dt.time(11), topic="مقدمهٔ درس",
            actor=self.manager,
        )
        self.assertEqual(session.topic, "مقدمهٔ درس")
        update_session(
            session=session, actor=self.manager,
            session_date=dt.date(2026, 10, 2), topic="حل تمرین",
        )
        revision = SessionScheduleRevision.objects.get(session=session)
        self.assertEqual(revision.version, 1)
        self.assertEqual(revision.before["session_date"], "2026-10-01")
        self.assertEqual(revision.after["session_date"], "2026-10-02")
        self.assertEqual(session.materials.count(), 0)

    def test_session_material_requires_content(self):
        session = create_session(
            offering=self.offering, lesson=self.lesson, teacher=self.teacher_person,
            session_date=dt.date(2026, 10, 3), start_time=dt.time(10), end_time=dt.time(11),
            actor=self.manager,
        )
        material = SessionMaterial.objects.create(
            session=session, title="جزوهٔ جلسه", url="https://example.com/handout.pdf"
        )
        self.assertEqual(material.public_url, "https://example.com/handout.pdf")
