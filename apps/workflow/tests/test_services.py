"""Service-level tests for the B6 semantic operations.

Covers: approve/reject service paths, ApprovalRecord creation (independent of
status), requires_comment enforcement, due_date derivation from
State.default_due_hours, notification outbox rows (never sent inline),
send_copy, delegate, and role-based authorization (negative tests).

Runs against the DB — same conventions as the forms test suite.
"""
from __future__ import annotations

import datetime

from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import Role
from apps.forms.tests.factories import UserFactory
from apps.tasks.models import WorkflowTask
from apps.workflow.models import (
    ActionLog,
    ApprovalRecord,
    Instance,
    InstanceCopy,
    NotificationOutbox,
    State,
    Transition,
    WorkflowDefinition,
)
from apps.workflow.services import (
    InvalidTransitionError,
    WorkflowEngineService,
)


def _definition(code="sem-wf", *, due_hours=None):
    definition, _ = WorkflowDefinition.objects.get_or_create(
        code=code, defaults={"name": "فرآیند معنایی", "version": 1}
    )
    new_state, _ = State.objects.get_or_create(
        workflow_definition=definition, code="new",
        defaults={"name": "جدید", "is_initial": True,
                  "default_due_hours": due_hours},
    )
    review_state, _ = State.objects.get_or_create(
        workflow_definition=definition, code="pending-manager",
        defaults={"name": "در انتظار مدیر", "default_due_hours": due_hours},
    )
    approved_state, _ = State.objects.get_or_create(
        workflow_definition=definition, code="approved",
        defaults={"name": "تاییدشده", "is_final": True},
    )
    rejected_state, _ = State.objects.get_or_create(
        workflow_definition=definition, code="rejected",
        defaults={"name": "ردشده", "is_final": True},
    )
    Transition.objects.get_or_create(
        workflow_definition=definition, from_state=new_state,
        to_state=review_state, name="submit",
        defaults={"allowed_role_codes": ["employee"], "kind": "submit"},
    )
    Transition.objects.get_or_create(
        workflow_definition=definition, from_state=review_state,
        to_state=approved_state, name="approve",
        defaults={"allowed_role_codes": ["manager"], "kind": "approve"},
    )
    Transition.objects.get_or_create(
        workflow_definition=definition, from_state=review_state,
        to_state=rejected_state, name="reject",
        defaults={"allowed_role_codes": ["manager"], "kind": "reject",
                  "requires_comment": True},
    )
    return definition


class SemanticOperationTests(TestCase):
    def setUp(self):
        for code in ("employee", "manager", "hr", "workflow_admin", "student",
                     "teacher", "parent"):
            Role.objects.get_or_create(code=code, defaults={"name": code, "priority": 50})
        self.engine = WorkflowEngineService()
        self.employee = UserFactory(username="sem-employee", roles=["employee"])
        self.manager = UserFactory(username="sem-manager", roles=["manager"])
        self.other_manager = UserFactory(username="sem-manager2", roles=["manager"])
        self.definition = _definition()
        self.instance = self.engine.create_instance(
            workflow_code=self.definition.code,
            requester=self.employee,
            title="درخواست تست",
        )

    def _submit(self):
        return self.engine.execute_transition(
            instance_id=self.instance.pk,
            transition_id=Transition.objects.get(
                workflow_definition=self.definition, name="submit").pk,
            actor=self.employee,
        )

    # ── approve / reject ────────────────────────────────────────────────

    def test_approve_creates_approval_record_and_outbox(self):
        self._submit()
        result = self.engine.approve(self.instance.pk, self.manager, comment="تایید")
        self.assertEqual(result.status, Instance.Status.COMPLETED)
        record = ApprovalRecord.objects.get(instance=self.instance)
        self.assertEqual(record.action, "approve")
        self.assertEqual(record.approver_id, self.manager.pk)
        self.assertEqual(record.role_code, "manager")
        self.assertFalse(record.is_revoked)
        # Requester got an outbox notification (not an actual send).
        self.assertTrue(
            NotificationOutbox.objects.filter(
                instance=self.instance, recipient=self.employee, template="approved"
            ).exists()
        )

    def test_reject_requires_comment(self):
        self._submit()
        with self.assertRaises(InvalidTransitionError):
            self.engine.reject(self.instance.pk, self.manager, comment="")
        result = self.engine.reject(self.instance.pk, self.manager, comment="علت رد")
        self.assertEqual(result.status, Instance.Status.REJECTED)
        self.assertEqual(
            ApprovalRecord.objects.get(instance=self.instance).action, "reject"
        )

    def test_approve_denied_without_manager_role(self):
        self._submit()
        with self.assertRaises(InvalidTransitionError):
            self.engine.approve(self.instance.pk, self.employee)
        self.assertFalse(ApprovalRecord.objects.filter(instance=self.instance).exists())

    # ── due_date derivation ─────────────────────────────────────────────

    def test_tasks_get_due_date_from_state_default(self):
        definition = _definition(code="sla-wf", due_hours=24)
        instance = self.engine.create_instance(
            workflow_code=definition.code, requester=self.employee, title="SLA"
        )
        # initial state has due_hours=24 → tasks for it carry a due_date.
        task = WorkflowTask.objects.filter(instance=instance).first()
        self.assertIsNotNone(task.due_date)
        delta = task.due_date - timezone.now()
        self.assertAlmostEqual(delta.total_seconds(), 24 * 3600, delta=120)

    def test_tasks_without_state_due_hours_have_null_due(self):
        self._submit()  # pending-manager has no default_due_hours
        task = WorkflowTask.objects.filter(
            instance=self.instance,
            state__code="pending-manager",
        ).first()
        self.assertIsNotNone(task)
        self.assertIsNone(task.due_date)

    # ── send_copy ───────────────────────────────────────────────────────

    def test_send_copy_creates_rows_and_notifications(self):
        created = self.engine.send_copy(
            self.instance.pk, self.manager,
            recipient_ids=[self.other_manager.pk], note="جهت اطلاع",
        )
        self.assertEqual(created, 1)
        self.assertTrue(
            InstanceCopy.objects.filter(
                instance=self.instance, recipient=self.other_manager
            ).exists()
        )
        self.assertTrue(
            NotificationOutbox.objects.filter(
                instance=self.instance, recipient=self.other_manager,
                template="copy_received",
            ).exists()
        )
        # No WorkflowTask must be created for a copy recipient.
        self.assertFalse(
            WorkflowTask.objects.filter(
                instance=self.instance, assignee=self.other_manager
            ).exists()
        )

    def test_send_copy_is_idempotent(self):
        self.engine.send_copy(self.instance.pk, self.manager,
                              recipient_ids=[self.other_manager.pk])
        created = self.engine.send_copy(self.instance.pk, self.manager,
                                        recipient_ids=[self.other_manager.pk])
        self.assertEqual(created, 0)

    # ── delegate ────────────────────────────────────────────────────────

    def test_delegate_moves_pending_tasks(self):
        self._submit()
        moved = self.engine.delegate(
            self.instance.pk, self.manager, self.other_manager, comment="مرخصی"
        )
        self.assertGreaterEqual(moved, 1)
        self.assertTrue(
            WorkflowTask.objects.filter(
                instance=self.instance,
                state__code="pending-manager",
                assignee=self.other_manager,
                status=WorkflowTask.Status.PENDING,
            ).exists()
        )
        self.assertFalse(
            WorkflowTask.objects.filter(
                instance=self.instance, state__code="pending-manager",
                assignee=self.manager, status=WorkflowTask.Status.PENDING,
            ).exists()
        )
        self.assertTrue(
            ActionLog.objects.filter(
                instance=self.instance, action="delegate"
            ).exists()
        )

    def test_delegate_denied_without_own_task(self):
        self._submit()
        third = UserFactory(username="sem-teacher", roles=["teacher"])
        with self.assertRaises(InvalidTransitionError):
            self.engine.delegate(self.instance.pk, third, self.other_manager)

    def test_delegate_recipient_must_hold_a_role_for_current_state(self):
        self._submit()
        teacher = UserFactory(username="sem-ineligible-teacher", roles=["teacher"])
        with self.assertRaises(InvalidTransitionError):
            self.engine.delegate(self.instance.pk, self.manager, teacher)

    # ── outbox is write-only in the transaction ─────────────────────────

    def test_transition_never_sends_outside_outbox(self):
        # The only allowed artifact of notification is an outbox row with
        # status pending; nothing sets sent_at during the transition.
        self._submit()
        rows = NotificationOutbox.objects.filter(instance=self.instance)
        self.assertTrue(rows.exists())
        self.assertFalse(rows.exclude(status=NotificationOutbox.Status.PENDING).exists())
        self.assertFalse(rows.exclude(sent_at__isnull=True).exists())
