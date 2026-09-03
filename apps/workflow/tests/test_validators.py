from __future__ import annotations

from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.workflow.models import Instance, Transition
from apps.workflow.validators import TransitionValidator

User = get_user_model()


class _MockUser:
    """Minimal mock for role_codes() without DB."""
    def __init__(self, roles: set[str], pk="actor-uuid"):
        self.pk = pk
        self.id = pk
        self._roles = roles
        self.username = f"user-{pk}"

    def role_codes(self) -> set[str]:
        return self._roles


class _MockState:
    def __init__(self, code="stub", pk="state-uuid"):
        self.code = code
        self.pk = pk
        self.id = pk


class _MockTransition:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.pk = kwargs.get("pk", "transition-uuid")
        self.id = self.pk


class TransitionValidatorTestCase(TestCase):
    """Pure unit tests — no DB required."""

    def setUp(self):
        self.validator = TransitionValidator()
        self.actor = _MockUser({"employee", "manager"})
        self.initial_state = _MockState("draft")
        self.approved_state = _MockState("approved")
        self.instance = MagicMock(spec=Instance)
        self.instance.status = Instance.Status.RUNNING
        self.instance.workflow_definition_id = "wf-uuid"
        self.instance.current_state = self.initial_state
        self.instance.current_state_id = self.initial_state.pk
        self.transition = _MockTransition(
            pk="t1",
            workflow_definition_id="wf-uuid",
            from_state_id=self.initial_state.pk,
            to_state_id=self.approved_state.pk,
            name="approve",
            allowed_role_codes=["manager"],
            guard_expression={},
        )

    # ─── Valid transition ───

    def test_valid_transition_passes(self):
        result = self.validator.validate(self.instance, self.transition, self.actor)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.errors, [])

    # ─── Instance not running ───

    def test_instance_not_running_denies(self):
        self.instance.status = Instance.Status.COMPLETED
        result = self.validator.validate(self.instance, self.transition, self.actor)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("running" in e or "وضعیت" in e for e in result.errors))

    # ─── Wrong workflow ───

    def test_wrong_workflow_denies(self):
        self.transition.workflow_definition_id = "other-wf"
        result = self.validator.validate(self.instance, self.transition, self.actor)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("Transition" in e and "این Instance" in e for e in result.errors))

    # ─── Wrong current state ───

    def test_wrong_current_state_denies(self):
        self.transition.from_state_id = "other-state"
        result = self.validator.validate(self.instance, self.transition, self.actor)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("از وضعیت جاری" in e for e in result.errors))

    # ─── Missing role ───

    def test_missing_role_denies(self):
        actor_no_role = _MockUser({"student"})
        result = self.validator.validate(self.instance, self.transition, actor_no_role)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("نقش" in e or "role" in e for e in result.errors))

    def test_no_role_codes_allows_anyone(self):
        self.transition.allowed_role_codes = []
        result = self.validator.validate(self.instance, self.transition, _MockUser({"student"}))
        self.assertTrue(result.is_valid)

    # ─── Guard integration ───

    def test_guard_deny_rejects(self):
        self.transition.guard_expression = {"type": "role_not_in", "roles": ["manager"], "field": "requester"}
        self.instance.requester = self.actor
        result = self.validator.validate(self.instance, self.transition, self.actor)
        # The actor has "manager" role, and the guard checks requester field which is same actor
        # The guard evaluator checks: does instance.requester have role "manager"? → yes → deny
        self.assertFalse(result.is_valid)

    def test_guard_unknown_type_denies(self):
        self.transition.guard_expression = {"type": "nonexistent"}
        result = self.validator.validate(self.instance, self.transition, self.actor)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("طبق سیاست" in e for e in result.errors))