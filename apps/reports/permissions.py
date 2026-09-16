"""RBAC gates for the reporting surface.

The dashboard deliberately has a smaller audience than the ordinary staff
workspace. A hidden sidebar item is only a UX affordance; these permissions
are the actual API/page boundary.
"""
from __future__ import annotations

from rest_framework.permissions import BasePermission


REPORT_ACCESS_ROLES = {"manager", "workflow_admin", "hr", "supervisor"}
FINANCIAL_REPORT_ROLES = {"manager", "workflow_admin", "hr"}


def role_codes(user) -> set[str]:
    if not user or not getattr(user, "is_authenticated", False):
        return set()
    try:
        return set(user.role_codes())
    except Exception:  # pragma: no cover - defensive for auth substitutes
        return set()


def can_access_reports(user) -> bool:
    return bool(role_codes(user) & REPORT_ACCESS_ROLES)


def can_view_financial_reports(user) -> bool:
    return bool(role_codes(user) & FINANCIAL_REPORT_ROLES)


class CanAccessReports(BasePermission):
    """Managers and supervisors may read operational analytics."""

    message = "فقط مدیریت یا سرپرست مجاز به مشاهدهٔ مرکز گزارش‌هاست."

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and not getattr(user, "is_deleted", False)
            and can_access_reports(user)
        )
