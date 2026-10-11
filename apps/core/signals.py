"""Authentication event hooks for the security audit log."""
from __future__ import annotations

from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver


@receiver(user_logged_in, dispatch_uid="core.audit_successful_session_login")
def audit_successful_session_login(sender, request, user, **kwargs):
    """Record successful session logins from dashboard, admin, and other views."""
    from apps.core.models import AuditEvent

    AuditEvent.record(
        kind=AuditEvent.Kind.LOGIN,
        summary="ورود موفق کاربر به سامانه.",
        actor=user,
        obj=user,
        request=request,
        metadata={
            "method": getattr(request, "method", None),
            "path": getattr(request, "path", None),
        },
    )


@receiver(user_logged_out, dispatch_uid="core.audit_successful_session_logout")
def audit_successful_session_logout(sender, request, user, **kwargs):
    """Record successful session logout events."""
    from apps.core.models import AuditEvent

    AuditEvent.record(
        kind=AuditEvent.Kind.LOGOUT,
        summary="خروج موفق کاربر از سامانه.",
        actor=user,
        obj=user,
        request=request,
        metadata={
            "method": getattr(request, "method", None),
            "path": getattr(request, "path", None),
        },
    )
