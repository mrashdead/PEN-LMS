"""Lifecycle policy for role codes.

Legacy roles remain readable for backward compatibility, but must not be
offered or assigned to new users while their migration is pending.
"""
from __future__ import annotations


LEGACY_ROLE_CODES = frozenset({"hr"})


def normalize_role_code(code: str) -> str:
    return (code or "").strip().lower()


def is_legacy_role(code: str) -> bool:
    return normalize_role_code(code) in LEGACY_ROLE_CODES
