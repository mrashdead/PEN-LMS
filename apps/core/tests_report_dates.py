import datetime as dt
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.test import SimpleTestCase, override_settings
from django.utils import timezone

from apps.core.report_dates import (
    ReportDateError, ReportRange, jalali_month_bounds, parse_report_date,
    preset_dates, project_today,
)


@override_settings(TIME_ZONE="Asia/Tehran", USE_TZ=True)
class ReportDateTests(SimpleTestCase):
    def test_today_uses_project_timezone_even_when_active_timezone_is_utc(self):
        with patch("django.utils.timezone.now", return_value=dt.datetime(2026, 10, 10, 21, tzinfo=dt.timezone.utc)), timezone.override("UTC"):
            self.assertEqual(project_today(), dt.date(2026, 10, 11))
            bounds = ReportRange.from_query({})
            self.assertEqual(bounds.start, dt.date(2026, 10, 11))
            self.assertEqual(bounds.start_at.astimezone(dt.timezone.utc), dt.datetime(2026, 10, 10, 20, 30, tzinfo=dt.timezone.utc))
            self.assertEqual(bounds.end_before - bounds.start_at, dt.timedelta(days=1))

    def test_jalali_and_iso_today_are_the_same_date(self):
        self.assertEqual(parse_report_date("۱۴۰۵/۰۷/۱۹"), dt.date(2026, 10, 11))
        self.assertEqual(parse_report_date("2026-10-11"), dt.date(2026, 10, 11))
        self.assertEqual(parse_report_date("١٤٠٥/٠٧/١٩"), dt.date(2026, 10, 11))

    def test_week_is_seven_inclusive_days_across_year_boundary(self):
        start, end = preset_dates("weekly", today=dt.date(2026, 3, 23))
        self.assertEqual(start, dt.date(2026, 3, 17))
        self.assertEqual(end, dt.date(2026, 3, 23))

    def test_mehr_and_current_month_clipping(self):
        self.assertEqual(jalali_month_bounds(1405, 7), (dt.date(2026, 9, 23), dt.date(2026, 10, 22)))
        self.assertEqual(preset_dates("monthly", today=dt.date(2026, 10, 11), year=1405, month=7), (dt.date(2026, 9, 23), dt.date(2026, 10, 11)))
        self.assertEqual(preset_dates("monthly", today=dt.date(2026, 11, 15), year=1405, month=7), jalali_month_bounds(1405, 7))

    def test_esfand_leap_year_and_short_last_week(self):
        self.assertEqual((jalali_month_bounds(1403, 12)[1] - jalali_month_bounds(1403, 12)[0]).days + 1, 30)
        self.assertEqual((jalali_month_bounds(1404, 12)[1] - jalali_month_bounds(1404, 12)[0]).days + 1, 29)
        self.assertEqual(preset_dates("month_week", today=dt.date(2026, 11, 15), year=1405, month=7, week=5), (dt.date(2026, 10, 21), dt.date(2026, 10, 22)))

    def test_manual_times_are_project_local_and_end_is_exclusive(self):
        with patch("django.utils.timezone.now", return_value=dt.datetime(2026, 11, 15, tzinfo=dt.timezone.utc)):
            bounds = ReportRange.from_query({"from": "۱۴۰۵/۰۷/۱۹", "to": "2026-10-11", "start_time": "۰۹:۳۰", "end_time": "۱۰:۳۰"})
        self.assertEqual(bounds.start_at, dt.datetime(2026, 10, 11, 9, 30, tzinfo=ZoneInfo("Asia/Tehran")))
        self.assertEqual(bounds.end_before - bounds.start_at, dt.timedelta(hours=1))

    def test_invalid_and_future_ranges_have_clear_errors(self):
        invalid = [
            ({"from": "1405/07/31", "to": "1405/07/31"}, "تاریخ شمسی"),
            ({"from": "2026-02-30", "to": "2026-03-01"}, "تاریخ شمسی"),
            ({"from": "2026-10-11"}, "با هم"),
            ({"from": "2026-10-11", "to": "2026-10-10"}, "بعد از شروع"),
            ({"from": "2026-10-11", "to": "2026-10-11", "start_time": "10:00", "end_time": "09:00"}, "بعد از شروع"),
            ({"from": "2026-10-12", "to": "2026-10-12"}, "آینده"),
            ({"from": "9999-12-31", "to": "9999-12-31"}, "آینده"),
            ({"from": "2026-10-11", "to": "2026-10-11", "end_time": "23:00"}, "آینده"),
            ({"period": "monthly", "year": "1405", "month": "13"}, "ماه شمسی"),
            ({"period": "month_week", "week": "6"}, "بین ۱ و ۵"),
            ({"from": "2026-10-10", "to": "2026-10-10", "end_time": "25:00"}, "ساعت"),
        ]
        with patch("django.utils.timezone.now", return_value=dt.datetime(2026, 10, 11, 8, tzinfo=dt.timezone.utc)):
            for query, message in invalid:
                with self.subTest(query=query), self.assertRaisesRegex(ReportDateError, message):
                    ReportRange.from_query(query)
