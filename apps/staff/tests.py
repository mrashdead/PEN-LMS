from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.forms.tests.factories import UserFactory
from apps.staff.models import ReviewHistory, ReviewStatus, TimesheetEntry
from apps.staff.services import clock_in, clock_out, review_timesheet


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
