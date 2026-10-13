from __future__ import annotations

from rest_framework.permissions import BasePermission

from apps.core.access_enforcer import acl_allows, acl_verbs_for

LEAD_OPERATOR_ROLES = {"supervisor", "manager", "hr", "workflow_admin"}


def _roles(user):
    return user.role_codes() if hasattr(user, "role_codes") else set()


def _active_user(user):
    return bool(user and user.is_authenticated and user.is_active and not getattr(user, "is_deleted", False))


def is_lead_operator(user):
    """Resolve full lead management from roles or an explicit lead grant."""
    if not _active_user(user):
        return False
    page_access = acl_allows(user, "page", "leads-dashboard", "view")
    if page_access is not None:
        return page_access
    model_verbs = acl_verbs_for(user, "model", "leads.lead")
    if model_verbs is not None:
        return {"view", "add", "change", "delete"}.issubset(model_verbs)
    return bool(_roles(user) & LEAD_OPERATOR_ROLES)


def is_lead_assessor(user):
    person = getattr(user, "person", None) if _active_user(user) else None
    return bool(person and person.is_active and not person.is_deleted and person.can_assess_leads)


def can_assess_lead(user, lead):
    return is_lead_operator(user) or (is_lead_assessor(user) and lead.assessor_id == user.person.pk)


class IsLeadOperator(BasePermission):
    message = "فقط کارکنان مجاز می‌توانند لیدها را مدیریت کنند."

    def has_permission(self, request, view):
        return is_lead_operator(request.user)


class IsLeadAssessor(BasePermission):
    message = "فقط کارکنان مجاز یا ارزیابان تعیین‌شده می‌توانند به لیدها دسترسی داشته باشند."

    def has_permission(self, request, view):
        return is_lead_operator(request.user) or is_lead_assessor(request.user)


class IsAssignedLeadAssessor(BasePermission):
    message = "این بخش فقط برای ارزیابان مجاز تعیین سطح است."

    def has_permission(self, request, view):
        return is_lead_assessor(request.user)
