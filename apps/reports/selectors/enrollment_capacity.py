"""Bounded, aggregate-only enrollment reporting; never exposes student/finance data."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from django.db.models import Count, Exists, F, IntegerField, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce, Greatest
from django.utils import timezone

from apps.academics.models import ClassEnrollment, ClassGroup
from apps.academics.scoping import REFERENCE_DATA_ROLES, class_groups_visible_to
from apps.core.utils import english_numbers, jalali_date_str
from apps.education.models import Course, CourseOffering, OfferingEnrollment
from apps.reports.selectors.reports import ReportFilterError, _clean_uuid, _parse_report_date


@dataclass(frozen=True)
class CapacityFilters:
    source: str
    start: dt.date
    end: dt.date
    course: str = ""
    classroom: str = ""
    status: str = ""
    capacity: str = ""
    search: str = ""
    group: str = "day"

    @classmethod
    def parse(cls, query):
        today = timezone.localdate()
        source = query.get("source", "offerings")
        if source not in {"offerings", "classes"}:
            raise ReportFilterError("نوع گزارش معتبر نیست.")
        start = _parse_report_date(query.get("from")) or today - dt.timedelta(days=29)
        end = _parse_report_date(query.get("to")) or today
        if end < start or (end - start).days > 365:
            raise ReportFilterError("بازه باید مرتب و حداکثر ۳۶۶ روز باشد.")
        status = query.get("status", "")
        allowed = dict(CourseOffering.Status.choices) if source == "offerings" else {"active", "inactive"}
        if status and status not in allowed:
            raise ReportFilterError("وضعیت انتخاب‌شده با نوع گزارش سازگار نیست.")
        capacity = query.get("capacity", "")
        if capacity not in {"", "full", "available", "unlimited"}:
            raise ReportFilterError("فیلتر ظرفیت معتبر نیست.")
        group = query.get("group", "day")
        if group not in {"day", "week", "month"}:
            raise ReportFilterError("تفکیک زمانی معتبر نیست.")
        return cls(source, start, end, _clean_uuid(query.get("course")),
                   _clean_uuid(query.get("classroom")), status, capacity,
                   english_numbers(query.get("search", "").strip())[:128], group)

    def dates(self):
        return {"from": self.start.isoformat(), "to": self.end.isoformat(),
                "from_jalali": jalali_date_str(self.start), "to_jalali": jalali_date_str(self.end)}


def visible_offerings(user):
    qs = CourseOffering.objects.filter(is_deleted=False)
    roles = set(user.role_codes())
    if user.is_superuser or roles & REFERENCE_DATA_ROLES:
        return qs
    # An explicitly authorized teacher still only sees their own teaching.
    person = getattr(user, "person", None)
    if person is not None and "teacher" in roles:
        return qs.filter(instructor=person)
    return qs.none()


def visible_classes(user):
    if user.is_superuser:
        return ClassGroup.objects.filter(is_deleted=False)
    roles = set(user.role_codes())
    if not roles & (REFERENCE_DATA_ROLES | {"teacher"}):
        return ClassGroup.objects.none()
    return class_groups_visible_to(user).filter(is_deleted=False)


def _count_for(queryset, foreign_key):
    return Coalesce(Subquery(
        queryset.filter(**{foreign_key: OuterRef("pk")}).order_by()
        .values(foreign_key).annotate(n=Count("pk")).values("n"),
        output_field=IntegerField(),
    ), Value(0))


def report_query(user, filters):
    """Independent count subqueries prevent multiplication by sessions or joins."""
    if filters.source == "offerings":
        qs = visible_offerings(user)
        registrations = OfferingEnrollment.objects.filter(is_deleted=False, is_active=True)
        foreign_key, date_field = "offering_id", "enrolled_at"
        # Count live memberships: legacy counters can drift after refunds/soft deletion.
        qs = qs.annotate(enrolled=_count_for(registrations, foreign_key))
        if filters.course:
            qs = qs.filter(course_id=filters.course)
        if filters.status:
            qs = qs.filter(status=filters.status)
        if filters.search:
            qs = qs.filter(Q(title__istartswith=filters.search) | Q(code__istartswith=filters.search))
    else:
        qs = visible_classes(user)
        registrations = ClassEnrollment.objects.filter(is_deleted=False, is_active=True)
        foreign_key, date_field = "class_group_id", "enrollment_date"
        qs = qs.annotate(enrolled=_count_for(registrations, foreign_key))
        if filters.course:
            # A group can have many sessions for the same course; EXISTS avoids duplicates.
            from apps.education.models import ClassSession
            linked = ClassSession.objects.filter(
                class_group_id=OuterRef("pk"), offering__course_id=filters.course,
                is_deleted=False, offering__is_deleted=False,
            )
            qs = qs.alias(matches_course=Exists(linked)).filter(matches_course=True)
        if filters.status:
            qs = qs.filter(is_active=filters.status == "active")
        if filters.search:
            qs = qs.filter(Q(name__istartswith=filters.search) | Q(code__istartswith=filters.search))
    if filters.classroom:
        qs = qs.filter(pk=filters.classroom)
    if filters.capacity == "full":
        qs = qs.filter(capacity__gt=0, enrolled__gte=F("capacity"))
    elif filters.capacity == "available":
        qs = qs.filter(Q(capacity=0) | Q(enrolled__lt=F("capacity")))
    elif filters.capacity == "unlimited":
        qs = qs.filter(capacity=0)
    registrations = registrations.filter(**{date_field + "__range": (filters.start, filters.end)})
    qs = qs.annotate(period_enrollments=_count_for(registrations, foreign_key))
    return qs, registrations, foreign_key, date_field


def report_summary(qs, registrations, foreign_key, date_field, filters):
    totals = qs.aggregate(
        total=Count("pk"), sum_enrolled=Coalesce(Sum("enrolled"), 0),
        sum_capacity=Coalesce(Sum("capacity"), 0),
        remaining=Coalesce(Sum(Greatest(F("capacity") - F("enrolled"), Value(0)), filter=Q(capacity__gt=0)), 0),
        full=Count("pk", filter=Q(capacity__gt=0, enrolled__gte=F("capacity"))),
        unlimited=Count("pk", filter=Q(capacity=0)),
        registrations=Coalesce(Sum("period_enrollments"), 0),
    )
    totals["enrolled"] = totals.pop("sum_enrolled")
    totals["capacity"] = totals.pop("sum_capacity")
    totals["available"] = totals["total"] - totals["full"]
    # SQL returns at most 366 date groups, regardless of the number of registrations.
    days = registrations.filter(**{foreign_key + "__in": qs.order_by().values("pk")}).order_by().values(date_field).annotate(total=Count("pk"))
    daily = {row[date_field]: row["total"] for row in days}
    buckets = {}
    current = filters.start
    while current <= filters.end:
        if filters.group == "week":
            key = current - dt.timedelta(days=(current.weekday() + 2) % 7)  # Saturday
            label = "هفتهٔ " + jalali_date_str(key)
        elif filters.group == "month":
            # Jalali month grouping, with Gregorian boundaries still used for filtering.
            label = jalali_date_str(current)[:7]
            key = label
        else:
            key, label = current, jalali_date_str(current)
        entry = buckets.setdefault(key, {"label": label, "total": 0})
        entry["total"] += daily.get(current, 0)
        current += dt.timedelta(days=1)
    return {"totals": totals, "trend": list(buckets.values()), "dates": filters.dates()}


def report_rows(qs, source):
    if source == "offerings":
        qs = qs.select_related("course").only(
            "id", "created_at", "title", "code", "capacity", "enrolled_count",
            "status", "is_active", "course__title", "course_id",
        )
    else:
        qs = qs.select_related(None).select_related("term").only(
            "id", "created_at", "name", "code", "capacity", "is_active", "term__title", "term_id",
        )
    return qs.order_by("-created_at", "-pk")


def row_data(row, source):
    limited = row.capacity > 0
    return {
        "id": str(row.pk), "code": row.code,
        "title": (row.title or row.course.title) if source == "offerings" else row.name,
        "parent": row.course.title if source == "offerings" else row.term.title,
        "capacity": row.capacity if limited else None,
        "enrolled": row.enrolled, "remaining": max(row.capacity - row.enrolled, 0) if limited else None,
        "full": limited and row.enrolled >= row.capacity,
        "occupancy": round(row.enrolled * 100 / row.capacity, 1) if limited else None,
        "period_enrollments": row.period_enrollments,
        "status": row.get_status_display() if source == "offerings" else ("فعال" if row.is_active else "غیرفعال"),
        "is_active": row.is_active,
    }


def report_options(user, query):
    """Searchable, bounded pickers; never ship the entire course/class directory."""
    source = query.get("source", "offerings")
    if source not in {"offerings", "classes"}:
        raise ReportFilterError("نوع گزارش معتبر نیست.")
    kind = query.get("kind", "course")
    search = query.get("q", "").strip()[:128]
    selected = _clean_uuid(query.get("selected"))
    if kind == "course":
        from apps.education.models import ClassSession
        offerings = visible_offerings(user)
        group_courses = ClassSession.objects.filter(
            class_group__in=visible_classes(user).order_by().values("pk"),
            is_deleted=False, offering__is_deleted=False,
        ).order_by().values("offering__course_id")
        qs = Course.objects.filter(is_deleted=False).filter(
            Q(pk__in=offerings.order_by().values("course_id")) | Q(pk__in=group_courses)
        )
        label_field = "title"
    elif kind == "classroom":
        filters = CapacityFilters.parse({"source": source, "course": query.get("course", "")})
        qs, _, _, _ = report_query(user, filters)
        label_field = "title" if source == "offerings" else "name"
    else:
        raise ReportFilterError("نوع فهرست معتبر نیست.")
    if selected:
        qs = qs.filter(pk=selected)
    elif search:
        qs = qs.filter(Q(**{label_field + "__istartswith": search}) | Q(code__istartswith=search))
    rows = list(qs.order_by(label_field, "pk").values("id", "code", label_field)[:31])
    return {"results": [{"id": str(r["id"]), "label": (r[label_field] or r["code"] or "بدون عنوان") + " · " + r["code"]} for r in rows[:30]], "has_more": len(rows) > 30}
