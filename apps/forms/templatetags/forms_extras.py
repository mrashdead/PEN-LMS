"""Small helpers for rendering dynamic form fields in Django templates.

``normalize_field`` merges the two accepted schema shapes (top-level flat
keys such as ``min_length``/``max``/``accept`` and the catalog's nested
``validators: {min_length: …, max_value: …, allowed_extensions: […]}``)
into one canonical dict the templates can rely on. The rules mirror
``apps/forms/schema_validation._validators_block`` (source of truth) so the
UI never diverges from the server.
"""
from __future__ import annotations

import json

from django import template

register = template.Library()


@register.filter
def get_item(mapping, key):
    """dict lookup by a variable key: {{ row|get_item:col.key }}."""
    try:
        if isinstance(mapping, dict):
            return mapping.get(key)
        return None
    except Exception:  # pragma: no cover - template safety net
        return None


@register.filter
def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


#: Maps nested ``validators`` keys to the flat key the templates read.
_VALIDATOR_ALIAS = {
    "min_length": "min_length",
    "max_length": "max_length",
    "min_value": "min",
    "max_value": "max",
    "regex": "pattern",
    "allowed_extensions": "accept",
    "max_file_size": "max_file_size",
    "allowed_mime_types": "mime_types",
}


@register.filter
def normalize_field(field):
    """
    Return a shallow-copied field definition with ``validators`` merged into
    the flat keys. Never mutate the caller's dict (schema JSON is shared).
    """
    if not isinstance(field, dict):
        return {}
    merged = dict(field)
    nested = field.get("validators")
    if isinstance(nested, dict):
        for nested_key, flat_key in _VALIDATOR_ALIAS.items():
            if flat_key not in merged and nested_key in nested:
                merged[flat_key] = nested[nested_key]

    # Normalise `accept` (may be ["pdf"] or [".pdf"]) to dotted, unique list.
    accept = merged.get("accept")
    if isinstance(accept, list):
        normalized = []
        for raw in accept:
            text = str(raw).strip().lower()
            if not text:
                continue
            if not text.startswith("."):
                text = f".{text}"
            if text not in normalized:
                normalized.append(text)
        merged["accept"] = normalized

    # Django template tags can't test `is not None`, so expose presence flags
    # for numeric bounds (0 is a valid bound we must still render).
    merged["has_min"] = merged.get("min") is not None
    merged["has_max"] = merged.get("max") is not None
    return merged


@register.filter
def to_json(value):
    """
    Serialize a Python value to JSON.

    We intentionally do NOT mark the result safe — Django's template
    auto-escaping converts the double quotes to &quot; which is what we
    want when embedding in ``data-x="{{ …|to_json }}"``. JS then reads
    ``el.dataset.x`` (already-decoded) and JSON.parses it.
    """
    try:
        return json.dumps(value, ensure_ascii=False)
    except (TypeError, ValueError):
        return "null"


#: url_names of every forms page — single source of truth for the sidebar's
#: active-state highlighting (see pen-templates/partials/sidebar.html).
FORMS_URL_NAMES = {
    "submission-list",
    "submission-picker",
    "submission-create",
    "submission-detail-page",
    "submission-edit-page",
}


@register.filter
def is_forms_url(url_name):
    """True when the current url_name belongs to the forms section."""
    return url_name in FORMS_URL_NAMES


@register.filter
def in_list(value, comma_separated):
    """Membership test for templates: {{ urlname|in_list:"a,b,c" }}."""
    return value in [item.strip() for item in comma_separated.split(",") if item.strip()]


#: Persian labels for the six submission statuses (models.py keeps English
#: TextChoices — we translate only in the presentation layer).
STATUS_LABELS_FA = {
    "draft": "پیش‌نویس",
    "submitted": "ارسال‌شده",
    "processing": "در حال بررسی",
    "approved": "تأییدشده",
    "rejected": "ردشده",
    "archived": "بایگانی",
}


@register.filter
def status_label(status):
    """Persian label for a submission status code (falls back to the code)."""
    return STATUS_LABELS_FA.get(status, status)
