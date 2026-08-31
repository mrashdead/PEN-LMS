from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional, Union
from uuid import UUID

from django.conf import settings

if TYPE_CHECKING:
    from apps.workflow.models import Instance

logger = logging.getLogger(__name__)


class GuardDeniedError(Exception):
    """Raised when a guard condition blocks a transition."""


class GuardEvaluator:
    """
    Evaluates guard expressions stored in Transition.guard_expression.

    Supported guard types (documented in Transition.guard_expression help_text):

    - ``{"type": "always_true"}`` — always allow (default for empty/{}).
    - ``{"type": "role_not_in", "roles": ["manager"], "field": "requester"}`` —
      Deny if the value of ``instance.<field>`` (e.g. ``instance.requester``) has
      *any* of the listed role codes.
    - ``{"type": "field_equals", "field": "amount", "value": 1000}`` —
      Compare ``instance.<field>`` == ``value``. Default path is ``instance``.
    - ``{"type": "field_not_equals", "field": "requester_id", "source": "actor.id"}`` —
      Compare ``instance.<field>`` != ``<source_path>``. If source starts with
      ``actor.`` it reads from the actor (user).
    - ``{"type": "entity_field_lt", "field": "enrolled_count", "other_field": "capacity"}`` —
      Compare two fields on the *linked domain entity* (via EntityWorkflow).
      Requires an active EntityWorkflow link.
    - ``{"type": "all", "guards": [...]}`` — every sub-guard must pass.
    - ``{"type": "any", "guards": [...]}`` — at least one sub-guard must pass.

    Rules:
    - Unknown type → **fail closed (deny)** — never silently allow.
    - Empty ``{}`` → always_true.
    - If a required field or path does not exist → deny.
    - Evaluator is pure: no writes, no side-effects.
    """

    def evaluate(
        self,
        guard: dict[str, Any],
        instance: Instance,
        actor: settings.AUTH_USER_MODEL,  # type: ignore[valid-type]
    ) -> tuple[bool, str]:
        """
        Returns (allowed: bool, reason: str).
        ``allowed=True`` means the transition may proceed.
        """
        guard_type = guard.get("type", "always_true")

        handler = getattr(self, f"_handle_{guard_type}", None)
        if handler is None:
            logger.warning("Unknown guard type: %s — denying", guard_type)
            return False, f"Unknown guard type '{guard_type}' (denied by policy)."

        try:
            return handler(guard, instance, actor)
        except Exception as e:
            logger.exception("Guard evaluation error: %s", e)
            return False, f"Guard evaluation error: {e}"

    # ------------------------------------------------------------------
    #  Handlers
    # ------------------------------------------------------------------

    def _handle_always_true(
        self, guard: dict[str, Any], instance: Instance,
        actor: settings.AUTH_USER_MODEL,
    ) -> tuple[bool, str]:
        return True, ""

    def _handle_role_not_in(
        self, guard: dict[str, Any], instance: Instance,
        actor: settings.AUTH_USER_MODEL,
    ) -> tuple[bool, str]:
        """
        Deny if ``instance.<field>`` (a User) has any of the listed roles.
        Example: {"type": "role_not_in", "roles": ["manager"], "field": "requester"}
        Means: if the requester has "manager" role → deny.
        """
        roles: list[str] = guard.get("roles", [])
        field: str = guard.get("field", "")
        if not roles or not field:
            return False, "role_not_in: missing 'roles' or 'field'."

        target_user = self._resolve_field(instance, field)
        if target_user is None:
            return False, f"role_not_in: field '{field}' not found or not a User."

        try:
            user_roles = target_user.role_codes()
        except AttributeError:
            return False, f"role_not_in: field '{field}' has no role_codes()."

        for role in roles:
            if role in user_roles:
                return False, (
                    f"User '{getattr(target_user, 'username', target_user)}' "
                    f"has role '{role}' — transition denied."
                )
        return True, ""

    def _handle_field_equals(
        self, guard: dict[str, Any], instance: Instance,
        actor: settings.AUTH_USER_MODEL,
    ) -> tuple[bool, str]:
        """
        Compare instance.<field> == value.
        """
        field: str = guard.get("field", "")
        expected: Any = guard.get("value")
        if not field:
            return False, "field_equals: missing 'field'."

        actual = self._resolve_field(instance, field)
        if actual is None and expected is not None:
            return False, f"field_equals: field '{field}' not found."

        if str(actual) != str(expected):
            return False, (
                f"field_equals: expected '{expected}', got '{actual}'."
            )
        return True, ""

    def _handle_field_not_equals(
        self, guard: dict[str, Any], instance: Instance,
        actor: settings.AUTH_USER_MODEL,
    ) -> tuple[bool, str]:
        """
        Compare instance.<field> != <source>.
        source can be "actor.id", "actor.username", instance.field_path, etc.
        Source is resolved from actor (if starts with "actor.") or from instance.
        """
        field: str = guard.get("field", "")
        source_path: str = guard.get("source", "")
        if not field or not source_path:
            return False, "field_not_equals: missing 'field' or 'source'."

        lhs = self._resolve_field(instance, field)
        rhs = self._resolve_source(source_path, instance, actor)

        if lhs is None and rhs is not None:
            return False, f"field_not_equals: field '{field}' not found."
        if rhs is None:
            return False, f"field_not_equals: source '{source_path}' not found."

        if str(lhs) == str(rhs):
            return False, (
                f"field_not_equals: '{field}' == '{source_path}' "
                f"(both '{lhs}') — transition denied."
            )
        return True, ""

    def _handle_entity_field_lt(
        self, guard: dict[str, Any], instance: Instance,
        actor: settings.AUTH_USER_MODEL,
    ) -> tuple[bool, str]:
        """
        Compare two fields on the *linked domain entity* via EntityWorkflow.
        entity.<field> < entity.<other_field>.
        Example: enrolled_count < capacity → allow.
        """
        field: str = guard.get("field", "")
        other_field: str = guard.get("other_field", "")
        if not field or not other_field:
            return False, "entity_field_lt: missing 'field' or 'other_field'."

        entity = self._get_linked_entity(instance)
        if entity is None:
            return False, "entity_field_lt: no linked entity found."

        lhs = getattr(entity, field, None)
        rhs = getattr(entity, other_field, None)
        if lhs is None:
            return False, f"entity_field_lt: field '{field}' not on entity."
        if rhs is None:
            return False, f"entity_field_lt: field '{other_field}' not on entity."

        try:
            lhs_val, rhs_val = float(lhs), float(rhs)
        except (ValueError, TypeError):
            return False, f"entity_field_lt: non-numeric fields ({lhs}, {rhs})."

        if not (lhs_val < rhs_val):
            return False, (
                f"entity_field_lt: '{field}' ({lhs_val}) is not less than "
                f"'{other_field}' ({rhs_val})."
            )
        return True, ""

    def _handle_all(
        self, guard: dict[str, Any], instance: Instance,
        actor: settings.AUTH_USER_MODEL,
    ) -> tuple[bool, str]:
        sub_guards: list[dict] = guard.get("guards", [])
        if not sub_guards:
            return True, ""
        for sub in sub_guards:
            ok, msg = self.evaluate(sub, instance, actor)
            if not ok:
                return False, f"all-guard failed: {msg}"
        return True, ""

    def _handle_any(
        self, guard: dict[str, Any], instance: Instance,
        actor: settings.AUTH_USER_MODEL,
    ) -> tuple[bool, str]:
        sub_guards: list[dict] = guard.get("guards", [])
        if not sub_guards:
            return True, ""
        errors: list[str] = []
        for sub in sub_guards:
            ok, msg = self.evaluate(sub, instance, actor)
            if ok:
                return True, ""
            errors.append(msg)
        return False, f"any-guard: no sub-guard passed: {'; '.join(errors)}"

    # ------------------------------------------------------------------
    #  Helpers
    # ------------------------------------------------------------------

    def _resolve_field(
        self,
        obj: Any,
        field_path: str,
    ) -> Any:
        """Resolve a dotted field path on an object (e.g. ``requester.id``)."""
        parts = field_path.split(".")
        current = obj
        for part in parts:
            try:
                current = getattr(current, part)
            except AttributeError:
                return None
            if callable(current):
                current = current()
        return current

    def _resolve_source(
        self,
        source_path: str,
        instance: Instance,
        actor: settings.AUTH_USER_MODEL,
    ) -> Any:
        """Resolve source: ``actor.<attr>`` → attribute on actor; else instance."""
        if source_path.startswith("actor."):
            attr = source_path[len("actor."):]
            return getattr(actor, attr, None)
        return self._resolve_field(instance, source_path)

    def _get_linked_entity(
        self,
        instance: Instance,
    ) -> Any:
        """
        Return the first domain entity linked via EntityWorkflow.
        Uses instance.entity_links (prefetch-friendly).
        """
        try:
            links = instance.entity_links.all()
        except AttributeError:
            return None
        for link in links:
            try:
                entity = link.entity
                if entity is not None:
                    return entity
            except Exception:
                continue
        return None