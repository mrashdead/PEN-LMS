"""Small helpers for rendering dynamic form fields in Django templates."""
from __future__ import annotations

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
