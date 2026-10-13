from __future__ import annotations

from apps.leads.models import Lead
from apps.leads.permissions import is_lead_assessor, is_lead_operator
from apps.persons.models import Person


def leads_for_user(user):
    qs = Lead.objects.select_related("assessor", "course", "lesson", "created_by", "created_by__person", "enrolled_person")
    if is_lead_operator(user):
        return qs
    person = getattr(user, "person", None)
    return qs.filter(assessor=person) if is_lead_assessor(user) else qs.none()


def assigned_leads_for_assessor(user):
    """Return only leads assigned to the authenticated, explicitly authorized assessor."""
    qs = Lead.objects.select_related("assessor", "course", "lesson")
    person = getattr(user, "person", None)
    if not is_lead_assessor(user):
        return qs.none()
    return qs.filter(assessor=person).order_by("assessment_date", "assessment_time", "-created_at")


def assessors():
    """Only explicitly authorized active staff can receive assessment requests."""
    return (
        Person.objects.filter(is_active=True, is_deleted=False, can_assess_leads=True)
        .order_by("first_name", "last_name")
    )
