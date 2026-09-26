"""Read-only selectors for the Pen LMS reporting centre.

The module is intentionally independent from HTTP. Every expensive read is
kept here, grouped in SQL where the schema allows it, and returned as plain
JSON-safe dictionaries for both the dashboard and the Excel exporter.

The current education schema stores a registration's financial snapshot on
``OfferingEnrollment``. Cash/POS rows are therefore considered settled;
cheque rows are shown as outstanding. This is explicit in the response so a
future payment-ledger model can replace the rule without changing the UI.
"""
from __future__ import annotations

import datetime as dt
import uuid
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

import jdatetime
from django.db.models import (
    Avg,
    Case,
    CharField,
    Count,
    F,
    FloatField,
    OuterRef,
    Q,
    Subquery,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Coalesce, TruncMonth
from django.utils import timezone

from apps.core.utils import english_numbers, jalali_date_str, persian_numbers, to_jalali_date
from apps.reports.permissions import can_view_financial_reports


REPORT_DAILY_OPEN_MINUTES = 8 * 60


class ReportFilterError(ValueError):
    """A user-facing error in the requested report range or filter."""


def _clean_uuid(value: Any) -> str:
    value = str(value or "").strip()
    if not value:
        return ""
    try:
        return str(uuid.UUID(value))
    except (ValueError, AttributeError, TypeError):
        raise ReportFilterError("شناسهٔ یکی از فیلترها معتبر نیست.")


def _parse_report_date(value: Any) -> dt.date | None:
    """Accept a Jalali date from the UI or an ISO Gregorian date."""
    raw = english_numbers(str(value or "").strip())
    if not raw:
        return None
    try:
        separator = "-" if "-" in raw else "/"
        pieces = [int(part) for part in raw.replace("-", "/").split("/")]
        if len(pieces) != 3:
            raise ValueError
        year, month, day = pieces
        # The UI uses slashes for Jalali and ISO hyphens for Gregorian. This
        # avoids the otherwise ambiguous 1405/2026 range of four-digit years.
        if separator == "/" and year >= 1300:
            return jdatetime.date(year, month, day).togregorian()
        return dt.date(year, month, day)
    except (TypeError, ValueError, OverflowError):
        raise ReportFilterError("تاریخ باید به شکل ۱۴۰۵/۰۶/۲۵ یا ۲۰۲۶/۰۹/۱۶ باشد.")


def _jalali_month_label(value: dt.date | None) -> str:
    if value is None:
        return "—"
    jalali = to_jalali_date(value)
    return persian_numbers(jalali.strftime("%Y/%m")) if jalali else "—"


def _jalali_day_label(value: dt.date | None) -> str:
    return persian_numbers(jalali_date_str(value)) if value else "—"


@dataclass(frozen=True)
class ReportFilters:
    """Normalized report filters shared by every selector."""

    start: dt.date
    end: dt.date
    department_id: str = ""
    course_id: str = ""
    location_id: str = ""
    period: str = "custom"

    @classmethod
    def from_query(cls, query) -> "ReportFilters":
        today = timezone.localdate()
        requested_period = (query.get("period") or "").strip().lower()
        if requested_period not in {"", "month", "quarter", "year", "custom"}:
            raise ReportFilterError("بازهٔ زمانی انتخاب‌شده معتبر نیست.")
        raw_start = query.get("from") or query.get("date_from")
        raw_end = query.get("to") or query.get("date_to")
        period = requested_period or ("custom" if raw_start or raw_end else "month")
        if not raw_start and not raw_end and period in {"month", "quarter", "year"}:
            if period == "month":
                start = today.replace(day=1)
                end = today
            elif period == "quarter":
                start_month = ((today.month - 1) // 3) * 3 + 1
                start = today.replace(month=start_month, day=1)
                end = today
            else:
                start = today.replace(month=1, day=1)
                end = today
        else:
            start = _parse_report_date(raw_start) if raw_start else today.replace(day=1)
            end = _parse_report_date(raw_end) if raw_end else today
        if end < start:
            raise ReportFilterError("تاریخ پایان باید بعد از تاریخ شروع باشد.")
        if (end - start).days > 366 * 5:
            raise ReportFilterError("بازهٔ گزارش نمی‌تواند بیشتر از پنج سال باشد.")
        return cls(
            start=start,
            end=end,
            department_id=_clean_uuid(query.get("department") or query.get("department_id")),
            course_id=_clean_uuid(query.get("course") or query.get("course_id")),
            location_id=_clean_uuid(query.get("location") or query.get("location_id")),
            period=period,
        )

    def as_dict(self) -> dict[str, str]:
        return {
            "from": self.start.isoformat(),
            "to": self.end.isoformat(),
            "from_jalali": _jalali_day_label(self.start),
            "to_jalali": _jalali_day_label(self.end),
            "department": self.department_id,
            "course": self.course_id,
            "location": self.location_id,
            "period": self.period,
        }


def _money(value: Any) -> int:
    if value in (None, ""):
        return 0
    if isinstance(value, str):
        value = value.replace(",", "").replace("٬", "").strip()
    return int(value)


def _pct(numerator: Any, denominator: Any) -> float:
    if not denominator:
        return 0.0
    return round(float(numerator or 0) * 100 / float(denominator), 1)


def _duration_minutes(start: dt.time | None, end: dt.time | None) -> int:
    if not start or not end:
        return 0
    start_minutes = start.hour * 60 + start.minute
    end_minutes = end.hour * 60 + end.minute
    return max(end_minutes - start_minutes, 0)


def _report_offerings(filters: ReportFilters, *, include_inactive: bool = True):
    from apps.education.models import CourseOffering

    qs = CourseOffering.objects.filter(is_deleted=False).select_related(
        "course", "department", "location", "instructor"
    ).prefetch_related("enrollments")
    if not include_inactive:
        qs = qs.filter(is_active=True)
    if filters.department_id:
        qs = qs.filter(
            Q(department_id=filters.department_id)
            | Q(course__department_id=filters.department_id)
        )
    if filters.course_id:
        qs = qs.filter(course_id=filters.course_id)
    if filters.location_id:
        qs = qs.filter(location_id=filters.location_id)
    return qs


def _report_sessions(filters: ReportFilters):
    from apps.education.models import ClassSession

    qs = ClassSession.objects.filter(
        is_deleted=False,
        session_date__gte=filters.start,
        session_date__lte=filters.end,
    ).select_related(
        "offering",
        "offering__course",
        "offering__department",
        "offering__location",
        "class_group",
        "lesson",
        "teacher",
        "location",
    ).prefetch_related("attendances")
    if filters.department_id:
        qs = qs.filter(
            Q(offering__department_id=filters.department_id)
            | Q(offering__course__department_id=filters.department_id)
        )
    if filters.course_id:
        qs = qs.filter(offering__course_id=filters.course_id)
    if filters.location_id:
        qs = qs.filter(location_id=filters.location_id)
    return qs


def _report_enrollments(filters: ReportFilters):
    from apps.education.models import OfferingEnrollment

    qs = OfferingEnrollment.objects.filter(
        is_deleted=False,
        is_active=True,
        enrolled_at__gte=filters.start,
        enrolled_at__lte=filters.end,
    ).select_related(
        "offering",
        "offering__course",
        "offering__department",
        "offering__location",
        "student",
    ).prefetch_related("offering__sessions")
    if filters.department_id:
        qs = qs.filter(
            Q(offering__department_id=filters.department_id)
            | Q(offering__course__department_id=filters.department_id)
        )
    if filters.course_id:
        qs = qs.filter(offering__course_id=filters.course_id)
    if filters.location_id:
        qs = qs.filter(offering__location_id=filters.location_id)
    return qs


def filter_options() -> dict[str, list[dict[str, str]]]:
    """Small option lists for the filter toolbar; no PII is exposed."""
    from apps.education.models import Course, Department, Location
    from apps.forms.models import FormSchema, RequestType
    from apps.workflow.models import WorkflowDefinition

    return {
        "departments": [
            {"id": str(row["id"]), "name": row["name"]}
            for row in Department.objects.filter(is_deleted=False, is_active=True)
            .order_by("name")
            .values("id", "name")
        ],
        "courses": [
            {"id": str(row["id"]), "title": row["title"]}
            for row in Course.objects.filter(is_deleted=False, is_active=True)
            .order_by("title")
            .values("id", "title")
        ],
        "locations": [
            {"id": str(row["id"]), "name": row["name"]}
            for row in Location.objects.filter(is_deleted=False, is_active=True)
            .order_by("name")
            .values("id", "name")
        ],
        "request_types": [
            {"id": row["code"], "title": row["title"]}
            for row in RequestType.objects.filter(is_deleted=False, is_active=True)
            .order_by("title", "code")
            .values("code", "title")
        ],
        "workflows": [
            {"id": row["code"], "name": row["name"]}
            for row in WorkflowDefinition.objects.filter(is_deleted=False, is_active=True)
            .order_by("name", "code")
            .values("code", "name")
        ],
        "forms": [
            {"id": row["slug"], "title": row["title"]}
            for row in FormSchema.objects.filter(is_deleted=False, is_active=True)
            .order_by("title", "slug")
            .values("slug", "title")
        ],
    }


def financial_report(user, filters: ReportFilters) -> dict[str, Any]:
    if not can_view_financial_reports(user):
        return {
            "visible": False,
            "message": "گزارش مالی فقط برای مدیریت قابل مشاهده است.",
        }

    qs = _report_enrollments(filters)
    totals = qs.aggregate(
        revenue=Coalesce(Sum("final_amount"), Value(0)),
        average_invoice=Coalesce(Avg("final_amount"), Value(0.0, output_field=FloatField())),
        registrations=Count("id"),
        paid_count=Count("id", filter=Q(payment_method__in=("cash", "pos"))),
        pending_count=Count("id", filter=Q(payment_method="cheque")),
    )

    # ``OfferingEnrollment`` has no paid_amount ledger yet. A cheque is
    # outstanding; if its entered cheque schedule does not cover the invoice,
    # it is additionally surfaced as an incomplete record for follow-up.
    partial_count = 0
    partial_amount = 0
    for row in qs.values("final_amount", "payment_method", "cheques"):
        if row["payment_method"] != "cheque":
            continue
        invoice = _money(row["final_amount"])
        cheque_total = sum(_money(item.get("amount")) for item in (row["cheques"] or []) if isinstance(item, dict))
        if cheque_total and cheque_total < invoice:
            partial_count += 1
            partial_amount += invoice - cheque_total

    department_name = Case(
        When(offering__department__name__isnull=False, then=F("offering__department__name")),
        default=F("offering__course__department__name"),
        output_field=CharField(),
    )
    by_course = [
        {
            "label": row["offering__course__title"] or "بدون عنوان",
            "enrollments": row["enrollments"],
            "revenue": _money(row["revenue"]),
        }
        for row in qs.values("offering__course__title").annotate(
            enrollments=Count("id"), revenue=Coalesce(Sum("final_amount"), Value(0))
        ).order_by("-enrollments", "-revenue")[:10]
    ]
    by_department = [
        {
            "label": row["department_name"] or "بدون دپارتمان",
            "enrollments": row["enrollments"],
            "revenue": _money(row["revenue"]),
        }
        for row in qs.annotate(department_name=department_name)
        .values("department_name")
        .annotate(enrollments=Count("id"), revenue=Coalesce(Sum("final_amount"), Value(0)))
        .order_by("-revenue")[:10]
    ]
    by_location = [
        {
            "label": row["offering__location__name"] or "بدون محل",
            "enrollments": row["enrollments"],
            "revenue": _money(row["revenue"]),
        }
        for row in qs.values("offering__location__name")
        .annotate(enrollments=Count("id"), revenue=Coalesce(Sum("final_amount"), Value(0)))
        .order_by("-revenue")[:10]
    ]
    revenue_trend = [
        {
            "label": _jalali_month_label(row["month"]),
            "value": _money(row["revenue"]),
        }
        for row in qs.annotate(month=TruncMonth("enrolled_at"))
        .values("month")
        .annotate(revenue=Coalesce(Sum("final_amount"), Value(0)))
        .order_by("month")
    ]
    return {
        "visible": True,
        "totals": {
            "revenue": _money(totals["revenue"]),
            "average_invoice": _money(totals["average_invoice"]),
            "registrations": totals["registrations"],
            "paid_count": totals["paid_count"],
            "partial_count": partial_count,
            "pending_count": totals["pending_count"],
            "pending_amount": _money(
                qs.filter(payment_method="cheque").aggregate(total=Sum("final_amount"))["total"]
            ),
            "partial_amount": partial_amount,
        },
        "revenue_trend": revenue_trend,
        "by_course": by_course,
        "by_department": by_department,
        "by_location": by_location,
        "data_note": "در مدل فعلی، پرداخت نقدی/POS قطعی و چک در انتظار وصول در نظر گرفته شده است.",
    }


def enrollment_report(filters: ReportFilters) -> dict[str, Any]:
    offerings = _report_offerings(filters)
    status_rows = offerings.values("status").annotate(total=Count("id"))
    status_counts = {row["status"]: row["total"] for row in status_rows}
    for status in ("draft", "open", "running", "closed", "finished", "cancelled"):
        status_counts.setdefault(status, 0)

    occupancy = offerings.filter(capacity__gt=0).aggregate(
        capacity=Coalesce(Sum("capacity"), Value(0)),
        enrolled=Coalesce(Sum("enrolled_count"), Value(0)),
    )
    popular = []
    for row in offerings.annotate(
        registration_total=Count(
            "enrollments",
            filter=Q(enrollments__is_deleted=False, enrollments__is_active=True),
        )
    ).values(
        "id", "code", "title", "course__title", "capacity", "registration_total"
    ).order_by("-registration_total", "-created_at")[:12]:
        capacity = _money(row["capacity"])
        registered = row["registration_total"]
        popular.append(
            {
                "id": str(row["id"]),
                "label": row["title"] or row["course__title"] or row["code"] or "بدون عنوان",
                "enrollments": registered,
                "capacity": capacity,
                "occupancy_pct": _pct(registered, capacity) if capacity else None,
            }
        )

    active_courses = offerings.filter(
        is_active=True,
        course__is_deleted=False,
        course__is_active=True,
    ).values("course_id").distinct().count()
    occupancy_pct = _pct(occupancy["enrolled"], occupancy["capacity"])
    return {
        "status": status_counts,
        "popular": popular,
        "capacity": {
            "total": _money(occupancy["capacity"]),
            "enrolled": _money(occupancy["enrolled"]),
            "occupancy_pct": occupancy_pct,
        },
        "active_courses": active_courses,
    }


def people_report(filters: ReportFilters) -> dict[str, Any]:
    from apps.education.models import ClassSession
    from apps.persons.models import Person

    alive = Q(is_deleted=False, is_active=True)
    role_specs = (
        ("student", "دانش‌آموز"),
        ("teacher", "مدرس"),
        ("employee", "کارمند"),
        ("guardian", "ولی / سرپرست"),
    )
    by_role = []
    for code, label in role_specs:
        total = Person.objects.filter(alive).filter(
            Q(person_type=code)
            | Q(
                type_assignments__type=code,
                type_assignments__is_deleted=False,
                type_assignments__is_active=True,
            )
        ).distinct().count()
        by_role.append({"key": code, "label": label, "value": total})

    new_students = [
        {"label": _jalali_month_label(row["month"]), "value": row["total"]}
        for row in Person.objects.filter(
            alive,
            person_type=Person.Type.STUDENT,
            created_at__date__gte=filters.start,
            created_at__date__lte=filters.end,
        ).annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(total=Count("id"))
        .order_by("month")
    ]

    sessions = _report_sessions(filters).filter(teacher__isnull=False)
    teacher_rows: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"hours": 0.0, "sessions": 0, "classes": set(), "label": "مدرس نامشخص"}
    )
    for row in sessions.values(
        "teacher_id", "teacher__first_name", "teacher__last_name",
        "offering_id", "class_code", "start_time", "end_time"
    ):
        key = str(row["teacher_id"])
        item = teacher_rows[key]
        item["label"] = (f"{row['teacher__first_name'] or ''} {row['teacher__last_name'] or ''}").strip() or item["label"]
        item["hours"] += _duration_minutes(row["start_time"], row["end_time"]) / 60
        item["sessions"] += 1
        item["classes"].add(str(row["offering_id"] or row["class_code"] or row["teacher_id"]))
    active_teachers = [
        {
            "label": item["label"],
            "hours": round(item["hours"], 1),
            "sessions": item["sessions"],
            "classes": len(item["classes"]),
        }
        for item in sorted(teacher_rows.values(), key=lambda value: (-value["hours"], value["label"]))[:10]
    ]
    return {
        "by_role": by_role,
        "new_students": new_students,
        "active_teachers": active_teachers,
    }


def class_report(filters: ReportFilters) -> dict[str, Any]:
    from apps.education.models import AttendanceRecord, ClassSession, Location

    sessions = _report_sessions(filters)
    status_rows = sessions.values("status").annotate(total=Count("id"))
    status = {row["status"]: row["total"] for row in status_rows}
    for code in ("scheduled", "held", "cancelled"):
        status.setdefault(code, 0)
    status["deferred"] = sessions.filter(
        status=ClassSession.Status.SCHEDULED,
        session_date__lt=timezone.localdate(),
    ).count()

    attendance = AttendanceRecord.objects.filter(
        is_deleted=False, session__in=sessions
    ).values("status").annotate(total=Count("id"))
    attendance_counts = {row["status"]: row["total"] for row in attendance}
    for code in ("present", "absent", "late", "excused"):
        attendance_counts.setdefault(code, 0)
    attendance_total = sum(attendance_counts.values())
    sessions_with_roster = sessions.annotate(
        attendance_total=Count("attendances", filter=Q(attendances__is_deleted=False))
    ).aggregate(
        average_attendance=Coalesce(Avg("attendance_total"), Value(0.0, output_field=FloatField()))
    )

    room_rows: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"label": "بدون محل", "used_minutes": 0}
    )
    for row in sessions.exclude(status=ClassSession.Status.CANCELLED).values(
        "location_id", "location__name", "start_time", "end_time"
    ):
        key = str(row["location_id"] or "none")
        room_rows[key]["label"] = row["location__name"] or room_rows[key]["label"]
        room_rows[key]["used_minutes"] += _duration_minutes(row["start_time"], row["end_time"])
    days = (filters.end - filters.start).days + 1
    room_capacity_minutes = days * REPORT_DAILY_OPEN_MINUTES
    rooms = []
    location_qs = Location.objects.filter(is_deleted=False, is_active=True)
    if filters.location_id:
        location_qs = location_qs.filter(pk=filters.location_id)
    for row in location_qs.values("id", "name"):
        key = str(row["id"])
        item = room_rows.pop(key, {"label": row["name"], "used_minutes": 0})
        item["label"] = row["name"]
        item["available_minutes"] = room_capacity_minutes
        item["utilization_pct"] = min(_pct(item["used_minutes"], room_capacity_minutes), 100.0)
        rooms.append(item)
    # Keep historical sessions whose location was removed from the active list.
    for item in room_rows.values():
        item["available_minutes"] = room_capacity_minutes
        item["utilization_pct"] = min(_pct(item["used_minutes"], room_capacity_minutes), 100.0)
        rooms.append(item)
    rooms.sort(key=lambda value: (value["utilization_pct"], value["label"]))
    total_used = sum(item["used_minutes"] for item in rooms)
    total_available = room_capacity_minutes * max(len(rooms), 1)

    return {
        "sessions": status,
        "attendance": {
            "counts": attendance_counts,
            "total": attendance_total,
            "absence_pct": _pct(attendance_counts["absent"], attendance_total),
            "late_pct": _pct(attendance_counts["late"], attendance_total),
            "average_per_session": round(float(sessions_with_roster["average_attendance"] or 0), 1),
        },
        "rooms": rooms[:20],
        "room_utilization_pct": min(_pct(total_used, total_available), 100.0),
        "room_assumption": "ظرفیت زمانی هر محل بر مبنای ۸ ساعت کاری در هر روز محاسبه شده است.",
    }


def workflow_report(filters: ReportFilters) -> dict[str, Any]:
    from apps.forms.models import FormSubmission
    from apps.workflow.models import ActionLog, Instance

    instances = Instance.objects.filter(
        is_deleted=False,
        created_at__date__gte=filters.start,
        created_at__date__lte=filters.end,
    ).select_related("workflow_definition", "current_state", "requester")
    instance_status = {
        row["status"]: row["total"]
        for row in instances.values("status").annotate(total=Count("id"))
    }
    for code in ("running", "completed", "rejected", "cancelled"):
        instance_status.setdefault(code, 0)

    first_response = ActionLog.objects.filter(
        instance_id=OuterRef("pk"), is_deleted=False
    ).exclude(action="create").order_by("created_at").values("created_at")[:1]
    response_rows = instances.annotate(first_response=Subquery(first_response)).values(
        "created_at", "first_response"
    )
    response_seconds = []
    for row in response_rows:
        if row["first_response"] and row["created_at"]:
            response_seconds.append((row["first_response"] - row["created_at"]).total_seconds())
    avg_response_hours = round(sum(response_seconds) / len(response_seconds) / 3600, 1) if response_seconds else 0.0

    submissions = FormSubmission.objects.filter(
        is_deleted=False,
        created_at__date__gte=filters.start,
        created_at__date__lte=filters.end,
    ).select_related("form_schema", "workflow_instance")
    form_status = {
        row["status"]: row["total"]
        for row in submissions.values("status").annotate(total=Count("id"))
    }
    form_types = [
        {"label": row["form_schema__title"] or row["form_schema__slug"], "value": row["total"]}
        for row in submissions.values("form_schema__title", "form_schema__slug")
        .annotate(total=Count("id"))
        .order_by("-total")[:10]
    ]
    return {
        "status": instance_status,
        "form_status": form_status,
        "form_types": form_types,
        "pending_review": instance_status.get("running", 0) + form_status.get("submitted", 0),
        "avg_response_hours": avg_response_hours,
        "responded_requests": len(response_seconds),
    }


def communications_report(filters: ReportFilters) -> dict[str, Any]:
    from apps.workflow.models import NotificationOutbox

    qs = NotificationOutbox.objects.filter(
        is_deleted=False,
        created_at__date__gte=filters.start,
        created_at__date__lte=filters.end,
    )
    rows = qs.values("channel", "status").annotate(total=Count("id"))
    channels: dict[str, dict[str, int]] = defaultdict(dict)
    for row in rows:
        channels[row["channel"]][row["status"]] = row["total"]
    return {
        "total": qs.count(),
        "unread_in_app": qs.filter(channel="in_app", is_read=False).count(),
        "by_channel": [{"label": key, "values": value} for key, value in channels.items()],
    }


def dashboard_data(user, filters: ReportFilters) -> dict[str, Any]:
    """Build the single dashboard read model used by the page and exports."""
    financial = financial_report(user, filters)
    enrollments = enrollment_report(filters)
    people = people_report(filters)
    classes = class_report(filters)
    workflow = workflow_report(filters)
    communications = communications_report(filters)
    active_students = next((row["value"] for row in people["by_role"] if row["key"] == "student"), 0)
    from apps.persons.models import Person

    thirty_days_ago = timezone.localdate() - dt.timedelta(days=29)
    new_students_30d = Person.objects.filter(
        is_deleted=False,
        is_active=True,
        person_type=Person.Type.STUDENT,
        created_at__date__gte=thirty_days_ago,
        created_at__date__lte=timezone.localdate(),
    ).count()
    return {
        "filters": filters.as_dict(),
        "permissions": {"can_view_financial": financial.get("visible", False)},
        "kpis": {
            "active_courses": enrollments["active_courses"],
            "total_revenue": financial.get("totals", {}).get("revenue", 0),
            "active_students": active_students,
            "class_utilization_pct": enrollments["capacity"]["occupancy_pct"],
            "room_utilization_pct": classes["room_utilization_pct"],
            "pending_requests": workflow["pending_review"],
            "new_students_30d": new_students_30d,
        },
        "financial": financial,
        "enrollments": enrollments,
        "people": people,
        "classes": classes,
        "workflow": workflow,
        "communications": communications,
    }


def export_rows(
    data: dict[str, Any],
    report: str,
    *,
    workflow_rows: list[dict[str, Any]] | None = None,
) -> list[tuple[str, list[str], list[list[Any]]]]:
    """Convert the JSON read model to Excel-friendly sheet definitions."""
    def excel_value(value):
        return value.isoformat() if hasattr(value, "isoformat") else value

    sheets: list[tuple[str, list[str], list[list[Any]]]] = []
    if report in {"all", "financial"} and data["financial"].get("visible"):
        section = data["financial"]
        sheets.append(
            (
                "مالی",
                ["شاخص", "مقدار"],
                [
                    ["درآمد کل", section["totals"]["revenue"]],
                    ["میانگین مبلغ ثبت‌نام", section["totals"]["average_invoice"]],
                    ["تعداد ثبت‌نام", section["totals"]["registrations"]],
                    ["پرداخت‌شده", section["totals"]["paid_count"]],
                    ["ناقص", section["totals"]["partial_count"]],
                    ["در انتظار پرداخت", section["totals"]["pending_count"]],
                    ["مطالبات در انتظار", section["totals"]["pending_amount"]],
                ],
            )
        )
        sheets.append(
            (
                "درآمد دوره‌ها",
                ["دوره", "تعداد ثبت‌نام", "درآمد"],
                [[row["label"], row["enrollments"], row["revenue"]] for row in section["by_course"]],
            )
        )
        sheets.append(
            (
                "درآمد دپارتمان‌ها",
                ["دپارتمان", "تعداد ثبت‌نام", "درآمد"],
                [[row["label"], row["enrollments"], row["revenue"]] for row in section["by_department"]],
            )
        )
        sheets.append(
            (
                "درآمد محل‌ها",
                ["محل آموزش", "تعداد ثبت‌نام", "درآمد"],
                [[row["label"], row["enrollments"], row["revenue"]] for row in section["by_location"]],
            )
        )
    if report in {"all", "enrollments"}:
        section = data["enrollments"]
        sheets.append(
            (
                "ثبت‌نام و ظرفیت",
                ["برگزاری", "ثبت‌نام", "ظرفیت", "درصد اشغال"],
                [[row["label"], row["enrollments"], row["capacity"], row["occupancy_pct"]] for row in section["popular"]],
            )
        )
        sheets.append(
            (
                "وضعیت برگزاری",
                ["وضعیت", "تعداد"],
                [[key, value] for key, value in section["status"].items()],
            )
        )
    if report in {"all", "people"}:
        section = data["people"]
        sheets.append(
            (
                "اشخاص",
                ["نقش", "تعداد"],
                [[row["label"], row["value"]] for row in section["by_role"]],
            )
        )
        sheets.append(
            (
                "مدرسان فعال",
                ["مدرس", "ساعت تدریس", "جلسات", "کلاس‌ها"],
                [[row["label"], row["hours"], row["sessions"], row["classes"]] for row in section["active_teachers"]],
            )
        )
    if report in {"all", "classes"}:
        section = data["classes"]
        sheets.append(
            (
                "بهره‌وری محل‌ها",
                ["محل", "دقیقه استفاده", "دقیقه قابل استفاده", "درصد بهره‌وری"],
                [[row["label"], row["used_minutes"], row["available_minutes"], row["utilization_pct"]] for row in section["rooms"]],
            )
        )
        sheets.append(
            (
                "حضور و غیاب",
                ["وضعیت", "تعداد"],
                [[key, value] for key, value in section["attendance"]["counts"].items()],
            )
        )
    if report in {"all", "workflow"}:
        section = data["workflow"]
        sheets.append(
            (
                "درخواست‌ها",
                ["وضعیت", "تعداد"],
                [[key, value] for key, value in section["status"].items()],
            )
        )
        sheets.append(
            (
                "وضعیت فرم‌ها",
                ["وضعیت", "تعداد"],
                [[key, value] for key, value in section["form_status"].items()],
            )
        )
        sheets.append(
            (
                "انواع فرم",
                ["فرم", "تعداد"],
                [[row["label"], row["value"]] for row in section["form_types"]],
            )
        )
        if workflow_rows is not None:
            sheets.append(
                (
                    "جزئیات درخواست",
                    [
                        "شماره", "نوع درخواست", "فرآیند", "عنوان", "وضعیت گردش‌کار",
                        "وضعیت درخواست", "مرحله", "ثبت‌کننده", "واحد ثبت‌کننده",
                        "مسئول فعلی", "واحد مسئول", "فرم", "تاریخ ایجاد", "تاریخ ثبت",
                        "تاریخ بررسی", "بررسی‌کننده", "تاریخ تأیید", "تاریخ رد", "تاریخچه اقدامات",
                    ],
                    [
                        [
                            row.get("request_number") or row.get("tracking_number") or row.get("id"),
                            row.get("request_type_title"), row.get("workflow_name"), row.get("title"),
                            row.get("status"), row.get("request_status"), row.get("current_step"),
                            row.get("requester_name"), row.get("requester_department"),
                            ", ".join(item.get("name") or item.get("username", "") for item in row.get("assigned_users", [])),
                            ", ".join(sorted({item.get("department", "") for item in row.get("assigned_users", []) if item.get("department")})),
                            row.get("form_title"), excel_value(row.get("created_at")),
                            excel_value(row.get("form_submitted_at")),
                            excel_value(row.get("reviewed_at") or row.get("last_reviewed_at")),
                            row.get("reviewed_by"), excel_value(row.get("approved_at")),
                            excel_value(row.get("rejected_at")),
                            " | ".join(
                                f"{item.get('action', '')}: {item.get('actor_name') or item.get('actor', '')}"
                                f" ({item.get('created_at', '')}) {item.get('comment', '')}"
                                for item in row.get("action_history", [])
                            )[:32000],
                        ]
                        for row in workflow_rows
                    ],
                )
            )
    if report in {"all", "communications"}:
        section = data["communications"]
        channel_rows = []
        for row in section["by_channel"]:
            for status, total in row["values"].items():
                channel_rows.append([row["label"], status, total])
        sheets.append(
            (
                "ارتباطات",
                ["کانال", "وضعیت", "تعداد"],
                channel_rows,
            )
        )
    return sheets
