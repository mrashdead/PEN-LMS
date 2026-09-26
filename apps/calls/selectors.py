"""
Read-only reporting selectors for the call log.

Aggregation is SQL-first; the follow-up overdueness is a boolean derived in
the query so the report never scans Python loops over large row sets.
"""
from __future__ import annotations

import datetime as dt
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from django.db.models import Count, Q, Sum
from django.utils import timezone

from apps.calls.models import CallResult, FollowUpStatus, InboundCall
from apps.core.utils import english_numbers, persian_numbers, to_jalali_date


class CallReportError(ValueError):
    """A user-facing error in the requested report range or filter."""


@dataclass(frozen=True)
class CallFilters:
    start: dt.date
    end: dt.date
    receiver_id: str = ""
    department: str = ""
    subject: str = ""
    result: str = ""
    follow_up_status: str = ""
    needs_follow_up: bool = False

    @classmethod
    def from_query(cls, query) -> "CallFilters":
        today = timezone.localtime().date()
        raw_start = query.get("from") or query.get("date_from")
        raw_end = query.get("to") or query.get("date_to")
        start = _parse_datetime(raw_start).date() if raw_start else today.replace(day=1)
        end = _parse_datetime(raw_end).date() if raw_end else today
        if end < start:
            raise CallReportError("تاریخ پایان باید بعد از تاریخ شروع باشد.")
        if (end - start).days > 366 * 3:
            raise CallReportError("بازهٔ گزارش نمی‌تواند بیشتر از سه سال باشد.")
        result = (query.get("result") or "").strip().lower()
        if result and result not in dict(CallResult.choices):
            raise CallReportError("نتیجهٔ تماس انتخاب‌شده معتبر نیست.")
        status = (query.get("follow_up_status") or "").strip().lower()
        if status and status not in dict(FollowUpStatus.choices):
            raise CallReportError("وضعیت پیگیری انتخاب‌شده معتبر نیست.")
        receiver_id = (query.get("receiver") or query.get("user") or "").strip()
        if receiver_id:
            try:
                import uuid

                receiver_id = str(uuid.UUID(receiver_id))
            except (ValueError, AttributeError, TypeError):
                raise CallReportError("شناسهٔ دریافت‌کننده معتبر نیست.")
        return cls(
            start=start, end=end, receiver_id=receiver_id,
            department=(query.get("department") or "").strip(),
            subject=(query.get("subject") or "").strip(),
            result=result,
            follow_up_status=status,
            needs_follow_up=(query.get("needs_follow_up") or "").strip().lower()
            in {"1", "true", "yes"},
        )


def _parse_datetime(value: Any):
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
        raise CallReportError("تاریخ باید به شکل ۱۴۰۵/۰۶/۲۵ یا ۲۰۲۶/۰۹/۱۶ باشد.")


def _jalali_month_label(value) -> str:
    if value is None:
        return "—"
    jalali = to_jalali_date(value)
    return persian_numbers(jalali.strftime("%Y/%m")) if jalali else "—"


def _jalali_day_label(value) -> str:
    if value is None:
        return "—"
    jalali = to_jalali_date(value)
    return persian_numbers(jalali.strftime("%Y/%m/%d")) if jalali else "—"


def _calls_base(filters: CallFilters, user):
    """Filter the call log — date bounds are the leading index columns."""
    from apps.calls.services import calls_visible_to

    qs = calls_visible_to(user).filter(is_deleted=False)
    start_dt = dt.datetime.combine(filters.start, dt.time.min, tzinfo=timezone.get_current_timezone())
    end_dt = dt.datetime.combine(filters.end, dt.time.max, tzinfo=timezone.get_current_timezone())
    qs = qs.filter(called_at__gte=start_dt, called_at__lte=end_dt)
    if filters.receiver_id:
        qs = qs.filter(Q(receiver_id=filters.receiver_id) | Q(assignee_id=filters.receiver_id))
    if filters.department:
        qs = qs.filter(Q(department__iexact=filters.department)
                       | Q(department_ref__name__iexact=filters.department))
    if filters.subject:
        qs = qs.filter(subject__icontains=filters.subject)
    if filters.result:
        qs = qs.filter(result=filters.result)
    if filters.follow_up_status:
        qs = qs.filter(follow_up_status=filters.follow_up_status)
    if filters.needs_follow_up:
        qs = qs.filter(follow_up_status__in=[FollowUpStatus.PENDING, FollowUpStatus.IN_PROGRESS])
    return qs


def calls_report(filters: CallFilters, *, user) -> dict[str, Any]:
    """KPI + breakdown read model for the call-log dashboard and export."""
    qs = _calls_base(filters, user)

    status_rows = qs.values("follow_up_status").annotate(total=Count("id"))
    by_status = {row["follow_up_status"]: row["total"] for row in status_rows}
    for code, _label in FollowUpStatus.choices:
        by_status.setdefault(code, 0)

    result_rows = qs.values("result").annotate(total=Count("id"))
    by_result = {row["result"]: row["total"] for row in result_rows}
    for code, _label in CallResult.choices:
        by_result.setdefault(code, 0)

    subject_rows = (
        qs.values("subject").annotate(total=Count("id")).order_by("-total")[:15]
    )
    subject_ref_rows = (
        qs.filter(subject_ref__isnull=False)
        .values("subject_ref__name").annotate(total=Count("id"))
        .order_by("-total")[:15]
    )
    receiver_rows = (
        qs.values("receiver_id", "receiver__first_name", "receiver__last_name", "receiver__username")
        .annotate(total=Count("id"))
        .order_by("-total")[:15]
    )
    department_rows = (
        qs.exclude(department="").values("department")
        .annotate(total=Count("id")).order_by("-total")[:15]
    )

    # Trend by Jalali month — grouped over DISTINCT dates, not rows.
    dates = qs.values_list("called_at", flat=True)
    month_counts: dict[dt.date, int] = defaultdict(int)
    day_counts: dict[dt.date, int] = defaultdict(int)
    for called_at in dates:
        local = timezone.localtime(called_at).date()
        month_counts[local.replace(day=1)] += 1
        day_counts[local] += 1

    total = sum(by_status.values())
    open_follow_ups = by_status.get(FollowUpStatus.PENDING, 0) + by_status.get(FollowUpStatus.IN_PROGRESS, 0)
    overdue = _overdue_count(qs)

    return {
        "totals": {
            "calls": total,
            "needs_follow_up": open_follow_ups,
            "overdue_follow_ups": overdue,
            "follow_up_done": by_status.get(FollowUpStatus.DONE, 0),
            "missed": by_status.get(FollowUpStatus.MISSED, 0),
        },
        "by_status": by_status,
        "by_result": by_result,
        "by_subject": [
            {"label": row["subject"] or "بدون موضوع", "value": row["total"]}
            for row in subject_rows
        ],
        "by_subject_ref": [
            {"label": row["subject_ref__name"], "value": row["total"]}
            for row in subject_ref_rows
        ],
        "by_receiver": [
            {
                "receiver_id": str(row["receiver_id"]),
                "label": _user_label(row),
                "value": row["total"],
            }
            for row in receiver_rows
        ],
        "by_department": [
            {"label": row["department"], "value": row["total"]}
            for row in department_rows
        ],
        "trend": [
            {"label": _jalali_month_label(month), "value": count}
            for month, count in sorted(month_counts.items())
        ],
        "daily": [
            {"label": _jalali_day_label(day), "value": count}
            for day, count in sorted(day_counts.items())
        ][:60],
    }


def _overdue_count(qs) -> int:
    now = timezone.now()
    return (
        qs.filter(
            follow_up_status__in=[FollowUpStatus.PENDING, FollowUpStatus.IN_PROGRESS],
            next_follow_up_at__lt=now,
        ).count()
    )


def _user_label(row: dict) -> str:
    first = row.get("receiver__first_name") or ""
    last = row.get("receiver__last_name") or ""
    full = " ".join(n for n in (first, last) if n)
    return full or row.get("receiver__username") or "—"


def calls_export_rows(data: dict[str, Any]) -> list[tuple[str, list[str], list[list[Any]]]]:
    sheets: list[tuple[str, list[str], list[list[Any]]]] = []
    totals = data.get("totals", {})
    sheets.append((
        "خلاصه تماس‌ها",
        ["شاخص", "مقدار"],
        [
            ["تعداد کل تماس", totals.get("calls", 0)],
            ["نیازمند پیگیری", totals.get("needs_follow_up", 0)],
            ["پیگیری سررسیدنشده", totals.get("overdue_follow_ups", 0)],
            ["پیگیری شد", totals.get("follow_up_done", 0)],
            ["تماس ناموفق مجدد", totals.get("missed", 0)],
        ],
    ))
    sheets.append((
        "بر اساس نتیجه",
        ["نتیجه", "تعداد"],
        [[key, value] for key, value in data.get("by_result", {}).items()],
    ))
    sheets.append((
        "بر اساس موضوع",
        ["موضوع", "تعداد"],
        [[row["label"], row["value"]] for row in data.get("by_subject", [])],
    ))
    sheets.append((
        "بر اساس دریافت‌کننده",
        ["دریافت‌کننده", "تعداد"],
        [[row["label"], row["value"]] for row in data.get("by_receiver", [])],
    ))
    return sheets
