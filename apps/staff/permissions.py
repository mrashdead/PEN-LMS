"""RBAC gates for the staff operations surface.

Permission split (criterion §4): READ is broad (staff may see the shared
operational picture), WRITE/review is narrow. The actual row scope still
comes from the ``*_visible_to`` selectors — a permission class is never the
only boundary.
"""
from __future__ import annotations

from rest_framework.permissions import BasePermission, SAFE_METHODS

from apps.staff.models import APPROVER_ROLES
from apps.staff.services import _is_approver


class IsStaffUser(BasePermission):
    """Any authenticated staff-role user may READ the staff module.

    End-user roles (student/guardian) have no staff operations at all; a
    teacher IS staff for this module (they keep timesheets and leave too).
    """

    message = "این بخش فقط برای کارکنان قابل دسترسی است."
    staff_roles = {"employee", "teacher", "supervisor", "manager", "workflow_admin", "hr"}

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, "is_superuser", False):
            return True
        return bool(set(user.role_codes()) & self.staff_roles)


class IsStaffReviewer(BasePermission):
    """Review verbs (approve/reject) are restricted to approver roles."""

    message = "فقط مدیر یا سرپرست مجاز به بررسی این رکورد است."

    def has_permission(self, request, view) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return _is_approver(request.user)


class IsTimesheetOwnerOrReviewer(BasePermission):
    """Owner may write own pending records; reviewers may act on any."""

    message = "شما فقط می‌توانید ساعت کاری خودتان را ثبت کنید."

    def has_object_permission(self, request, view, obj) -> bool:
        if _is_approver(request.user):
            return True
        return getattr(obj, "user_id", None) == request.user.pk
