"""Report calendar contracts: Jalali input, Gregorian storage, project timezone."""
import datetime as dt
from dataclasses import dataclass

import jdatetime
from django.utils import timezone

from apps.core.utils import english_numbers


class ReportDateError(ValueError):
    pass


def project_today():
    return timezone.localdate(timezone=timezone.get_default_timezone())


def parse_report_date(value):
    if isinstance(value, dt.date) and not isinstance(value, dt.datetime):
        return value
    raw = english_numbers(str(value or "").strip())
    try:
        year, month, day = map(int, raw.replace("-", "/").split("/"))
        # Existing APIs send Gregorian ISO; visible inputs use Jalali years.
        if 1300 <= year <= 1600:
            return jdatetime.date(year, month, day).togregorian()
        if "-" in raw and year >= 1700:
            return dt.date(year, month, day)
    except (ValueError, TypeError, OverflowError):
        pass
    raise ReportDateError("تاریخ شمسی را مانند ۱۴۰۵/۰۷/۰۱ یا تاریخ میلادی را مانند 2026-09-23 وارد کنید.")


def jalali_month_bounds(year, month):
    try:
        year, month = int(english_numbers(str(year))), int(english_numbers(str(month)))
        first = jdatetime.date(year, month, 1)
        following = jdatetime.date(year + (month == 12), 1 if month == 12 else month + 1, 1)
        return first.togregorian(), following.togregorian() - dt.timedelta(days=1)
    except (ValueError, TypeError, OverflowError):
        raise ReportDateError("سال یا ماه شمسی معتبر نیست.")


def preset_dates(period, *, today=None, year=None, month=None, week=None):
    today = today or project_today()
    period = {"day": "daily", "week": "weekly", "month": "monthly"}.get(period, period)
    if period == "daily":
        return today, today
    if period == "weekly":
        return today - dt.timedelta(days=6), today
    jalali = jdatetime.date.fromgregorian(date=today)
    year = year or jalali.year
    month = month or jalali.month
    if period in {"monthly", "month_week", "quarter", "year"}:
        if period == "quarter":
            month = ((jalali.month - 1) // 3) * 3 + 1
        if period == "year":
            month = 1
        start, end = jalali_month_bounds(year, month)
        if period == "month_week":
            try:
                week = int(english_numbers(str(week)))
                if not 1 <= week <= 5:
                    raise ValueError
            except (ValueError, TypeError):
                raise ReportDateError("هفتهٔ ماه باید عددی بین ۱ و ۵ باشد.")
            start += dt.timedelta(days=(week - 1) * 7)
            if start > end:
                raise ReportDateError("این ماه هفتهٔ انتخاب‌شده را ندارد.")
            end = min(end, start + dt.timedelta(days=6))
        elif period in {"quarter", "year"}:
            _, end = jalali_month_bounds(year, month + 2 if period == "quarter" else 12)
        if start > today:
            raise ReportDateError("بازهٔ گزارش نمی‌تواند از آینده شروع شود.")
        return start, min(end, today)
    raise ReportDateError("بازهٔ زمانی انتخاب‌شده معتبر نیست.")


def parse_report_time(value):
    if not value:
        return None
    if isinstance(value, dt.time):
        return value
    try:
        result = dt.time.fromisoformat(english_numbers(str(value).strip()))
        if result.tzinfo is not None:
            raise ValueError
        return result
    except (ValueError, TypeError):
        raise ReportDateError("ساعت را به شکل ۱۴:۳۰ وارد کنید.")


@dataclass(frozen=True)
class ReportRange:
    start: dt.date
    end: dt.date
    start_time: dt.time | None = None
    end_time: dt.time | None = None

    @property
    def start_at(self):
        return timezone.make_aware(dt.datetime.combine(self.start, self.start_time or dt.time.min), timezone.get_default_timezone())

    @property
    def end_before(self):
        # Date-only end includes the whole local day; a specified clock time
        # is the exclusive upper bound, shared by filtering and exports.
        end = dt.datetime.combine(self.end, self.end_time) if self.end_time else dt.datetime.combine(self.end + dt.timedelta(days=1), dt.time.min)
        return timezone.make_aware(end, timezone.get_default_timezone())

    def validate(self):
        if self.end < self.start:
            raise ReportDateError("تاریخ و ساعت پایان باید بعد از شروع باشد.")
        if (self.end - self.start).days > 366 * 5:
            raise ReportDateError("بازهٔ گزارش نمی‌تواند بیشتر از پنج سال باشد.")
        if self.start > project_today() or self.end > project_today():
            raise ReportDateError("تاریخ گزارش نمی‌تواند در آینده باشد.")
        if self.end_before <= self.start_at:
            raise ReportDateError("تاریخ و ساعت پایان باید بعد از شروع باشد.")
        if (self.start_time and self.start_at > timezone.now()) or (self.end_time and self.end_before > timezone.now()):
            raise ReportDateError("ساعت گزارش نمی‌تواند در آینده باشد.")
        return self

    @classmethod
    def from_query(cls, query, default="daily"):
        raw_start = query.get("from") or query.get("date_from")
        raw_end = query.get("to") or query.get("date_to")
        if bool(raw_start) != bool(raw_end):
            raise ReportDateError("تاریخ شروع و پایان را با هم وارد کنید.")
        if raw_start:
            start, end = parse_report_date(raw_start), parse_report_date(raw_end)
        else:
            if query.get("start_time") or query.get("end_time"):
                raise ReportDateError("برای انتخاب ساعت، تاریخ شروع و پایان را وارد کنید.")
            start, end = preset_dates((query.get("period") or default).strip().lower(), year=query.get("year"), month=query.get("month"), week=query.get("week"))
        return cls(start, end, parse_report_time(query.get("start_time")), parse_report_time(query.get("end_time"))).validate()
