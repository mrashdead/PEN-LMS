"""
Playhouse API permissions.

Operators are institutional staff — anyone holding a staff/management role
(employee, supervisor, manager, hr, workflow_admin) may run the playhouse
front desk. Finance write actions additionally require manager-level roles.
"""
from __future__ import annotations

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import View

#: Roles allowed to operate the playhouse front desk.
OPERATOR_ROLES = {"employee", "supervisor", "manager", "hr", "workflow_admin"}
#: Roles allowed to mark invoices paid (finance-sensitive).
FINANCE_ROLES = {"manager", "hr", "workflow_admin"}
PRICE_EDITOR_ROLES = FINANCE_ROLES | {"supervisor"}


class IsPlayhouseOperator(BasePermission):
    """Authenticated, active staff who may run the playhouse desk."""

    message = "فقط پرسنل مجموعه می‌توانند از خانه بازی استفاده کنند."

    def has_permission(self, request: Request, view: View) -> bool:
        user = request.user
        if not (user and user.is_authenticated and user.is_active):
            return False
        roles = user.role_codes() if hasattr(user, "role_codes") else set()
        return bool(roles & OPERATOR_ROLES)


class IsPlayhouseFinance(BasePermission):
    """Manager-level roles only — for payment/void actions."""

    message = "فقط مدیران می‌توانند پرداخت را ثبت کنند."

    def has_permission(self, request: Request, view: View) -> bool:
        user = request.user
        if not (user and user.is_authenticated and user.is_active):
            return False
        roles = user.role_codes() if hasattr(user, "role_codes") else set()
        return bool(roles & FINANCE_ROLES)
