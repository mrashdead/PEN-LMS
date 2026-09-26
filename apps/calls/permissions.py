"""RBAC gate for the call-log surface."""
from __future__ import annotations

from rest_framework.permissions import BasePermission

from apps.calls.services import CALL_OPERATOR_ROLES, is_call_operator


class CanAccessCalls(BasePermission):
    """Operators log and follow up calls; managers additionally report."""

    message = "شما مجاز به دسترسی به ثبت تماس‌ها نیستید."

    def has_permission(self, request, view) -> bool:
        return is_call_operator(request.user)


__all__ = ["CALL_OPERATOR_ROLES", "CanAccessCalls"]
