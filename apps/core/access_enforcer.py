"""
Access enforcer — لایه‌ی تصمیم‌گیری نهایی برای PersonACL.

قواعد (Horsitai حک beaut گرفته از سازمان تصمیم):
  • superuser → همیشه مجاز.
  • اگر ردیف PersonACLEntry برای (user, type, key) زنده وجود داشته باشد
    → تصمیم همان لیست فعل‌های ردیف است (گرینت صریح).
  • اگر ردیف نباشد → None برمی‌گردانیم تا کالر نقش/گروه فعلی (baseline) ادامه یابد.
"""
from __future__ import annotations

from typing import Any

from apps.org.models import PersonACLEntry, ACLEntryType

#: verbهای هر نوع منبع (fallback وقتی کلید ناشناخته است) — از catalog می‌آید.
from apps.core.access_catalog import valid_verbs


def acl_allows(
    user: Any,
    resource_type: str,
    resource_key: str,
    verb: str,
) -> bool | None:
    """
    Decide explicit-ACL access for ``verb`` on ``(resource_type, resource_key)``.

    Returns:
      True      → explicitly granted
      False     → explicitly present but verb not in list (denied)
      None      → no ACL entry → caller falls back to role/group baseline
    """
    if user is None or not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True

    entry = (
        PersonACLEntry.objects.filter(
            user=user,
            resource_type=resource_type,
            resource_key=resource_key,
            is_deleted=False,
        )
        .only("verbs")
        .first()
    )
    if entry is None:
        return None
    return verb in (entry.verbs or [])


def acl_verbs_for(user: Any, resource_type: str, resource_key: str) -> set[str] | None:
    """
    Return the explicit verbs set if an ACL entry exists, else None.

    Useful when the caller needs the whole set (e.g. UI label), not a single verb.
    """
    if user is None or not getattr(user, "is_authenticated", False):
        return set()
    if getattr(user, "is_superuser", False):
        return valid_verbs(resource_type, resource_key)
    entry = PersonACLEntry.objects.filter(
        user=user,
        resource_type=resource_type,
        resource_key=resource_key,
        is_deleted=False,
    ).only("verbs").first()
    if entry is None:
        return None
    return set(entry.verbs or [])


def acl_strict(
    user: Any,
    resource_type: str,
    resource_key: str,
    verb: str,
    baseline: bool,
) -> bool:
    """
    Convenience: explicit ACL if present, otherwise use given baseline result.

    This is the single call sites use when they have already computed the
    role/group-baseline decision (``baseline``) and just need to layer ACL on top.
    """
    decision = acl_allows(user, resource_type, resource_key, verb)
    if decision is not None:
        return decision
    return baseline
