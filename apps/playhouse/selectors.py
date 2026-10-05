"""
Playhouse data-access helpers (selectors).

Keep all QuerySet construction here — views and pages never hand-build
queries. N+1 avoidance is baked in via ``select_related``/``prefetch_related``.
"""
from __future__ import annotations

from datetime import date

from django.db.models import Q, QuerySet
from django.utils import timezone

from apps.playhouse.models import (
    PlayhouseInvoice,
    PlayhouseMember,
    PlayhouseSession,
)
from apps.persons.models import Person


def sessions_today() -> QuerySet[PlayhouseSession]:
    """Today's sessions with member + operator preloaded, newest first."""
    return (
        PlayhouseSession.objects.filter(
            Q(session_date=timezone.localdate())
            | Q(session_date__isnull=True, created_at__date=timezone.localdate())
        )
        .select_related("member", "operator", "invoice")
        .prefetch_related("invoice__items")
        .order_by("entry_at", "created_at")
    )


def sessions_on(day: date) -> QuerySet[PlayhouseSession]:
    """Daily attendance register, including incomplete and cancelled entries."""
    return (
        PlayhouseSession.objects.filter(
            Q(session_date=day)
            | Q(session_date__isnull=True, created_at__date=day)
        )
        .select_related("member", "operator", "ended_by", "invoice")
        .prefetch_related("invoice__items")
        .order_by("entry_at", "created_at")
    )


def active_sessions() -> QuerySet[PlayhouseSession]:
    """Sessions still inside the playhouse (running timers)."""
    return (
        PlayhouseSession.objects.filter(status=PlayhouseSession.Status.ACTIVE)
        .select_related("member", "operator")
        .order_by("entry_at")
    )


def member_autocomplete(query: str, limit: int = 20) -> QuerySet[PlayhouseMember]:
    """Members matching first/last name or guardian mobile (for the picker)."""
    qs: QuerySet[PlayhouseMember] = PlayhouseMember.objects.all()
    if query:
        clean = query.strip()
        qs = qs.filter(
            Q(first_name__icontains=clean)
            | Q(last_name__icontains=clean)
            | Q(guardian_mobile__icontains=clean)
        )
    return qs.order_by("-created_at")[:limit]


def member_and_person_autocomplete(query: str, limit: int = 25) -> list[dict]:
    """Return stored playhouse visitors plus active Pen students."""
    clean = (query or "").strip()
    members = member_autocomplete(clean, limit=limit)
    linked_people = {str(member.person_id) for member in members if member.person_id}
    results = [
        {
            "id": str(member.pk),
            "source": "playhouse",
            "member_pk": str(member.pk),
            "person_pk": str(member.person_id) if member.person_id else "",
            "first_name": member.first_name,
            "last_name": member.last_name,
            "age": member.age,
            "guardian_mobile": member.guardian_mobile,
            "display_name": member.display_name,
            "meta": "عضو خانه بازی" if not member.person_id else "دانش‌آموز لینک‌شده",
        }
        for member in members
    ]
    if len(results) < limit:
        people = Person.objects.filter(
            person_type=Person.Type.STUDENT,
            is_active=True,
        )
        if clean:
            people = people.filter(
                Q(first_name__icontains=clean)
                | Q(last_name__icontains=clean)
                | Q(mobile__icontains=clean)
                | Q(student_code__icontains=clean)
            )
        for person in people.order_by("-created_at")[: limit - len(results)]:
            if str(person.pk) in linked_people:
                continue
            age = None
            if person.birth_date:
                today = date.today()
                age = today.year - person.birth_date.year - (
                    (today.month, today.day) < (person.birth_date.month, person.birth_date.day)
                )
            results.append({
                "id": str(person.pk),
                "source": "person",
                "member_pk": "",
                "person_pk": str(person.pk),
                "first_name": person.first_name,
                "last_name": person.last_name,
                "age": age,
                "guardian_mobile": person.mobile,
                "display_name": person.display_name,
                "meta": "دانش‌آموز مجموعه Pen",
            })
    return results[:limit]


def invoices_between(
    start: date | None = None, end: date | None = None
) -> QuerySet[PlayhouseInvoice]:
    """Invoices optionally filtered by paid date range, for finance reports."""
    qs = PlayhouseInvoice.objects.select_related(
        "session", "member", "operator"
    ).order_by("-created_at")
    if start:
        qs = qs.filter(created_at__date__gte=start)
    if end:
        qs = qs.filter(created_at__date__lte=end)
    return qs
