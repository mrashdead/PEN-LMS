"""Publication, learner delivery and row authorization for period reports."""
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.core.utils import to_jalali_date
from apps.education.models import Course, CourseOffering, OfferingEnrollment, StudentProgressReport
from apps.forms.tests.factories import UserFactory, make_person


class ProgressReportTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.teacher = UserFactory(username="progress-teacher", roles=["teacher"])
        self.teacher_person = make_person(user=self.teacher, person_type="teacher")
        self.learner = UserFactory(username="progress-student", roles=["student"])
        self.student = make_person(user=self.learner, first_name="آرمان", person_type="student")
        course = Course.objects.create(code="progress-course", title="ریاضی")
        self.offering = CourseOffering.objects.create(course=course, instructor=self.teacher_person, title="کلاس ریاضی")
        self.enrollment = OfferingEnrollment.objects.create(offering=self.offering, student=self.student)
        self.client.force_authenticate(self.teacher)
        self.today = timezone.localdate()
        self.payload = {
            "offering": str(self.offering.pk), "student": str(self.student.pk), "period": "daily",
            "period_start": self.jalali(self.today), "period_end": self.jalali(self.today),
            "title": "تمرین کسرها", "summary": "شرح کامل\n" + "عملکرد دانش‌آموز در حل تمرین. " * 100,
            "strengths": "حل دقیق مسئله", "improvements": "تمرین بیشتر تقسیم", "homework": "صفحهٔ ۲۰", "next_steps": "مرور کسرها",
        }

    @staticmethod
    def jalali(date):
        return to_jalali_date(date).strftime("%Y/%m/%d")

    def create_report(self, **changes):
        response = self.client.post("/api/education/progress-reports/", {**self.payload, **changes}, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        return response.data

    @staticmethod
    def rows(response):
        return response.data if isinstance(response.data, list) else response.data["results"]

    def test_draft_edit_send_read_round_trip_for_each_period(self):
        for period, days in (("daily", 1), ("weekly", 7), ("monthly", 31)):
            with self.subTest(period=period):
                self.client.force_authenticate(self.teacher)
                report = self.create_report(period=period, period_start=self.jalali(self.today - timedelta(days=days - 1)))
                url = f'/api/education/progress-reports/{report["id"]}/'
                self.assertEqual(report["status"], "draft")
                self.client.force_authenticate(self.learner)
                listing = self.client.get(f"/api/education/portal/progress-reports/?period={period}")
                self.assertEqual(listing.status_code, 200)
                self.assertEqual(self.rows(listing), [])
                self.assertEqual(self.client.post(f'/api/education/portal/progress-reports/{report["id"]}/read/', {}, format="json").status_code, 404)

                self.client.force_authenticate(self.teacher)
                changed = self.client.patch(url, {"title": "عنوان اصلاح‌شده"}, format="json")
                self.assertEqual(changed.status_code, 200, changed.data)
                sent = self.client.post(url + "send/", {}, format="json")
                self.assertEqual(sent.status_code, 200, sent.data)
                self.assertEqual(sent.data["status"], "sent")
                again = self.client.post(url + "send/", {}, format="json")
                self.assertEqual(again.data["sent_at"], sent.data["sent_at"])
                self.assertEqual(self.client.patch(url, {"summary": "تغییر"}, format="json").status_code, 400)

                self.client.force_authenticate(self.learner)
                delivered = self.client.get(f"/api/education/portal/progress-reports/?period={period}")
                self.assertEqual(delivered.status_code, 200)
                self.assertEqual(len(self.rows(delivered)), 1)
                self.assertEqual(self.rows(delivered)[0]["summary"], self.payload["summary"].strip())
                self.assertEqual(self.rows(delivered)[0]["homework"], self.payload["homework"])
                receipt = self.client.post(f'/api/education/portal/progress-reports/{report["id"]}/read/', {}, format="json")
                self.assertEqual(receipt.status_code, 200, receipt.data)
                self.assertIsNotNone(receipt.data["read_at"])
                second = self.client.post(f'/api/education/portal/progress-reports/{report["id"]}/read/', {}, format="json")
                self.assertEqual(second.data["read_at"], receipt.data["read_at"])
        self.assertEqual(StudentProgressReport.objects.count(), 3)

    def test_teacher_cannot_write_for_another_class_or_student(self):
        stranger = UserFactory(username="progress-stranger-teacher", roles=["teacher"])
        make_person(user=stranger, person_type="teacher")
        self.client.force_authenticate(stranger)
        self.assertEqual(self.client.post("/api/education/progress-reports/", self.payload, format="json").status_code, 403)
        self.client.force_authenticate(self.teacher)
        outsider = make_person(person_type="student")
        self.assertEqual(self.client.post("/api/education/progress-reports/", {**self.payload, "student": str(outsider.pk)}, format="json").status_code, 400)
        self.enrollment.is_active = False
        self.enrollment.save()
        self.assertEqual(self.client.post("/api/education/progress-reports/", self.payload, format="json").status_code, 400)
        self.assertFalse(StudentProgressReport.objects.exists())

    def test_iso_today_from_form_is_not_reinterpreted_as_jalali(self):
        report = self.create_report(period_start=self.today.isoformat(), period_end=self.today.isoformat())
        stored = StudentProgressReport.objects.get(pk=report["id"])
        self.assertEqual(stored.period_start, self.today)
        self.assertEqual(stored.period_end, self.today)

    def test_manual_times_survive_edit_and_invalid_times_are_rejected(self):
        yesterday = self.today - timedelta(days=1)
        report = self.create_report(period_start=self.jalali(yesterday), period_end=self.jalali(yesterday), start_time="09:00", end_time="10:00")
        url = f'/api/education/progress-reports/{report["id"]}/'
        edited = self.client.patch(url, {"title": "اصلاح عنوان"}, format="json")
        self.assertEqual(edited.status_code, 200, edited.data)
        self.assertEqual(edited.data["start_time"], "09:00:00")
        self.assertEqual(edited.data["period_start"], report["period_start"])
        invalid = self.client.patch(url, {"end_time": "08:00"}, format="json")
        self.assertEqual(invalid.status_code, 400)
        self.assertIn("بعد از شروع", str(invalid.data))
        invalid = self.client.patch(url, {"end_time": "25:00"}, format="json")
        self.assertEqual(invalid.status_code, 400)
        self.assertIn("ساعت", str(invalid.data))

    def test_other_teacher_cannot_read_edit_or_send_draft(self):
        report = self.create_report()
        stranger = UserFactory(username="progress-draft-stranger", roles=["teacher"])
        make_person(user=stranger, person_type="teacher")
        self.client.force_authenticate(stranger)
        url = f'/api/education/progress-reports/{report["id"]}/'
        self.assertEqual(self.rows(self.client.get("/api/education/progress-reports/")), [])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.patch(url, {"summary": "تغییر"}, format="json").status_code, 404)
        self.assertEqual(self.client.post(url + "send/", {}, format="json").status_code, 404)

    def test_student_cannot_read_another_students_reports_or_write(self):
        report = self.create_report()
        self.client.post(f'/api/education/progress-reports/{report["id"]}/send/', {}, format="json")
        stranger = UserFactory(username="progress-other-student", roles=["student"])
        make_person(user=stranger, person_type="student")
        self.client.force_authenticate(stranger)
        self.assertEqual(self.rows(self.client.get("/api/education/portal/progress-reports/")), [])
        self.assertEqual(self.client.get(f"/api/education/portal/progress-reports/?student={self.student.pk}").status_code, 403)
        self.assertEqual(self.client.post(f'/api/education/portal/progress-reports/{report["id"]}/read/', {}, format="json").status_code, 404)
        self.assertEqual(self.client.post("/api/education/progress-reports/", self.payload, format="json").status_code, 403)

    def test_send_requires_active_learner_account_and_current_membership(self):
        report = self.create_report()
        url = f'/api/education/progress-reports/{report["id"]}/send/'
        self.learner.is_active = False
        self.learner.save()
        self.assertEqual(self.client.post(url, {}, format="json").status_code, 400)
        self.learner.is_active = True
        self.learner.save()
        self.enrollment.is_active = False
        self.enrollment.save()
        self.assertEqual(self.client.post(url, {}, format="json").status_code, 400)
        self.assertEqual(StudentProgressReport.objects.get(pk=report["id"]).status, "draft")

    def test_period_ranges_and_empty_text_are_validated(self):
        invalid = [
            {"period_end": self.jalali(self.today - timedelta(days=1))},
            {"period_start": self.jalali(self.today - timedelta(days=1))},
            {"period": "weekly", "period_start": self.jalali(self.today - timedelta(days=7))},
            {"period": "monthly", "period_start": self.jalali(self.today - timedelta(days=31))},
            {"period_start": self.jalali(self.today + timedelta(days=1)), "period_end": self.jalali(self.today + timedelta(days=1))},
            {"summary": "   "}, {"period": "yearly"},
        ]
        for changes in invalid:
            with self.subTest(changes=changes):
                self.assertEqual(self.client.post("/api/education/progress-reports/", {**self.payload, **changes}, format="json").status_code, 400)
        self.assertFalse(StudentProgressReport.objects.exists())
        self.assertEqual(self.client.get("/api/education/progress-reports/?student=invalid").status_code, 400)

    def test_guardian_access_requires_current_permission_and_does_not_mark_student_read(self):
        from apps.persons.models import StudentGuardian

        report = self.create_report()
        self.client.post(f'/api/education/progress-reports/{report["id"]}/send/', {}, format="json")
        guardian = UserFactory(username="progress-guardian", roles=["guardian"])
        person = make_person(user=guardian, person_type="guardian")
        link = StudentGuardian.objects.create(student=self.student, guardian=person)
        self.client.force_authenticate(guardian)
        url = f"/api/education/portal/progress-reports/?student={self.student.pk}"
        self.assertEqual(self.client.get(url).status_code, 200)
        receipt = self.client.post(f'/api/education/portal/progress-reports/{report["id"]}/read/', {"student": str(self.student.pk)}, format="json")
        self.assertEqual(receipt.status_code, 200)
        self.assertIsNone(receipt.data["read_at"])
        link.can_view_grades = False
        link.save()
        self.assertEqual(self.client.get(url).status_code, 403)
        link.can_view_grades = True
        link.valid_to = self.today - timedelta(days=1)
        link.save()
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_class_report_is_delivered_to_each_active_student_with_independent_receipts(self):
        second_learner = UserFactory(username="progress-student-two", roles=["student"])
        second_student = make_person(user=second_learner, first_name="نگار", person_type="student")
        OfferingEnrollment.objects.create(offering=self.offering, student=second_student)
        payload = {key: value for key, value in self.payload.items() if key != "student"}

        response = self.client.post("/api/education/progress-reports/class/", payload, format="json")

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["count"], 2)
        reports = StudentProgressReport.objects.filter(class_report_id=response.data["class_report_id"])
        self.assertEqual(reports.count(), 2)
        self.assertEqual(set(reports.values_list("student_id", flat=True)), {self.student.pk, second_student.pk})
        first_report = reports.get(student=self.student)
        second_report = reports.get(student=second_student)
        self.assertEqual(first_report.status, StudentProgressReport.Status.SENT)
        class_history = self.client.get(
            f"/api/education/progress-reports/class/?offering={self.offering.pk}",
        )
        self.assertEqual(class_history.status_code, 200, class_history.data)
        self.assertEqual(len(self.rows(class_history)), 1)
        self.assertEqual(self.rows(class_history)[0]["recipient_count"], 2)
        self.assertEqual(self.rows(class_history)[0]["read_count"], 0)

        self.client.force_authenticate(self.learner)
        first_listing = self.client.get("/api/education/portal/progress-reports/")
        self.assertEqual(first_listing.status_code, 200)
        self.assertTrue(self.rows(first_listing)[0]["is_class_report"])
        first_receipt = self.client.post(
            f"/api/education/portal/progress-reports/{first_report.pk}/read/", {}, format="json",
        )
        self.assertEqual(first_receipt.status_code, 200)
        self.client.force_authenticate(self.teacher)
        updated_class_history = self.client.get(
            f"/api/education/progress-reports/class/?offering={self.offering.pk}",
        )
        self.assertEqual(self.rows(updated_class_history)[0]["read_count"], 1)

        self.client.force_authenticate(second_learner)
        second_listing = self.client.get("/api/education/portal/progress-reports/")
        self.assertEqual(second_listing.status_code, 200)
        self.assertIsNone(self.rows(second_listing)[0]["read_at"])
        self.assertEqual(self.rows(second_listing)[0]["id"], str(second_report.pk))

    def test_teacher_page_and_sidebar_are_available_and_student_page_is_denied(self):
        self.client.force_login(self.teacher)
        response = self.client.get("/workspace/teacher/progress-reports/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ذخیره پیش‌نویس")
        self.assertContains(response, "ارسال به دانش‌آموز")
        self.assertContains(response, 'href="/workspace/teacher/progress-reports/"')
        self.client.force_authenticate(self.learner)
        self.client.force_login(self.learner)
        self.assertEqual(self.client.get("/workspace/teacher/progress-reports/").status_code, 404)
        self.assertContains(self.client.get("/workspace/portal/"), "گزارش‌های مدرس")
