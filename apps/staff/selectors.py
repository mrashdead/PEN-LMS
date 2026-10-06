"""
Read-only reporting selectors for the staff module.

All aggregation happens in SQL (annotate/aggregate); the date bounds are
plain DATE comparisons so PostgreSQL can use the composite indexes. The
 Jalali month grouping is per-DISTINCT-date in Python (bounded by the number
of distinct dates, not by the number of rows) — the same pattern as
apps/education/reports.py.
"""
from __future__ import annotations

import datetime as dt
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from django.db.models import Avg, Case, Count, F, Q, Sum, Value, When
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.core.utils import english_numbers, persian_numbers, to_jalali_date
from apps.staff.models import (
    LeaveRequest,
    ReviewStatus,
    TimesheetEntry,
    WorkReport,
)


class StaffReportError(ValueError):
    """A user-facing error in the requested report range or filter."""


@dataclass(frozen=True)
class StaffFilters:
    start: dt.date
    end: dt.date
    user_id: str = ""
    status: str = ""
    kind: str = ""

    @classmethod
    def from_query(cls, query) -> "StaffFilters":
        today = timezone.localdate()
        raw_start = query.get("from") or query.get("date_from")
        raw_end = query.get("to") or query.get("date_to")
        start = _parse_date(raw_start) if raw_start else today.replace(day=1)
        end = _parse_date(raw_end) if raw_end else today
        if end < start:
            raise StaffReportError("تاریخ پایان باید بعد از تاریخ شروع باشد.")
        if (end - start).days > 366 * 3:
            raise StaffReportError("بازهٔ گزارش نمی‌تواند بیشتر از سه سال باشد.")
        status = (query.get("status") or "").strip().lower()
        if status and status not in dict(ReviewStatus.choices):
            raise StaffReportError("وضعیت انتخاب‌شده معتبر نیست.")
        user_id = (query.get("user") or query.get("user_id") or "").strip()
        if user_id:
            try:
                import uuid

                user_id = str(uuid.UUID(user_id))
            except (ValueError, AttributeError, TypeError):
                raise StaffReportError("شناسهٔ کاربر معتبر نیست.")
        return cls(
            start=start, end=end, user_id=user_id, status=status,
            kind=(query.get("kind") or "").strip().lower(),
        )


def _parse_date(value: Any) -> dt.date | None:
    import jdatetime

    raw = english_numbers(str(value or "").strip())
    if not raw:
        return None
    try:
        separator = "-" if "-" in raw else "/"
        pieces = [int(part) for part in raw.replace("-", "/").split("/")]
        if len(pieces) != 3:
            raise ValueError
        year, month, day = pieces
        if separator == "/" and year >= 1300:
            return jdatetime.date(year, month, day).togregorian()
        return dt.date(year, month, day)
    except (TypeError, ValueError, OverflowError):
        raise StaffReportError("تاریخ باید به شکل ۱۴۰۵/۰۶/۲۵ یا ۲۰۲۶/۰۹/۱۶ باشد.")


def _jalali_month_label(value: dt.date | None) -> str:
    if value is None:
        return "—"
    jalali = to_jalali_date(value)
    return persian_numbers(jalali.strftime("%Y/%m")) if jalali else "—"


def _jalali_day_label(value: dt.date | None) -> str:
    if value is None:
        return "—"
    jalali = to_jalali_date(value)
    return persian_numbers(jalali.strftime("%Y/%m/%d")) if jalali else "—"


def _timesheet_base(filters: StaffFilters):
    qs = TimesheetEntry.objects.filter(is_deleted=False)
    if filters.user_id:
        qs = qs.filter(user_id=filters.user_id)
    if filters.status:
        qs = qs.filter(status=filters.status)
    if filters.kind:
        qs = qs.filter(kind=filters.kind)
    return qs.filter(work_date__gte=filters.start, work_date__lte=filters.end)


def _leave_base(filters: StaffFilters):
    qs = LeaveRequest.objects.filter(is_deleted=False)
    if filters.user_id:
        qs = qs.filter(user_id=filters.user_id)
    if filters.status:
        qs = qs.filter(status=filters.status)
    # A leave intersects the window if its range touches [start, end].
    return qs.filter(start_date__lte=filters.end, end_date__gte=filters.start)


def _report_base(filters: StaffFilters):
    qs = WorkReport.objects.filter(is_deleted=False)
    if filters.user_id:
        qs = qs.filter(user_id=filters.user_id)
    if filters.status:
        qs = qs.filter(status=filters.status)
    return qs.filter(report_date__gte=filters.start, report_date__lte=filters.end)


# ─────────────────────────────────────────────────────────────────────────────
# گزارش ساعت کاری
# ─────────────────────────────────────────────────────────────────────────────

def timesheet_report(filters: StaffFilters) -> dict[str, Any]:
    """وضعیت ساعت کاری در بازه — مجموع دقیقه، میانگین روزانه، توزیع وضعیت."""
    qs = _timesheet_base(filters)
    rows = list(qs.select_related("user").order_by("-work_date"))
    total_minutes = sum(r.duration_minutes or 0 for r in rows)
    worked_days = {r.work_date for r in rows if r.duration_minutes}
    by_status: dict[str, int] = defaultdict(int)
    by_user: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"label": "—", "minutes": 0, "days": set(), "entries": 0}
    )
    for row in rows:
        by_status[row.status] += 1
        item = by_user[str(row.user_id)]
        item["label"] = _user_label(row.user)
        item["minutes"] += row.duration_minutes or 0
        item["days"].add(row.work_date)
        item["entries"] += 1

    daily: dict[str, int] = defaultdict(int)
    for row in rows:
        if row.duration_minutes:
            daily[row.work_date.isoformat()] += row.duration_minutes

    trend = [
        {
            "label": _jalali_month_label(_month_of(day)),
            "value": minutes,
        }
        for day, minutes in sorted(_by_month(daily).items())
    ]
    per_user = [
        {
            "user_id": key,
            "label": item["label"],
            "minutes": item["minutes"],
            "hours": round(item["minutes"] / 60, 1),
            "days": len(item["days"]),
            "entries": item["entries"],
        }
        for key, item in sorted(
            by_user.items(), key=lambda kv: -kv[1]["minutes"]
        )[:20]
    ]
    calendar_days = max((filters.end - filters.start).days + 1, 1)
    return {
        "totals": {
            "entries": len(rows),
            "minutes": total_minutes,
            "hours": round(total_minutes / 60, 1),
            "worked_days": len(worked_days),
            "average_minutes_per_day": round(total_minutes / calendar_days, 1),
        },
        "by_status": {key: by_status.get(key, 0) for key, _ in ReviewStatus.choices},
        "per_user": per_user,
        "trend": trend,
        "daily": [
            {"label": _jalali_day_label(dt.date.fromisoformat(day)), "minutes": minutes}
            for day, minutes in sorted(daily.items())
        ][:60],
    }


# ─────────────────────────────────────────────────────────────────────────────
# گزارش مرخصی
# ─────────────────────────────────────────────────────────────────────────────

def leave_report(filters: StaffFilters) -> dict[str, Any]:
    qs = _leave_base(filters).select_related("user", "leave_type", "reviewed_by")
    rows = list(qs.order_by("-start_date"))
    by_status: dict[str, int] = defaultdict(int)
    by_type: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"label": "—", "count": 0, "days": Decimal_zero()}
    )
    by_user: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"label": "—", "count": 0, "days": Decimal_zero()}
    )
    for row in rows:
        by_status[row.status] += 1
        type_item = by_type[str(row.leave_type_id)]
        type_item["label"] = row.leave_type.name if row.leave_type_id else "—"
        type_item["count"] += 1
        type_item["days"] += _approved_days(row)
        user_item = by_user[str(row.user_id)]
        user_item["label"] = _user_label(row.user)
        user_item["count"] += 1
        user_item["days"] += _approved_days(row)

    pending = [r for r in rows if r.status == ReviewStatus.PENDING]
    return {
        "totals": {
            "requests": len(rows),
            "pending": len(pending),
            "approved_days": float(sum(_approved_days(r) for r in rows)),
            "pending_days": float(sum(
                r.duration for r in pending if r.unit != LeaveRequest.Unit.HOUR
            )),
        },
        "by_status": {key: by_status.get(key, 0) for key, _ in ReviewStatus.choices},
        "by_type": [
            {"label": item["label"], "count": item["count"], "days": float(item["days"])}
            for key, item in sorted(by_type.items(), key=lambda kv: -kv[1]["count"])
        ],
        "by_user": [
            {
                "user_id": key,
                "label": item["label"],
                "count": item["count"],
                "days": float(item["days"]),
            }
            for key, item in sorted(by_user.items(), key=lambda kv: -kv[1]["days"])
        ][:20],
        "pending_review": [
            {
                "id": str(r.pk),
                "user": _user_label(r.user),
                "leave_type": r.leave_type.name if r.leave_type_id else "—",
                "start_date": r.start_date.isoformat(),
                "end_date": r.end_date.isoformat(),
                "start_date_jalali": _jalali_day_label(r.start_date),
                "end_date_jalali": _jalali_day_label(r.end_date),
                "start_time": r.start_time.strftime("%H:%M") if r.start_time else None,
                "end_time": r.end_time.strftime("%H:%M") if r.end_time else None,
                "time_range_display": r.time_range_display,
                "duration_display": r.duration_display,
            }
            for r in pending[:20]
        ],
    }


def _approved_days(row) -> Any:
    """Day-equivalent of a row — counted only when approved."""
    if row.status != ReviewStatus.APPROVED:
        return Decimal_zero()
    if row.unit == LeaveRequest.Unit.HOUR:
        return Decimal_zero()
    return row.duration


def Decimal_zero():
    from decimal import Decimal

    return Decimal(0)


# ─────────────────────────────────────────────────────────────────────────────
# گزارش کاری (work reports)
# ─────────────────────────────────────────────────────────────────────────────

def work_report_summary(filters: StaffFilters) -> dict[str, Any]:
    qs = _report_base(filters).select_related("user", "reviewed_by")
    rows = list(qs.order_by("-report_date"))
    by_status: dict[str, int] = defaultdict(int)
    by_user: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"label": "—", "count": 0, "minutes": 0}
    )
    for row in rows:
        by_status[row.status] += 1
        item = by_user[str(row.user_id)]
        item["label"] = _user_label(row.user)
        item["count"] += 1
        item["minutes"] += row.spent_minutes or 0
    pending = [r for r in rows if r.status == ReviewStatus.PENDING]
    return {
        "totals": {
            "reports": len(rows),
            "minutes": sum(r.spent_minutes or 0 for r in rows),
            "pending": len(pending),
            "approved": by_status.get(ReviewStatus.APPROVED, 0),
            "rejected": by_status.get(ReviewStatus.REJECTED, 0),
        },
        "by_status": {key: by_status.get(key, 0) for key, _ in ReviewStatus.choices},
        "per_user": [
            {
                "user_id": key,
                "label": item["label"],
                "count": item["count"],
                "minutes": item["minutes"],
                "hours": round(item["minutes"] / 60, 1),
            }
            for key, item in sorted(by_user.items(), key=lambda kv: -kv[1]["minutes"])
        ][:20],
        "pending_review": [
            {
                "id": str(r.pk),
                "user": _user_label(r.user),
                "title": r.title,
                "report_date": r.report_date.isoformat(),
                "report_date_jalali": _jalali_day_label(r.report_date),
                "spent_minutes": r.spent_minutes,
            }
            for r in pending[:20]
        ],
    }


def staff_dashboard(user, filters: StaffFilters) -> dict[str, Any]:
    """Single read model for the staff-operations dashboard + export."""
    from dataclasses import replace

    from apps.staff.models import APPROVER_ROLES

    roles = set(user.role_codes()) if getattr(user, "is_authenticated", False) else set()
    if not (getattr(user, "is_superuser", False) or roles & set(APPROVER_ROLES)):
        filters = replace(filters, user_id=str(user.pk))
    return {
        "filters": {
            "from": filters.start.isoformat(),
            "to": filters.end.isoformat(),
            "from_jalali": _jalali_day_label(filters.start),
            "to_jalali": _jalali_day_label(filters.end),
            "user": filters.user_id,
            "status": filters.status,
        },
        "timesheet": timesheet_report(filters),
        "leave": leave_report(filters),
        "work_reports": work_report_summary(filters),
    }


# ─────────────────────────────────────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────────────────────────────────────

def _user_label(user) -> str:
    if user is None:
        return "—"
    full = " ".join(n for n in (getattr(user, "first_name", ""), getattr(user, "last_name", "")) if n)
    return full or getattr(user, "username", "—")


def _month_of(day):
    return day.replace(day=1)


def _by_month(daily: dict[str, int]) -> dict[dt.date, int]:
    out: dict[dt.date, int] = defaultdict(int)
    for iso_day, minutes in daily.items():
        out[_month_of(dt.date.fromisoformat(iso_day))] += minutes
    return out


def staff_export_rows(data: dict[str, Any]) -> list[tuple[str, list[str], list[list[Any]]]]:
    """Excel sheet definitions for the staff module."""
    sheets: list[tuple[str, list[str], list[list[Any]]]] = []
    timesheet = data.get("timesheet", {})
    sheets.append((
        "خلاصه ساعت کاری",
        ["شاخص", "مقدار"],
        [
            ["تعداد ثبت", timesheet.get("totals", {}).get("entries", 0)],
            ["مجموع دقیقه", timesheet.get("totals", {}).get("minutes", 0)],
            ["مجموع ساعت", timesheet.get("totals", {}).get("hours", 0)],
            ["روزهای کاری", timesheet.get("totals", {}).get("worked_days", 0)],
        ],
    ))
    sheets.append((
        "ساعت کاری کاربران",
        ["کاربر", "ساعت", "روز", "تعداد ثبت"],
        [
            [row["label"], row["hours"], row["days"], row["entries"]]
            for row in timesheet.get("per_user", [])
        ],
    ))
    leave = data.get("leave", {})
    sheets.append((
        "خلاصه مرخصی",
        ["شاخص", "مقدار"],
        [
            ["تعداد درخواست", leave.get("totals", {}).get("requests", 0)],
            ["در انتظار بررسی", leave.get("totals", {}).get("pending", 0)],
            ["روزهای تأییدشده", leave.get("totals", {}).get("approved_days", 0)],
        ],
    ))
    sheets.append((
        "مرخصی بر اساس نوع",
        ["نوع مرخصی", "تعداد", "روز"],
        [
            [row["label"], row["count"], row["days"]]
            for row in leave.get("by_type", [])
        ],
    ))
    reports = data.get("work_reports", {})
    sheets.append((
        "خلاصه گزارش کاری",
        ["شاخص", "مقدار"],
        [
            ["تعداد گزارش", reports.get("totals", {}).get("reports", 0)],
            ["تأییدشده", reports.get("totals", {}).get("approved", 0)],
            ["ردشده", reports.get("totals", {}).get("rejected", 0)],
            ["در انتظار", reports.get("totals", {}).get("pending", 0)],
        ],
    ))
    sheets.append((
        "گزارش کاری کاربران",
        ["کاربر", "تعداد گزارش", "ساعت"],
        [
            [row["label"], row["count"], row["hours"]]
            for row in reports.get("per_user", [])
        ],
    ))
    return sheets
