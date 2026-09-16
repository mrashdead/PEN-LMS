from __future__ import annotations

from datetime import date
from types import SimpleNamespace

from django.core.exceptions import PermissionDenied
from django.test import SimpleTestCase
from django.test import RequestFactory
from django.utils import timezone

from apps.reports.permissions import CanAccessReports, can_access_reports, can_view_financial_reports
from apps.reports.selectors.reports import ReportFilterError, ReportFilters
from apps.reports.views.reports import ReportsPage


class ReportFiltersTests(SimpleTestCase):
    def test_jalali_dates_are_normalized_to_gregorian(self):
        filters = ReportFilters.from_query({"from": "۱۴۰۵/۰۶/۰۱", "to": "۱۴۰۵/۰۶/۳۱"})

        self.assertEqual(filters.start, date(2026, 8, 23))
        self.assertEqual(filters.end, date(2026, 9, 22))
        self.assertEqual(filters.period, "custom")

    def test_explicit_iso_dates_are_custom(self):
        filters = ReportFilters.from_query({"from": "2026-09-01", "to": "2026-09-16"})

        self.assertEqual(filters.period, "custom")
        self.assertEqual(filters.as_dict()["from_jalali"], "۱۴۰۵/۰۶/۱۰")

    def test_quarter_period_uses_current_quarter(self):
        filters = ReportFilters.from_query({"period": "quarter"})

        self.assertEqual(filters.start.month, 7)
        self.assertEqual(filters.start.day, 1)
        self.assertEqual(filters.end, timezone.localdate())

    def test_invalid_range_is_rejected(self):
        with self.assertRaises(ReportFilterError):
            ReportFilters.from_query({"from": "2026-09-17", "to": "2026-09-16"})


class ReportPermissionTests(SimpleTestCase):
    def _user(self, *roles):
        return SimpleNamespace(
            is_authenticated=True,
            is_active=True,
            is_deleted=False,
            role_codes=lambda: set(roles),
        )

    def test_teacher_and_student_are_not_report_users(self):
        self.assertFalse(can_access_reports(self._user("teacher")))
        self.assertFalse(can_access_reports(self._user("student")))

    def test_supervisor_can_view_operational_reports_but_not_financial(self):
        supervisor = self._user("supervisor")

        self.assertTrue(can_access_reports(supervisor))
        self.assertFalse(can_view_financial_reports(supervisor))

    def test_manager_can_view_financial_reports(self):
        self.assertTrue(can_view_financial_reports(self._user("manager")))

    def test_permission_class_returns_false_for_inactive_user(self):
        request = SimpleNamespace(user=self._user("manager"))
        request.user.is_active = False

        self.assertFalse(CanAccessReports().has_permission(request, None))

    def test_teacher_gets_forbidden_on_server_rendered_page(self):
        request = RequestFactory().get("/workspace/reports/")
        request.user = self._user("teacher")

        with self.assertRaises(PermissionDenied):
            ReportsPage.as_view()(request)
