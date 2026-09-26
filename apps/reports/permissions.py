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


CAPACITY_REPORT_RESOURCE = "workspace-enrollment-capacity"


def can_access_capacity_report(user) -> bool:
    """Explicit user ACL overrides the default management/supervisor grant.

    This grants aggregate reporting only. Selectors still limit teachers to
    their classes; student/guardian accounts never receive institution totals.
    """
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if not user.is_active or getattr(user, "is_deleted", False):
        return False
    from apps.core.access_enforcer import acl_strict
    return acl_strict(user, "page", CAPACITY_REPORT_RESOURCE, "view",
                      baseline=bool(role_codes(user) & REPORT_ACCESS_ROLES))


class CanAccessCapacityReport(BasePermission):
    message = "دسترسی به گزارش ثبت‌نام و ظرفیت کلاس‌ها مجاز نیست."

    def has_permission(self, request, view):
        return can_access_capacity_report(request.user)
