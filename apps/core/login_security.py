"""Cache-backed guard for the browser login form.

DRF's ``login`` throttle only protects API views. The dashboard login is a
normal Django form, so it needs an explicit guard at the form boundary too.
"""
from __future__ import annotations

import hashlib

from django.core.cache import cache


RATE_LIMIT = 5
RATE_WINDOW_SECONDS = 60
FAILURE_LIMIT = 10
FAILURE_WINDOW_SECONDS = 15 * 60
LOCK_SECONDS = 15 * 60


def _fingerprint(username: str, ip_address: str) -> str:
    raw = f"{username.strip().lower()}|{ip_address.strip()}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _keys(username: str, ip_address: str) -> tuple[str, str, str]:
    fingerprint = _fingerprint(username, ip_address)
    return (
        f"pen:login:rate:{fingerprint}",
        f"pen:login:failures:{fingerprint}",
        f"pen:login:lock:{fingerprint}",
    )


def client_ip(request) -> str:
    # Do not trust spoofable X-Forwarded-For in this security decision.
    return request.META.get("REMOTE_ADDR", "unknown") or "unknown"


def state(request, username: str) -> dict[str, int | bool]:
    rate_key, failure_key, lock_key = _keys(username, client_ip(request))
    return {
        "locked": bool(cache.get(lock_key)),
        "rate_count": int(cache.get(rate_key) or 0),
        "failure_count": int(cache.get(failure_key) or 0),
    }


def blocked(request, username: str) -> str | None:
    current = state(request, username)
    if current["locked"]:
        return "به‌دلیل چند ورود ناموفق، حساب ورود شما موقتاً قفل شده است. ۱۵ دقیقه بعد دوباره تلاش کنید."
    if current["rate_count"] >= RATE_LIMIT:
        return "تعداد تلاش‌های ورود بیش از حد مجاز است. یک دقیقه بعد دوباره تلاش کنید."
    return None


def record_failure(request, username: str) -> None:
    if not username.strip():
        return
    rate_key, failure_key, lock_key = _keys(username, client_ip(request))
    cache.add(rate_key, 0, RATE_WINDOW_SECONDS)
    rate_count = cache.incr(rate_key)
    cache.add(failure_key, 0, FAILURE_WINDOW_SECONDS)
    failure_count = cache.incr(failure_key)
    if failure_count >= FAILURE_LIMIT:
        cache.set(lock_key, True, LOCK_SECONDS)
    if rate_count < 0:  # pragma: no cover - defensive for unusual backends
        cache.set(rate_key, 1, RATE_WINDOW_SECONDS)


def clear_failures(request, username: str) -> None:
    rate_key, failure_key, lock_key = _keys(username, client_ip(request))
    cache.delete_many([rate_key, failure_key, lock_key])
