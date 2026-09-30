"""ویرایش «دوره»: فقط تغییرات واقعی — بدون ردیف تکراری و بدون دوباره‌سازی سرفصل.

باگ گزارش‌شده: در صفحهٔ «دوره‌ها» وقتی دوره‌ای از قبل درس داشت، هر بار ویرایش و
ذخیره همان درس‌ها دوبار ثبت می‌شد و «برگزاری»/«قیمت» دوبرابر می‌شد.

علت ریشه‌ای (با پروب روی همین مدل‌ها تأیید شد): ذخیرهٔ ویرایش، تمام ردیف‌های
CourseLesson را soft-delete می‌کرد و از نو می‌ساخت، و مدیر M2M جنگو جدول
واسط را بدون فیلتر soft-delete آن join می‌کند؛ پس ردیف مرده هم شمرده می‌شد و
همان درس دو بار در ``lesson_titles``/``total_tuition`` ظاهر می‌شد.

Conventions: TestCase + CaptureQueriesContext برای اثبات «نوشتن نکردن»،
rest_framework.test.APIClient + force_login برای سطح HTTP، UserFactory و
مدل‌های دامنه مستقیم (مثل apps.education.tests_class_formation).
"""
from __future__ import annotations

from django.contrib.auth.models import Permission
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.education.models import Course, CourseLesson, CourseOffering, Lesson
from apps.education.serializers import CourseSerializer
from apps.education.services import create_offering_enrollment
from apps.forms.tests.factories import UserFactory, make_person


def _seed_roles():
    for code in ("manager", "employee", "teacher", "student"):
        Role.objects.get_or_create(code=code, defaults={"name": code, "priority": 50})


class CourseCurriculumDiffTests(TestCase):
    """منطق diff در CourseSerializer: هیچ ردیفی بی‌دلیل دوباره ساخته نمی‌شود."""

    def setUp(self):
        _seed_roles()
        self.lessons = [
            Lesson.objects.create(title=f"درس {i}", tuition=1000 * i, duration_hours=10)
            for i in (1, 2, 3)
        ]
        self.course = Course.objects.create(title="دورهٔ ویرایش", code="edit-course")
        self.save_course(lessons=[self.lessons[0], self.lessons[1]])

    # helpers ────────────────────────────────────────────────────────────────
    def save_course(self, *, lessons=None, **fields):
        data = dict(fields)
        if lessons is not None:
            data["lessons"] = [str(lesson.pk) for lesson in lessons]
        serializer = CourseSerializer(self.course, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        self.course.refresh_from_db()
        return serializer

    def link_rows(self):
        """(lesson_id, order) ردیف‌های زنده، به ترتیب سرفصل."""
        return [
            (str(lesson_id), order)
            for lesson_id, order in CourseLesson.objects.filter(course=self.course)
            .order_by("order").values_list("lesson_id", "order")
        ]

    def all_rows(self):
        return CourseLesson.all_objects.filter(course=self.course)

    # tests ──────────────────────────────────────────────────────────────────
    def test_identical_save_writes_nothing(self):
        rows_before = self.link_rows()
        updated_before = self.course.updated_at

        with CaptureQueriesContext(connection) as queries:
            self.save_course(lessons=[self.lessons[0], self.lessons[1]])

        self.assertEqual(self.link_rows(), rows_before)           # ترتیب/شناسه‌ها دست‌نخورده
        self.assertEqual(self.all_rows().count(), 2)              # ردیف مرده‌ای ساخته نشد
        self.course.refresh_from_db()
        self.assertEqual(self.course.updated_at, updated_before)  # هیچ نوشتنی رخ نداد
        writes = [
            query["sql"] for query in queries.captured_queries
            if query["sql"].strip().upper().startswith(("INSERT", "UPDATE", "DELETE"))
        ]
        self.assertEqual(writes, [])

    def test_repeated_saves_never_duplicate_a_lesson(self):
        for _ in range(3):
            self.save_course(lessons=[self.lessons[0]])

        payload = CourseSerializer(self.course).data
        self.assertEqual(payload["lessons"], [str(self.lessons[0].pk)])
        self.assertEqual(len(payload["lesson_titles"]), 1)
        self.assertEqual(payload["total_tuition"], 1000)
        self.assertEqual(self.all_rows().count(), 1)

    def test_adding_a_lesson_adds_exactly_one_link(self):
        kept = {lesson_id for lesson_id, _ in self.link_rows()}
        self.save_course(lessons=self.lessons)

        rows = self.link_rows()
        self.assertEqual(
            [lesson_id for lesson_id, _ in rows],
            [str(lesson.pk) for lesson in self.lessons],
        )
        self.assertEqual([order for _, order in rows], [1, 2, 3])
        self.assertEqual(self.all_rows().count(), 3)
        # ردیف‌های قبلی دوباره ساخته نشدند (فقط درس سوم اضافه شد)
        self.assertEqual(
            {lesson_id for lesson_id, _ in rows} - {str(self.lessons[2].pk)}, kept
        )

    def test_removing_a_lesson_removes_only_that_link(self):
        rows_before = {
            str(lesson_id): pk
            for lesson_id, pk in self.all_rows().values_list("lesson_id", "pk")
        }
        self.save_course(lessons=[self.lessons[0]])

        self.assertEqual(self.link_rows(), [(str(self.lessons[0].pk), 1)])
        self.assertEqual(self.all_rows().count(), 1)              # ردیف مرده باقی نماند
        self.assertEqual(
            self.all_rows().get().pk, rows_before[str(self.lessons[0].pk)]
        )
        self.assertEqual(CourseSerializer(self.course).data["total_tuition"], 1000)

    def test_reordered_lessons_keep_one_row_each(self):
        self.save_course(lessons=[self.lessons[1], self.lessons[0]])

        self.assertEqual(
            self.link_rows(),
            [(str(self.lessons[1].pk), 1), (str(self.lessons[0].pk), 2)],
        )
        self.assertEqual(self.all_rows().count(), 2)
        self.assertEqual(CourseSerializer(self.course).data["total_tuition"], 3000)

    def test_duplicate_ids_in_payload_create_one_link(self):
        self.save_course(lessons=[self.lessons[0], self.lessons[0], self.lessons[1]])

        self.assertEqual(
            self.link_rows(),
            [(str(self.lessons[0].pk), 1), (str(self.lessons[1].pk), 2)],
        )
        self.assertEqual(self.all_rows().count(), 2)

    def test_changed_field_is_the_only_thing_written(self):
        rows_before = self.link_rows()
        updated_before = self.course.updated_at

        with CaptureQueriesContext(connection) as queries:
            self.save_course(
                lessons=[self.lessons[0], self.lessons[1]], title="دورهٔ ویرایش‌شده"
            )

        self.course.refresh_from_db()
        self.assertEqual(self.course.title, "دورهٔ ویرایش‌شده")
        self.assertEqual(self.link_rows(), rows_before)
        self.assertEqual(self.all_rows().count(), 2)
        self.assertGreater(self.course.updated_at, updated_before)
        course_updates = [
            query["sql"] for query in queries.captured_queries
            if query["sql"].strip().upper().startswith("UPDATE")
            and "education_course_lesson" not in query["sql"]
        ]
        self.assertEqual(len(course_updates), 1)                 # فقط خود دوره، یک بار
        self.assertIn("title", course_updates[0])

    def test_soft_deleted_legacy_link_is_not_double_counted(self):
        # دادهٔ خرابِ باقی‌مانده از ویرایش‌های قدیمی (soft-deleted، بدون حذف فیزیکی)
        CourseLesson.objects.filter(course=self.course, lesson=self.lessons[0]).delete()

        payload = CourseSerializer(self.course).data
        self.assertEqual(payload["lessons"], [str(self.lessons[1].pk)])
        self.assertEqual(len(payload["lesson_titles"]), 1)
        self.assertEqual(payload["total_tuition"], 2000)
        self.assertEqual(
            [lesson.pk for lesson in self.course.alive_lessons()], [self.lessons[1].pk]
        )


class CourseEditAPITests(TestCase):
    """جریان واقعی کاربر: تعریف دوره، بعد ویرایش و ذخیرهٔ همان درس‌ها."""

    def setUp(self):
        _seed_roles()
        self.client = APIClient()
        self.manager = UserFactory(username="course-edit-manager", roles=["manager"])
        self.manager.user_permissions.set(
            Permission.objects.filter(
                content_type__app_label="education",
                codename__in=("view_course", "add_course", "change_course"),
            )
        )
        self.client.force_login(self.manager)
        self.lessons = [
            Lesson.objects.create(title=f"درس API {i}", tuition=2500 * i) for i in (1, 2)
        ]
        self.expected_tuition = 2500 + 5000

    def _create_course(self):
        response = self.client.post(
            "/api/education/courses/",
            {"title": "دورهٔ API", "lessons": [str(lesson.pk) for lesson in self.lessons]},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        return Course.objects.get(pk=response.json()["id"])

    def _patch(self, course, **extra):
        payload = {"lessons": [str(lesson.pk) for lesson in self.lessons]}
        payload.update(extra)
        response = self.client.patch(
            f"/api/education/courses/{course.pk}/", payload, format="json"
        )
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()

    def test_editing_twice_keeps_one_link_per_lesson(self):
        course = self._create_course()

        for _ in range(2):
            data = self._patch(course)
            self.assertEqual(
                data["lessons"], [str(lesson.pk) for lesson in self.lessons]
            )
            self.assertEqual(len(data["lesson_titles"]), 2)
            self.assertEqual(data["total_tuition"], self.expected_tuition)

        self.assertEqual(CourseLesson.all_objects.filter(course=course).count(), 2)

    def test_offering_roster_and_price_use_each_lesson_once(self):
        course = self._create_course()
        self._patch(course)
        self._patch(course, title="دورهٔ API ویرایش‌شده")

        offering = CourseOffering.objects.create(
            course=course, title="برگزاری API",
            status=CourseOffering.Status.OPEN, capacity=5,
        )
        self.assertEqual(offering.lesson_links.count(), 2)
        self.assertEqual(len(CourseSerializer(course).data["lesson_titles"]), 2)

        enrollment = create_offering_enrollment(
            offering=offering, student=make_person(), actor=self.manager,
        )
        self.assertEqual(enrollment.course_amount, self.expected_tuition)
