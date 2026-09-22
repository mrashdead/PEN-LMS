from __future__ import annotations

from django.db.models import Q
from django.utils import timezone

from apps.leads.models import Lead
from apps.persons.models import Person


def leads_for_user(user):
    qs = Lead.objects.select_related("assessor", "course", "lesson", "created_by", "created_by__person", "enrolled_person")
    roles = user.role_codes() if hasattr(user, "role_codes") else set()
    if roles & {"employee", "supervisor", "manager", "hr", "workflow_admin"}:
        return qs
    person = getattr(user, "person", None)
    return qs.filter(assessor=person) if person else qs.none()


def assigned_leads_for_teacher(user):
    """Return only leads assigned to the authenticated teacher's own profile."""
    qs = Lead.objects.select_related("assessor", "course", "lesson")
    person = getattr(user, "person", None)
    if not person or not person.is_active or not person.is_teacher():
        return qs.none()
    return qs.filter(assessor=person).order_by("assessment_date", "assessment_time", "-created_at")


def assessors():
    """Active teachers, including people whose teacher type is an assignment."""
    now = timezone.now()
    current_teacher_assignment = (
        Q(type_assignments__type=Person.Type.TEACHER)
        & Q(type_assignments__is_active=True)
        & Q(type_assignments__is_deleted=False)
        & (Q(type_assignments__valid_from__isnull=True) | Q(type_assignments__valid_from__lte=now))
        & (Q(type_assignments__valid_to__isnull=True) | Q(type_assignments__valid_to__gte=now))
    )
    return (
        Person.objects.filter(is_active=True, is_deleted=False)
        .filter(Q(person_type=Person.Type.TEACHER) | current_teacher_assignment)
        .distinct()
        .order_by("first_name", "last_name")
    )
