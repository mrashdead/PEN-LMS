"""
ACL business logic — granting, revoking, querying PersonACLEntry.

All write operations are atomic and lock the target row to prevent concurrent
updates from clobbering each other.
"""
from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import QuerySet

from apps.core.access_catalog import (
    catalog_entry,
    catalog_for_type,
    valid_verbs,
)
from apps.org.models import ACLEntryType, ACLVerb, PersonACLEntry

User = get_user_model()


# ── Query helpers ─────────────────────────────────────────────────────────────

def user_directory(q: str = "") -> list[dict[str, Any]]:
    """Staff users for the picker — search by name / username / department."""
    from django.db.models import Q
    qs = (
        User.objects.filter(is_active=True, is_deleted=False)
        .select_related("person")
        .order_by("first_name", "last_name")
    )
    q = (q or "").strip()
    if q:
        qs = qs.filter(
            Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(username__icontains=q)
            | Q(person__department__icontains=q)
        )
    rows = []
    for u in qs[:100]:
        person = getattr(u, "person", None)
        name = " ".join(n for n in (u.first_name, u.last_name) if n) or u.username
        roles = []
        try:
            roles = list(u.role_codes())
        except Exception:
            roles = []
        rows.append({
            "id": str(u.pk),
            "name": name,
            "username": u.username,
            "department": getattr(person, "department", "") if person else u.department or "",
            "is_superuser": bool(u.is_superuser),
            "roles": roles,
        })
    return rows


def user_acl_full(user: User) -> dict[str, Any]:
    """
    Full ACL detail for one user: identity + superuser flag + all explicit
    entries (user_acl_map), serialized.
    """
    person = getattr(user, "person", None)
    name = " ".join(n for n in (user.first_name, user.last_name) if n) or user.username
    return {
        "id": str(user.pk),
        "name": name,
        "username": user.username,
        "department": getattr(person, "department", "") if person else user.department or "",
        "is_superuser": bool(user.is_superuser),
        "roles": list(user.role_codes()) if hasattr(user, "role_codes") else [],
        "entries": [entry_serialize(e) for e in acl_entries_for(user)],
    }


def acl_entries_for(user: User) -> QuerySet[PersonACLEntry]:
    return (
        PersonACLEntry.objects.filter(user=user, is_deleted=False)
        .order_by("resource_type", "resource_key")
    )


def user_acl_map(user: User) -> dict[tuple[str, str], PersonACLEntry]:
    """Mapping (resource_type, resource_key) -> entry, to serialize all rows."""
    return {(e.resource_type, e.resource_key): e for e in acl_entries_for(user)}


def entry_serialize(entry: PersonACLEntry) -> dict[str, Any]:
    return {
        "id": str(entry.pk),
        "resource_type": entry.resource_type,
        "resource_key": entry.resource_key,
        "verbs": list(entry.verbs or []),
        "granted_by": (
            {"id": str(entry.granted_by_id)} if entry.granted_by_id else None
        ),
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
    }


# ── Catalog-facing helpers ────────────────────────────────────────────────────

def catalog(user=None) -> dict[str, Any]:
    """
    Build the full catalog for the UI grid: pages + models + dynamic forms.
    Each entry: {key, title, category, verbs, description}.
    """
    pages = [
        {
            "key": r.key,
            "title": r.title,
            "category": r.category,
            "verbs": list(r.verbs),
            "description": r.description,
        }
        for r in catalog_for_type("page")
    ]
    models = [
        {
            "key": r.key,
            "title": r.title,
            "category": r.category,
            "verbs": list(r.verbs),
            "description": getattr(r, "description", ""),
        }
        for r in catalog_for_type("model")
    ]
    forms = form_catalog()
    return {
        "pages": pages,
        "forms": forms,
        "models": models,
        "verbs": {
            "view": "مشاهده",
            "add": "ایجاد",
            "change": "ویرایش",
            "delete": "حذف",
            "submit": "ارسال",
            "approve": "تأیید",
            "reject": "رد",
        },
    }


def form_catalog() -> list[dict[str, Any]]:
    """Dynamic form resources from FormSchema table."""
    from apps.forms.models import FormSchema
    return [
        {
            "key": s.slug,
            "title": s.title,
            "category": "form",
            "verbs": list(valid_verbs("form", s.slug)),
            "description": s.description or "",
        }
        for s in FormSchema.objects.filter(is_active=True, is_deleted=False)
        .order_by("title")
        .only("slug", "title", "description")
    ]


# ── Write helpers (atomic + locked) ───────────────────────────────────────────

@transaction.atomic
def grant_verbs(
    user: User,
    resource_type: str,
    resource_key: str,
    verbs: list[str],
    actor: User,
) -> PersonACLEntry:
    """
    Set the explicit verb list for (user, type, key).

    - Unknown (type,key): reject (caller must validate) — validates here too.
    - Empty verbs: treat as revoke (delete the row).
    - Row locked via select_for_update to prevent concurrent clobbering.
    """
    catalog = catalog_entry(resource_type, resource_key)
    if catalog is None:
        raise ValueError(f"منبع نامعتبر: {resource_type}:{resource_key}")

    allowed = set(valid_verbs(resource_type, resource_key)) | set(ACLVerb.values)
    cleaned = sorted({v for v in verbs if v in allowed})

    if not cleaned:
        # empty → revoke
        revoke(user, resource_type, resource_key, actor)
        return None

    obj, created = PersonACLEntry.objects.select_for_update().get_or_create(
        user=user,
        resource_type=resource_type,
        resource_key=resource_key,
        defaults={"verbs": cleaned, "granted_by": actor},
        is_deleted=False,
    )
    if created:
        return obj
    obj.verbs = cleaned
    obj.granted_by = actor
    obj.revoked_at = None
    obj.revoked_by = None
    obj.save(update_fields=["verbs", "granted_by", "revoked_at", "revoked_by"])
    return obj


@transaction.atomic
def revoke(
    user: User,
    resource_type: str,
    resource_key: str,
    actor: User,
) -> bool:
    """
    Soft-delete the ACL entry for (user, type, key), recording the actor.
    Returns True if a live entry was removed.
    """
    entry = (
        PersonACLEntry.objects.select_for_update()
        .filter(
            user=user,
            resource_type=resource_type,
            resource_key=resource_key,
            is_deleted=False,
        )
        .first()
    )
    if entry is None:
        return False
    from django.utils import timezone

    entry.is_deleted = True
    entry.revoked_at = timezone.now()
    entry.revoked_by = actor
    entry.save(update_fields=["is_deleted", "revoked_at", "revoked_by"])
    return True


# ── Validation ────────────────────────────────────────────────────────────────

def validate_grant_payload(payload: dict[str, Any]) -> tuple[str, str, list[str]]:
    """Parse + validate a grant payload → (type, key, verbs). Raises ValueError."""
    resource_type = str(payload.get("resource_type", "")).strip()
    resource_key = str(payload.get("resource_key", "")).strip()
    verbs = payload.get("verbs", []) or []
    if not isinstance(verbs, list):
        raise ValueError("verbs باید لیست باشد.")
    verbs = [str(v).strip() for v in verbs]

    if resource_type not in {t.value for t in ACLEntryType}:
        raise ValueError("resource_type نامعتبر است.")
    if not resource_key:
        raise ValueError("resource_key الزامی است.")
    invalid = [v for v in verbs if v not in ACLVerb.values]
    if invalid:
        raise ValueError(f"فعل ناشناخته: {', '.join(invalid)}")
    return resource_type, resource_key, verbs
