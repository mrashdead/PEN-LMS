"""Filters for legacy groups that should not appear in the learner UI."""
from __future__ import annotations

from django.db.models import Q


_PARENT_GROUP_LABELS = (
    "والدین",
    "والدين",
    "گروه والدین",
    "گروه والدين",
    "ولی / والدین",
    "ولي / والدين",
    "والدین دانش‌آموزان",
    "والدين دانش آموزان",
    "parent",
    "parents",
    "guardian",
    "guardians",
)


def _normalized_group_name(value: str) -> str:
    return "".join(
        char for char in str(value or "").casefold().replace("ي", "ی").replace("ك", "ک")
        if not char.isspace() and char not in "\u200c\u200f/\\_-"
    )


_PARENT_GROUP_KEYS = {_normalized_group_name(label) for label in _PARENT_GROUP_LABELS}


def is_parent_portal_group(name: str) -> bool:
    """Whether a group is a legacy parent/guardian portal group."""
    return _normalized_group_name(name) in _PARENT_GROUP_KEYS


def visible_group_queryset(queryset):
    """Filter legacy parent groups in SQL before related permission data loads."""
    condition = Q()
    for label in _PARENT_GROUP_LABELS:
        condition |= Q(name__iexact=label)
    return queryset.exclude(condition)
