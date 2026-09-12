"""
Global DRF exception handler — surfaces the standard DRF error shape AND
records a queryable AuditEvent for every denial (§13-4).

Configured via REST_FRAMEWORK["EXCEPTION_HANDLER"]. It never changes response
semantics; audit failures are swallowed so a broken audit table can never turn
a 403 into a 500.
"""
from __future__ import annotations

import logging

from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


def audited_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    try:
        if response is not None and response.status_code in (403, 404):
            from apps.core.models import AuditEvent
            from apps.core.utils import get_client_ip

            request = context.get("request")
            view = context.get("view")
            actor = getattr(request, "user", None)
            if actor is not None and not getattr(actor, "is_authenticated", False):
                actor = None
            # 404 is only interesting on authenticated access to a scoped
            # object (a probe); 403 always. Both are cheap to record.
            AuditEvent.objects.create(
                kind=(
                    AuditEvent.Kind.ACCESS_DENIED
                    if response.status_code == 403
                    else AuditEvent.Kind.SENSITIVE_READ
                ),
                actor_id=getattr(actor, "pk", None),
                summary=(
                    f"{'دسترسی رد شد' if response.status_code == 403 else 'یافت نشد'}"
                    f" — {type(view).__name__ if view else '?'}"
                ),
                metadata={
                    "status": response.status_code,
                    "method": getattr(request, "method", None),
                    "path": getattr(request, "path", None),
                    "view": type(view).__name__ if view else None,
                },
                ip_address=get_client_ip(request) if request else None,
            )
    except Exception:  # noqa: BLE001 — audit must never break the response
        logger.exception("exception_handler audit write failed")
    return response
