import datetime
from types import SimpleNamespace

from apps.academics.models import AcademicTerm, ClassEnrollment, ClassGroup
from apps.core.tests_teacher_portal_round import _PortalBase
from apps.education.models import ClassSession, CourseOffering
from apps.education.serializers import CourseSerializer, CourseOfferingSerializer, OfferingEnrollmentSerializer
from apps.education.services import teacher_classes
from apps.education.teaching import learner_courses, teacher_standalone_classes
from apps.forms.tests.factories import UserFactory, make_person
from apps.education.registration_selectors import RegistrationScope, registration_detail, entity_context


class TeachingIdentityTests(_PortalBase):
    def setUp(self):
        super().setUp()
        self.other_teacher = make_person(person_type="teacher", first_name="مدرس", last_name="دیگر")
        self.term = AcademicTerm.objects.create(title="پاییز", start_date="2026-09-01", end_date="2026-12-31")

    def group(self, **kwargs):
        return ClassGroup.objects.create(term=self.term, name="کلاس الف", code="group-a", **kwargs)

    def test_identity_tracks_teacher_reassignment_and_missing_teacher(self):
        enrollment = self.offering.enrollments.first()
        self.assertEqual(learner_courses(enrollment.student)[0]["teacher"]["id"], str(self.teacher_person.pk))
        self.offering.instructor = self.other_teacher
        self.offering.save()
        self.assertEqual(learner_courses(enrollment.student)[0]["teacher"]["name"], self.other_teacher.display_name)
        enrollment.refresh_from_db()
        self.assertEqual(OfferingEnrollmentSerializer(enrollment).data["teacher"]["id"], str(self.other_teacher.pk))
        self.offering.instructor = None
        self.offering.save()
        self.assertIsNone(learner_courses(enrollment.student)[0]["teacher"])
        self.assertEqual(CourseOfferingSerializer(self.offering).data["instructor_name"], "مدرس تعیین نشده")

    def test_actual_class_teacher_is_separate_and_linked_registration_is_not_duplicated(self):
        group = self.group(offering=self.offering, teacher=self.other_teacher)
        enrollment = self.offering.enrollments.first()
        membership = ClassEnrollment.objects.create(class_group=group, student=enrollment.student)
        enrollment.final_class_enrollment = membership
        enrollment.save()
        rows = learner_courses(enrollment.student)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["instructor"]["id"], str(self.teacher_person.pk))
        self.assertEqual(rows[0]["class_teacher"]["id"], str(self.other_teacher.pk))
        self.assertEqual(rows[0]["teacher"], rows[0]["class_teacher"])

    def test_deleted_teacher_is_not_exposed_and_uses_offering_fallback(self):
        group = self.group(offering=self.offering, teacher=self.other_teacher)
        membership = ClassEnrollment.objects.create(class_group=group, student=self.students[0])
        self.other_teacher.is_deleted = True
        self.other_teacher.save()
        row = learner_courses(membership.student)[-1]
        self.assertIsNone(row["class_teacher"])
        self.assertEqual(row["teacher"]["id"], str(self.teacher_person.pk))

    def test_teacher_reads_own_running_and_preregistration_and_not_foreign_offering(self):
        own_open = CourseOffering.objects.create(course=self.course, instructor=self.teacher_person, status="open")
        foreign = CourseOffering.objects.create(course=self.course, instructor=self.other_teacher, status="running")
        rows = teacher_classes(self.teacher)
        self.assertEqual({r["id"] for r in rows}, {str(self.offering.pk), str(own_open.pk)})
        self.assertNotIn(str(foreign.pk), {r["id"] for r in rows})
        self.assertEqual(next(r for r in rows if r["status"] == "open")["status_label"], "پیش‌ثبت‌نام")

    def test_class_assignment_exposes_offering_but_not_other_classes_or_sessions(self):
        self.offering.instructor = self.other_teacher
        self.offering.save()
        mine = self.group(offering=self.offering, teacher=self.teacher_person)
        foreign = ClassGroup.objects.create(term=self.term, name="کلاس دیگر", code="other", offering=self.offering, teacher=self.other_teacher)
        for index, group in enumerate((mine, foreign), 1):
            ClassSession.objects.create(offering=self.offering, class_group=group, teacher=group.teacher,
                                        session_number=index, session_date=datetime.date(2026, 11, index),
                                        start_time=datetime.time(10), end_time=datetime.time(11))
        rows = teacher_classes(self.teacher)
        self.assertEqual(len(rows), 1)
        self.assertEqual([g["id"] for g in rows[0]["class_groups"]], [str(mine.pk)])
        self.assertEqual(rows[0]["stats"]["total"], 1)
        self.assertFalse(rows[0]["can_manage"])
        self.assertEqual([s["number"] for s in rows[0]["sessions"]], [1])
        mine.is_deleted = True
        mine.save()
        ClassSession.objects.filter(teacher=self.teacher_person).update(is_deleted=True)
        self.assertEqual(teacher_classes(self.teacher), [])

    def test_standalone_class_visible_only_to_its_teacher_and_enrolled_learner(self):
        group = self.group(teacher=self.teacher_person, schedule={"days": ["شنبه"], "start_time": "10:00"})
        ClassEnrollment.objects.create(class_group=group, student=self.students[0])
        self.assertEqual(teacher_standalone_classes(self.teacher)[0]["id"], str(group.pk))
        self.assertEqual(learner_courses(self.students[0])[-1]["class_name"], group.name)
        self.assertEqual(len(learner_courses(self.students[1])), 1)
        group.teacher = self.other_teacher
        group.save()
        self.assertEqual(teacher_standalone_classes(self.teacher), [])

    def test_registration_details_and_course_context_show_current_identity(self):
        manager = UserFactory(username="teaching-manager", roles=["manager"])
        scope = RegistrationScope(manager)
        enrollment = self.offering.enrollments.first()
        row = registration_detail(scope, "offering", enrollment.pk)
        self.assertEqual(row["teacher"]["id"], str(self.teacher_person.pk))
        context = entity_context(scope, "course", self.course.pk)
        self.assertEqual(context["instructors"][0]["instructor"]["id"], str(self.teacher_person.pk))

    def test_learner_api_includes_own_courses_and_no_foreign_student_data(self):
        user = UserFactory(username="teaching-learner", roles=["student"])
        self.students[0].user = user
        self.students[0].save()
        self.client.force_login(user)
        response = self.client.get("/api/education/portal/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["courses"][0]["teacher"]["id"], str(self.teacher_person.pk))
        self.assertEqual(self.client.get("/api/education/portal/", {"student": self.students[1].pk}).status_code, 403)

    def test_course_teacher_names_obey_offering_scope(self):
        CourseOffering.objects.create(course=self.course, instructor=self.other_teacher, status="open")
        teacher_names = CourseSerializer(self.course, context={"request": SimpleNamespace(user=self.teacher)}).data["instructor_names"]
        self.assertIn(self.teacher_person.display_name, teacher_names)
        self.assertNotIn(self.other_teacher.display_name, teacher_names)

    def test_session_assignment_is_a_real_read_relationship(self):
        self.offering.instructor = self.other_teacher
        self.offering.save()
        session = ClassSession.objects.create(offering=self.offering, teacher=self.teacher_person,
                                             session_number=1, session_date=datetime.date(2026, 11, 1),
                                             start_time=datetime.time(10), end_time=datetime.time(11))
        self.assertEqual(teacher_classes(self.teacher)[0]["sessions"][0]["id"], str(session.pk))
        session.is_deleted = True
        session.save()
        self.assertEqual(teacher_classes(self.teacher), [])

    def test_inactive_offering_is_listed_with_read_only_flags(self):
        self.offering.is_active = False
        self.offering.save()
        row = teacher_classes(self.teacher)[0]
        self.assertFalse(row["is_active"])
        self.assertFalse(row["can_manage"])
        self.assertFalse(row["can_write_progress_report"])
