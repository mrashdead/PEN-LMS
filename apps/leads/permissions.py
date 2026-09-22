from __future__ import annotations

from rest_framework.permissions import BasePermission


LEAD_OPERATOR_ROLES = {"employee", "supervisor", "manager", "hr", "workflow_admin"}
LEAD_ASSESSOR_ROLES = LEAD_OPERATOR_ROLES | {"teacher"}


def _roles(user):
    return user.role_codes() if hasattr(user, "role_codes") else set()


class IsLeadOperator(BasePermission):
    message = "فقط کارکنان مجاز می‌توانند لیدها را مدیریت کنند."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_active and _roles(user) & LEAD_OPERATOR_ROLES)


class IsLeadAssessor(BasePermission):
    message = "فقط استاد یا کارکنان مجاز می‌توانند تعیین سطح را ثبت کنند."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_active and _roles(user) & LEAD_ASSESSOR_ROLES)


class IsLeadTeacher(BasePermission):
    message = "این بخش فقط برای استادان تعیین سطح است."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_active and "teacher" in _roles(user))


def is_lead_operator(user):
    return bool(user and _roles(user) & LEAD_OPERATOR_ROLES)
