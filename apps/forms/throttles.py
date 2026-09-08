"""Scoped DRF throttles for the forms write endpoints."""
from __future__ import annotations

from rest_framework.throttling import UserRateThrottle


class FormWriteThrottle(UserRateThrottle):
    """
    Authenticated-user throttle for form writes.

    Registered under the ``form_write`` scope in REST_FRAMEWORK settings
    (30/minute). Applied only to write actions so read browsing is unaffected.
    """

    scope = "form_write"
