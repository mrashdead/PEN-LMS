from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.core.utils import to_jalali_date
from apps.forms.tests.factories import UserFactory, make_person
from apps.staff.models import LeaveRequest, LeaveType, ReviewHistory, ReviewStatus, TimesheetEntry, WorkReport
from apps.staff.services import clock_in, clock_out, review_timesheet


class TeacherLeaveRequestTests(TestCase):
    def test_teacher_can_create_read_and_cancel_leave_request(self):
        teacher = UserFactory(username="teacher-leave-user", roles=["teacher"])
        person = make_person(user=teacher, person_type="teacher")
        leave_type = LeaveType.objects.create(code="annual", name="استحقاقی")
        work_date = timezone.localdate() + timedelta(days=1)
        jalali_date = to_jalali_date(work_date).strftime("%Y/%m/%d")
        self.client.force_login(teacher)

        response = self.client.post("/api/staff/leave-requests/", {
            "leave_type": str(leave_type.pk),
            "start_date": jalali_date,
            "end_date": jalali_date,
            "unit": LeaveRequest.Unit.DAY,
        })

        self.assertEqual(response.status_code, 201)
        record = LeaveRequest.objects.get(pk=response.json()["id"])
        self.assertEqual(LeaveRequest.objects.filter(user=teacher).count(), 1)
        self.assertEqual(record.user, teacher)
        self.assertEqual(record.person, person)
        self.assertEqual(record.start_date, work_date)
        self.assertEqual(record.duration, 1)
        self.assertEqual(response.json()["status"], ReviewStatus.PENDING)
        self.assertEqual(response.json()["status_display"], record.get_status_display())

        listing = self.client.get("/api/staff/leave-requests/")
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.json()[0]["id"], str(record.pk))
        detail = self.client.get(f"/api/staff/leave-requests/{record.pk}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["status_display"], record.get_status_display())

        cancelled = self.client.post(f"/api/staff/leave-requests/{record.pk}/cancel/")
        self.assertEqual(cancelled.status_code, 200)
        record.refresh_from_db()
        self.assertEqual(record.status, ReviewStatus.CANCELLED)
        self.assertEqual(cancelled.json()["status_display"], record.get_status_display())

    def test_teacher_can_create_work_report_with_status_display(self):
        teacher = UserFactory(username="teacher-work-report-user", roles=["teacher"])
        self.client.force_login(teacher)

        response = self.client.post("/api/staff/work-reports/", {"title": "گزارش تدریس"})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], ReviewStatus.PENDING)
        self.assertEqual(response.json()["status_display"], ReviewStatus.PENDING.label)


class WorkReportDetailsTests(TestCase):
    def test_reviewer_can_read_complete_teacher_report(self):
        teacher = UserFactory(username="report-details-teacher", roles=["teacher"])
        manager = UserFactory(username="report-details-manager", roles=["manager"])
        description = "توضیحات کامل فعالیت\n" + "شرح تدریس و تمرین‌های انجام‌شده. " * 100
        report = WorkReport.objects.create(
            user=teacher, report_date=timezone.localdate(),
            title="گزارش تدریس", description=description, spent_minutes=90,
        )
        self.client.force_login(manager)

        listing = self.client.get("/api/staff/work-reports/")
        self.assertEqual(listing.status_code, 200)
        rows = listing.json()
        rows = rows if isinstance(rows, list) else rows["results"]
        self.assertEqual(rows[0]["description"], description)
        detail = self.client.get(f"/api/staff/work-reports/{report.pk}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["description"], description)
        self.assertEqual(detail.json()["status"], ReviewStatus.PENDING)

        coworker = UserFactory(username="report-details-coworker", roles=["teacher"])
        self.client.force_login(coworker)
        self.assertEqual(
            self.client.get(f"/api/staff/work-reports/{report.pk}/").status_code, 404,
        )


class TimesheetWorkflowTests(TestCase):
    def test_clocking_and_review_preserve_audit_history(self):
        employee = UserFactory(username="staff-clock-user", roles=["employee"])
        reviewer = UserFactory(username="staff-clock-reviewer", roles=["manager"])
        work_date = timezone.localdate()

        entry = clock_in(user=employee, work_date=work_date)
        clock_out(user=employee, work_date=work_date)
        entry.refresh_from_db()

        self.assertIsNotNone(entry.check_out)
        self.assertGreaterEqual(entry.duration_minutes, 0)
        self.assertEqual(entry.status, ReviewStatus.PENDING)

        reviewed = review_timesheet(
            entry_id=entry.pk, actor=reviewer, decision=ReviewStatus.APPROVED,
        )
        self.assertEqual(reviewed.status, ReviewStatus.APPROVED)
        self.assertTrue(ReviewHistory.objects.filter(
            record_type=ReviewHistory.RecordType.TIMESHEET,
            record_id=entry.pk,
            to_status=ReviewStatus.APPROVED,
            actor=reviewer,
        ).exists())

    def test_rejection_requires_reason(self):
        employee = UserFactory(username="staff-reject-user", roles=["employee"])
        reviewer = UserFactory(username="staff-reject-manager", roles=["manager"])
        entry = TimesheetEntry.objects.create(
            user=employee,
            work_date=timezone.localdate(),
            check_in=timezone.now() - timedelta(hours=1),
        )
        from apps.staff.services import InvalidReviewError

        with self.assertRaises(InvalidReviewError):
            review_timesheet(
                entry_id=entry.pk, actor=reviewer, decision=ReviewStatus.REJECTED,
            )

    def test_staff_workspace_renders_and_timesheet_list_is_paginated(self):
        employee = UserFactory(username="staff-pagination-user", roles=["employee"])
        today = timezone.localdate()
        for offset in range(25):
            work_date = today - timedelta(days=offset)
            TimesheetEntry.objects.create(
                user=employee,
                work_date=work_date,
                check_in=timezone.now() - timedelta(days=offset, hours=8),
                check_out=timezone.now() - timedelta(days=offset),
            )
        self.client.force_login(employee)

        page = self.client.get("/api/staff/timesheets/")
        workspace = self.client.get("/workspace/staff/")

        self.assertEqual(page.status_code, 200)
        self.assertEqual(len(page.json()["results"]), 20)
        self.assertIsNotNone(page.json()["next"])
        self.assertEqual(workspace.status_code, 200)
        self.assertContains(workspace, "درخواست مرخصی")

    def test_staff_report_is_limited_to_the_requesting_employee(self):
        employee = UserFactory(username="staff-report-owner", roles=["employee"])
        coworker = UserFactory(username="staff-report-coworker", roles=["employee"])
        today = timezone.localdate()
        for user in (employee, coworker):
            TimesheetEntry.objects.create(
                user=user,
                work_date=today,
                check_in=timezone.now() - timedelta(hours=2),
                check_out=timezone.now() - timedelta(hours=1),
            )
        self.client.force_login(employee)

        response = self.client.get("/api/staff/reports/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["timesheet"]["totals"]["entries"], 1)
