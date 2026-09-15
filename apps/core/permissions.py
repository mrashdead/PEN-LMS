"""
Role-aware API permissions.

Django Groups remain useful for model permissions. These classes add the
business-level role and ownership checks that model permissions cannot express.
"""
from __future__ import annotations

from typing import Any

from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request
from rest_framework.views import View


class IsActiveUser(BasePermission):
    """Allow only authenticated, active and non-soft-deleted users."""

    message = "حساب کاربری شما فعال نیست یا غیرفعال شده است."

    def has_permission(self, request: Request, view: View) -> bool:
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and not getattr(user, "is_deleted", False)
        )


class HasAnyRole(BasePermission):
    """Allow users with at least one role listed on the view class attribute `required_roles`."""

    message = "شما مجوز دسترسی به این بخش را ندارید."

    def has_permission(self, request: Request, view: View) -> bool:
        roles = set(getattr(view, "required_roles", None) or ())
        if not roles:
            return True
        user = request.user
        return bool(user and user.is_authenticated and user.role_codes() & roles)


class IsManagerOrAdmin(BasePermission):
    """Allow institutional/process managers for management operations."""

    message = "فقط مدیر یا مدیر گردش کار مجاز به این عملیات است."
    allowed_roles = {"manager", "workflow_admin", "hr"}

    def has_permission(self, request: Request, view: View) -> bool:
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.role_codes() & self.allowed_roles
        )


class IsAcademicManager(BasePermission):
    """Read access for academic staff; write access for academic managers."""

    message = "شما مجوز این عملیات آموزشی را ندارید."
    read_roles = {"teacher", "manager", "workflow_admin", "hr", "employee"}
    write_roles = {"manager", "workflow_admin"}

    def has_permission(self, request: Request, view: View) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        roles = user.role_codes()
        return bool(roles & (self.read_roles if request.method in SAFE_METHODS else self.write_roles))


class IsWorkflowParticipant(BasePermission):
    """Require instance ownership/task participation, or an elevated role."""

    message = "شما به این درخواست دسترسی ندارید."
    elevated_roles = {"manager", "workflow_admin", "hr"}

    def has_permission(self, request: Request, view: View) -> bool:
        user = request.user
        return bool(user and user.is_authenticated)

    def has_object_permission(self, request: Request, view: View, obj: Any) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.role_codes() & self.elevated_roles:
            return True
        if getattr(obj, "requester_id", None) == user.pk:
            return True
        return obj.tasks.filter(assignee_id=user.pk).exists()


class IsPersonOwnerOrManager(BasePermission):
    """Allow reading visible people; restrict writes to owner or managers."""

    message = "شما مجاز به ویرایش اطلاعات این شخص نیستید."

    def has_permission(self, request: Request, view: View) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request: Request, view: View, obj: Any) -> bool:
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        if getattr(obj, "user_id", None) == user.pk:
            return True
        return bool(user.role_codes() & {"manager", "hr", "workflow_admin"})


class CanCreateUserForPerson(BasePermission):
    """Only HR and elevated managers can provision accounts."""

    message = "فقط مدیر، منابع انسانی یا مدیر گردش کار می‌تواند کاربر بسازد."

    def has_permission(self, request: Request, view: View) -> bool:
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.role_codes() & {"manager", "hr", "workflow_admin"}
        )


class CanManageWorkflow(BasePermission):
    """Only process managers can access workflow administration endpoints."""

    message = "شما مجوز مدیریت گردش کار را ندارید."

    def has_permission(self, request: Request, view: View) -> bool:
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.role_codes() & {"manager", "workflow_admin"}
        )


class CanAccessPersons(BasePermission):
    """Read own profile for end users; manage all profiles for staff."""

    message = "شما مجوز دسترسی به اطلاعات اشخاص را ندارید."
    elevated_roles = {"manager", "hr", "workflow_admin"}
    read_roles = elevated_roles | {"employee", "teacher", "student"}

    def has_permission(self, request: Request, view: View) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        roles = user.role_codes()
        if request.method in SAFE_METHODS:
            return bool(roles & self.read_roles)
        return bool(roles & self.elevated_roles)
