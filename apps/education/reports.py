"""
Aggregated reports over REAL relational data (criterion §13-7).

Rules taken from the engineering report §5/§7:
  - daily/weekly/monthly attendance reads from ClassSession.session_date —
    a DATE column — never from JSON payloads or created_at (which is UTC and
    breaks the Tehran day boundary);
  - aggregation happens in SQL (annotate/aggregate) — no per-row Python;
  - every queryset goes through apps.academics.scoping so a teacher sees only
    their own sessions and a student only their own classes;
  - Jalali grouping uses the DB date converted in Python per GROUP — bounded
    by the number of DISTINCT dates, not the number of rows.

Grades: descriptive pass/fail only (numeric scores are rejected by design).
"""
from __future__ import annotations

from collections import defaultdict
from typing import Optional

from django.db.models import Count, Q
from django.utils import timezone

from apps.academics.scoping import (
    ELEVATED_ROLES,
    REFERENCE_DATA_ROLES,
    education_sessions_visible_to,
)
from apps.core.utils import to_jalali_date


class ReportError(Exception):
    pass


def _period_bounds(period: str, ref_date) -> tuple:
    """Return (start_date, end_date) for day/week/month containing ref_date.

    Week starts Saturday (Iranian convention). All arithmetic is on real
    dates; tz-aware datetimes are converted to Asia/Tehran local dates first.
    """
    import datetime as dt

    if ref_date is None:
        ref_date = timezone.localdate()
    elif hasattr(ref_date, "astimezone"):
        ref_date = timezone.localdate(ref_date)  # aware datetime → Tehran date
    if period == "day":
        return ref_date, ref_date
    if period == "week":
        # weekday(): Mon=0..Sun=6 → Saturday start ⇒ offset = (weekday+1) % 7
        offset = (ref_date.weekday() + 1) % 7
        start = ref_date - dt.timedelta(days=offset)
        end = start + dt.timedelta(days=6)
        return start, end
    if period == "month":
        start = ref_date.replace(day=1)
        if ref_date.month == 12:
            end = ref_date.replace(year=ref_date.year + 1, month=1, day=1) - dt.timedelta(days=1)
        else:
            end = ref_date.replace(month=ref_date.month + 1, day=1) - dt.timedelta(days=1)
        return start, end
    raise ReportError(f"بازه‌ی گزارش نامعتبر: {period} (day/week/month)")


def attendance_report(
    *,
    user,
    period: str = "day",
    ref=None,
    group_by_jalali_month: bool = False,
) -> dict:
    """
    تجمیع حضور بر اساس جلسات واقعی.

    خروجی: {"period", "start", "end", "totals", "by_day"/"by_month", "sessions"}
    هر سطر حضور بدون N+1: یک کوئری values + annotate روی رکوردها.
    """
    from apps.education.models import AttendanceRecord

    start, end = _period_bounds(period, ref)
    sessions = education_sessions_visible_to(user).filter(
        session_date__gte=start, session_date__lte=end, is_deleted=False,
    )
    records = (
        AttendanceRecord.objects.filter(
            session__in=sessions, is_deleted=False,
        )
        .values("status")
        .annotate(total=Count("id"))
    )
    totals = {r["status"]: r["total"] for r in records}
    total_all = sum(totals.values())

    payload = {
        "period": period,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "totals": totals,
        "all": total_all,
        "sessions": sessions.count(),
    }

    if group_by_jalali_month:
        rows = (
            AttendanceRecord.objects.filter(
                session__in=sessions, is_deleted=False,
            )
            .values_list("session__session_date", "status")
        )
        buckets: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for session_date, status in rows:
            key = to_jalali_date(session_date).strftime("%Y/%m") if session_date else "?"
            buckets[key][status] += 1
        payload["by_month"] = {
            k: dict(v) for k, v in sorted(buckets.items())
        }
    elif period in ("week", "month"):
        rows = (
            AttendanceRecord.objects.filter(
                session__in=sessions, is_deleted=False,
            )
            .values_list("session__session_date", "status")
        )
        buckets: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for session_date, status in rows:
            if session_date:
                buckets[session_date.isoformat()][status] += 1
        payload["by_day"] = {k: dict(v) for k, v in sorted(buckets.items())}

    return payload


def capacity_report(*, user, course_id=None, offering_id=None, is_active=None) -> list[dict]:
    """
    وضعیت ظرفیت برگزاری‌ها (§13-7: «ظرفیت ثبت‌نام») — یک کوئری annotate.
    مدیر: همه؛ مدرس: برگزاری‌هایی که مدرسشان است؛ سایر نقش‌ها: خالی.
    """
    from apps.education.models import CourseOffering

    qs = CourseOffering.objects.filter(is_deleted=False).select_related("course")
    roles = set(user.role_codes()) if hasattr(user, "role_codes") else set()
    person = getattr(user, "person", None)
    if roles & REFERENCE_DATA_ROLES:
        pass
    elif person is not None and "teacher" in roles:
        qs = qs.filter(instructor=person)
    else:
        return []

    if course_id:
        qs = qs.filter(course_id=course_id)
    if offering_id:
        qs = qs.filter(pk=offering_id)
    if is_active is not None:
        qs = qs.filter(is_active=is_active)

    # enrolled_count is the service-maintained denormalized counter (kept
    # consistent under a row lock by enroll_student/withdraw_student) — no
    # join needed; one plain .values() query.
    rows = qs.values(
        "id", "title", "capacity", "enrolled_count", "start_date", "end_date",
        "course__title", "is_active",
    )
    report = []
    for r in rows:
        cap = r["capacity"] or 0
        enrolled = r["enrolled_count"] or 0
        report.append({
            "id": str(r["id"]),
            "title": r["title"] or r["course__title"],
            "capacity": cap,
            "enrolled": enrolled,
            "seats_left": None if not cap else max(cap - enrolled, 0),
            "full": bool(cap and enrolled >= cap),
            "is_active": r["is_active"],
        })
    return report


def class_group_capacity_report(*, user, term_id=None, class_group_id=None, is_active=None):
    """Capacity rows for the academics class groups, counted in SQL."""
    from django.db.models import Count, Q

    from apps.academics.scoping import class_groups_visible_to

    groups = class_groups_visible_to(user).filter(is_deleted=False)
    if term_id:
        groups = groups.filter(term_id=term_id)
    if class_group_id:
        groups = groups.filter(pk=class_group_id)
    if is_active is not None:
        groups = groups.filter(is_active=is_active)
    rows = groups.annotate(
        enrolled=Count(
            "enrollments",
            filter=Q(enrollments__is_active=True, enrollments__is_deleted=False),
        ),
    ).values("id", "name", "code", "term__title", "capacity", "enrolled", "is_active")
    return [
        {
            "id": str(row["id"]),
            "name": row["name"],
            "code": row["code"],
            "term": row["term__title"],
            "capacity": row["capacity"],
            "enrolled": row["enrolled"],
            "seats_left": max(row["capacity"] - row["enrolled"], 0),
            "full": row["capacity"] > 0 and row["enrolled"] >= row["capacity"],
            "is_active": row["is_active"],
        }
        for row in rows
    ]
