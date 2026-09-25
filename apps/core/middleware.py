from __future__ import annotations

import contextvars
import logging
import re
import time
import uuid


_request_id = contextvars.ContextVar("request_id", default="-")
_UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-8][0-9a-fA-F]{3}-[89aAbB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$")
_logger = logging.getLogger("apps.http")


class RequestIDLogFilter(logging.Filter):
    """Add the active request ID to every console log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id.get()
        return True


class RequestIDMiddleware:
    """Propagate a validated request ID through logs and the response header."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        supplied = request.headers.get("X-Request-ID", "")
        request_id = str(uuid.UUID(supplied)) if _UUID_RE.fullmatch(supplied) else str(uuid.uuid4())
        token = _request_id.set(request_id)
        request.request_id = request_id
        started = time.perf_counter()
        try:
            response = self.get_response(request)
            response["X-Request-ID"] = request_id
            level = logging.ERROR if response.status_code >= 500 else logging.INFO
            _logger.log(
                level,
                "http_request status=%s method=%s route=%s duration_ms=%.1f",
                response.status_code,
                request.method,
                getattr(getattr(request, "resolver_match", None), "url_name", None) or "unmatched",
                (time.perf_counter() - started) * 1000,
            )
            return response
        finally:
            _request_id.reset(token)
