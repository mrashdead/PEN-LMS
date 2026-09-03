from __future__ import annotations

from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.workflow.guards import GuardEvaluator
from apps.workflow.models import Instance

User = get_user_model()


class _MockUser:
    def __init__(self, roles: set[str], pk="actor-uuid", username="actor"):
        self.pk = pk
        self.id = pk
        self._roles = roles
        self.username = username

    def role_codes(self) -> set[str]:
        return self._roles


class _MockEntity:
    """Minimal mock for a linked domain entity (e.g. CourseOffering)."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class GuardEvaluatorTestCase(TestCase):
    """Pure unit tests — no DB required."""

    def setUp(self):
        self.evaluator = GuardEvaluator()
        self.actor = _MockUser({"employee", "manager"}, pk="actor-1", username="ali")
        self.instance = MagicMock(spec=Instance)
        self.instance.pk = "instance-uuid"
        self.instance.id = self.instance.pk
        self.instance.requester = _MockUser({"employee"}, pk="requester-1", username="reza")
        self.instance.requester_id = self.instance.requester.pk

    # ─── always_true ───

    def test_always_true_allows(self):
        ok, msg = self.evaluator.evaluate({"type": "always_true"}, self.instance, self.actor)
        self.assertTrue(ok)

    def test_empty_dict_allows(self):
        ok, msg = self.evaluator.evaluate({}, self.instance, self.actor)
        self.assertTrue(ok)

    # ─── unknown type (fail closed) ───

    def test_unknown_type_denies(self):
        ok, msg = self.evaluator.evaluate({"type": "banana"}, self.instance, self.actor)
        self.assertFalse(ok)
        self.assertIn("طبق سیاست", msg)

    # ─── role_not_in ───

    def test_role_not_in_denies_when_user_has_role(self):
        guard = {"type": "role_not_in", "roles": ["manager"], "field": "requester"}
        ok, msg = self.evaluator.evaluate(guard, self.instance, self.actor)
        # instance.requester has {"employee"} roles, NOT manager → should allow
        self.assertTrue(ok)

    def test_role_not_in_denies_matching_role(self):
        # Give requester the "manager" role
        self.instance.requester = _MockUser({"employee", "manager"}, pk="requester-1")
        guard = {"type": "role_not_in", "roles": ["manager"], "field": "requester"}
        ok, msg = self.evaluator.evaluate(guard, self.instance, self.actor)
        self.assertFalse(ok)
        self.assertIn("نقش 'manager'", msg)

    def test_role_not_in_missing_field(self):
        guard = {"type": "role_not_in", "roles": ["manager"], "field": "nonexistent"}
        ok, msg = self.evaluator.evaluate(guard, self.instance, self.actor)
        self.assertFalse(ok)

    # ─── field_equals ───

    def test_field_equals_matches(self):
        guard = {"type": "field_equals", "field": "requester_id", "value": "requester-1"}
        ok, msg = self.evaluator.evaluate(guard, self.instance, self.actor)
        self.assertTrue(ok)

    def test_field_equals_mismatch(self):
        guard = {"type": "field_equals", "field": "requester_id", "value": "other-id"}
        ok, msg = self.evaluator.evaluate(guard, self.instance, self.actor)
        self.assertFalse(ok)

    # ─── field_not_equals ───

    def test_field_not_equals_passes_when_different(self):
        guard = {"type": "field_not_equals", "field": "requester_id", "source": "actor.id"}
        # requester_id == "requester-1", actor.id == "actor-1" → different → allow
        ok, msg = self.evaluator.evaluate(guard, self.instance, self.actor)
        self.assertTrue(ok)

    def test_field_not_equals_denies_when_same(self):
        self.instance.requester_id = self.actor.pk
        guard = {"type": "field_not_equals", "field": "requester_id", "source": "actor.id"}
        ok, msg = self.evaluator.evaluate(guard, self.instance, self.actor)
        self.assertFalse(ok)

    # ─── entity_field_lt (needs linked entity mock) ───

    def test_entity_field_lt_passes(self):
        """Simulate entity with enrolled_count < capacity."""
        entity = _MockEntity(enrolled_count=5, capacity=10)
        # Patch _get_linked_entity to return our mock
        with patch.object(self.evaluator, "_get_linked_entity", return_value=entity):
            guard = {"type": "entity_field_lt", "field": "enrolled_count", "other_field": "capacity"}
            ok, msg = self.evaluator.evaluate(guard, self.instance, self.actor)
            self.assertTrue(ok)

    def test_entity_field_lt_denies_when_equal(self):
        entity = _MockEntity(enrolled_count=10, capacity=10)
        with patch.object(self.evaluator, "_get_linked_entity", return_value=entity):
            guard = {"type": "entity_field_lt", "field": "enrolled_count", "other_field": "capacity"}
            ok, msg = self.evaluator.evaluate(guard, self.instance, self.actor)
            self.assertFalse(ok)

    def test_entity_field_lt_no_entity(self):
        with patch.object(self.evaluator, "_get_linked_entity", return_value=None):
            guard = {"type": "entity_field_lt", "field": "enrolled_count", "other_field": "capacity"}
            ok, msg = self.evaluator.evaluate(guard, self.instance, self.actor)
            self.assertFalse(ok)
            self.assertIn("موجودیت دامنه", msg)

    # ─── all (AND) ───

    def test_all_passes_when_all_pass(self):
        guard = {
            "type": "all",
            "guards": [
                {"type": "always_true"},
                {"type": "field_not_equals", "field": "requester_id", "source": "actor.id"},
            ],
        }
        ok, msg = self.evaluator.evaluate(guard, self.instance, self.actor)
        self.assertTrue(ok)

    def test_all_fails_when_one_fails(self):
        guard = {
            "type": "all",
            "guards": [
                {"type": "always_true"},
                {"type": "field_equals", "field": "requester_id", "value": "wrong-id"},
            ],
        }
        ok, msg = self.evaluator.evaluate(guard, self.instance, self.actor)
        self.assertFalse(ok)

    # ─── any (OR) ───

    def test_any_passes_when_one_passes(self):
        guard = {
            "type": "any",
            "guards": [
                {"type": "field_equals", "field": "requester_id", "value": "wrong-id"},
                {"type": "always_true"},
            ],
        }
        ok, msg = self.evaluator.evaluate(guard, self.instance, self.actor)
        self.assertTrue(ok)

    def test_any_fails_when_all_fail(self):
        guard = {
            "type": "any",
            "guards": [
                {"type": "field_equals", "field": "requester_id", "value": "wrong"},
                {"type": "field_equals", "field": "nonexistent", "value": "x"},
            ],
        }
        ok, msg = self.evaluator.evaluate(guard, self.instance, self.actor)
        self.assertFalse(ok)