"""Django Group/model permissions used by API views.

Role permissions answer: «what kind of actor is this user?»
Group/model permissions answer: «what may this user do to this model?»
Sensitive endpoints should list both checks.
"""
from __future__ import annotations

from typing import Any

from rest_framework.permissions import BasePermission, DjangoModelPermissions
from rest_framework.request import Request
from rest_framework.views import View


class StrictDjangoModelPermissions(DjangoModelPermissions):
    """Django model permissions with read access requiring ``view_*`` and superuser bypass."""

    perms_map = {
        "GET": ["%(app_label)s.view_%(model_name)s"],
        "OPTIONS": [],
        "HEAD": [],
        "POST": ["%(app_label)s.add_%(model_name)s"],
        "PUT": ["%(app_label)s.change_%(model_name)s"],
        "PATCH": ["%(app_label)s.change_%(model_name)s"],
        "DELETE": ["%(app_label)s.delete_%(model_name)s"],
    }

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return super().has_permission(request, view)


class HasGroupPermission(BasePermission):
    """Check explicit model permissions declared on a view."""

    message = "گروه یا حساب شما مجوز لازم را ندارد."

    def has_permission(self, request: Request, view: View) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        required = getattr(view, "required_permissions", {})
        perms = required.get(request.method.upper(), required.get("*", []))
        return user.has_perms(perms) if perms else True


class GroupObjectPermission(BasePermission):
    """Object permission hook for views that require explicit group checks."""

    def has_permission(self, request: Request, view: View) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(
        self, request: Request, view: View, obj: Any
    ) -> bool:
        return True


__all__ = ["StrictDjangoModelPermissions", "HasGroupPermission", "GroupObjectPermission"]
