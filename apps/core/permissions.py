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

from apps.core.crud import (
    can_create_resource,
    can_delete_resource,
    can_edit_resource,
    can_restore_resource,
    can_view_resource,
)


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
    read_roles = {"teacher", "manager", "workflow_admin", "hr", "employee", "supervisor"}
    write_roles = {"manager", "workflow_admin", "supervisor"}

    def has_permission(self, request: Request, view: View) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        roles = user.role_codes()
        return bool(roles & (self.read_roles if request.method in SAFE_METHODS else self.write_roles))


class IsTeacherPortalUser(BasePermission):
    """Teacher-portal writes: the teacher role itself, or any manager tier.

    ``IsAcademicManager`` refuses every non-safe method to a plain teacher
    (its write trio is {manager, workflow_admin}), yet the whole point of the
    teacher panel is that a teacher WRITES attendance and report cards for
    their OWN classes. Row ownership (instructor == their Person, or elevated
    role) is checked per-object inside those views — the role class only says
    "this actor may use the teacher-portal verbs at all".
    """

    message = "این بخش فقط برای مدرس یا مدیر سامانه است."
    allowed_roles = {"teacher", "manager", "workflow_admin", "hr"}

    def has_permission(self, request: Request, view: View) -> bool:
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.role_codes() & self.allowed_roles
        )


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
        return can_edit_resource(user, obj, "persons")


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


class ResourceCRUDPermission(BasePermission):
    """Final object-aware gate shared by CRUD and POST soft-delete views."""

    message = "شما مجوز این عملیات روی این رکورد را ندارید."

    def _resource(self, view, obj=None):
        return getattr(view, "resource_key", None)

    def has_permission(self, request: Request, view: View) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        resource = self._resource(view)
        if getattr(view, "restore_action", False):
            return can_restore_resource(user, getattr(view, "queryset", None).model if getattr(view, "queryset", None) else None)
        if getattr(view, "soft_delete_action", False):
            return bool(user.is_superuser or user.role_codes() & {"manager", "workflow_admin", "hr", "supervisor"})
        if request.method in SAFE_METHODS:
            return True
        if request.method == "POST":
            return can_create_resource(user, resource or "")
        return True

    def has_object_permission(self, request: Request, view: View, obj: Any) -> bool:
        resource = self._resource(view)
        if getattr(view, "restore_action", False):
            return can_restore_resource(request.user, obj)
        if getattr(view, "soft_delete_action", False) or request.method == "DELETE":
            return can_delete_resource(request.user, obj, resource)
        if request.method in SAFE_METHODS:
            return can_view_resource(request.user, obj, resource)
        return can_edit_resource(request.user, obj, resource)
