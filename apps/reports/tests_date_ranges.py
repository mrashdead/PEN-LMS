import datetime as dt
from io import BytesIO
from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.core.report_dates import ReportRange
from apps.education.models import Course, CourseOffering, ClassSession, OfferingEnrollment
from apps.education.reports import attendance_report
from apps.forms.tests.factories import UserFactory, make_person
from apps.reports.selectors.reports import ReportFilters, financial_report, _report_sessions


@override_settings(TIME_ZONE="Asia/Tehran")
class ReportDataRangeTests(TestCase):
    def setUp(self):
        self.manager = UserFactory(username="range-manager", roles=["manager"])
        self.offering = CourseOffering.objects.create(course=Course.objects.create(code="range-course", title="آزمون"))

    def session(self, day, hour="09:00"):
        return ClassSession.objects.create(offering=self.offering, session_number=self.offering.sessions.count() + 1, session_date=day, start_time=hour, end_time="12:00")

    @patch("django.utils.timezone.now", return_value=dt.datetime(2026, 11, 15, 10, tzinfo=dt.timezone.utc))
    def test_mehr_filters_calendar_data_and_groups_one_jalali_month(self, _now):
        for day in (dt.date(2026, 9, 22), dt.date(2026, 9, 23), dt.date(2026, 10, 22), dt.date(2026, 10, 23)):
            OfferingEnrollment.objects.create(offering=self.offering, student=make_person(), enrolled_at=day, final_amount=100)
        filters = ReportFilters.from_query({"period": "monthly", "year": "1405", "month": "7"})
        report = financial_report(self.manager, filters)
        self.assertEqual(report["totals"]["registrations"], 2)
        self.assertEqual(report["totals"]["revenue"], 200)
        self.assertEqual(report["revenue_trend"], [{"label": "۱۴۰۵/۰۷", "value": 200}])
        client = APIClient()
        client.force_authenticate(self.manager)
        response = client.get("/api/reports/dashboard/", {"period": "monthly", "year": "1405", "month": "7"})
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["filters"]["from"], "2026-09-23")
        self.assertEqual(response.data["filters"]["to"], "2026-10-22")
        self.assertEqual(response.data["financial"]["totals"]["revenue"], 200)
        response = client.get("/api/reports/export/", {"period": "monthly", "year": "1405", "month": "7", "report": "financial"})
        self.assertEqual(response.status_code, 200)
        from openpyxl import load_workbook
        workbook = load_workbook(BytesIO(response.content))
        metadata = dict(workbook["بازه گزارش"].values)
        self.assertEqual(metadata["از تاریخ شمسی"], "۱۴۰۵/۰۷/۰۱")
        self.assertEqual(metadata["تا تاریخ شمسی"], "۱۴۰۵/۰۷/۳۰")
        self.assertEqual(metadata["منطقه زمانی"], "Asia/Tehran")

    @patch("django.utils.timezone.now", return_value=dt.datetime(2026, 10, 11, 10, tzinfo=dt.timezone.utc))
    def test_weekly_data_excludes_eighth_day_and_tomorrow(self, _now):
        for day in range(4, 13):
            self.session(dt.date(2026, 10, day))
        filters = ReportFilters.from_query({"period": "weekly"})
        self.assertEqual(_report_sessions(filters).count(), 7)
        data = attendance_report(user=self.manager, period="week")
        self.assertEqual(data["start"], "2026-10-05")
        self.assertEqual(data["end"], "2026-10-11")
        self.assertEqual(data["sessions"], 7)

    @patch("django.utils.timezone.now", return_value=dt.datetime(2026, 10, 11, 10, tzinfo=dt.timezone.utc))
    def test_manual_time_filters_sessions_and_api_rejects_future(self, _now):
        for hour in ("08:00", "09:00", "10:00"):
            self.session(dt.date(2026, 10, 10), hour)
        query = {"from": "1405/07/18", "to": "1405/07/18", "start_time": "09:00", "end_time": "10:00"}
        filters = ReportFilters.from_query(query)
        self.assertEqual(_report_sessions(filters).count(), 1)
        self.assertEqual(attendance_report(user=self.manager, bounds=ReportRange.from_query(query))["sessions"], 1)
        client = APIClient()
        client.force_authenticate(self.manager)
        result = client.get("/api/reports/dashboard/", {"from": "2026-10-12", "to": "2026-10-12"})
        self.assertEqual(result.status_code, 400)
        self.assertIn("آینده", result.data["detail"])
        result = client.get("/api/education/reports/attendance/", query)
        self.assertEqual(result.status_code, 200, result.data)
        self.assertEqual(result.data["sessions"], 1)
