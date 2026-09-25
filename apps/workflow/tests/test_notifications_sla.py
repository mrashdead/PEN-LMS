"""Notification inbox + SLA scan tests (outbox consumer half of B6)."""
from __future__ import annotations

import datetime
import io
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest import skipUnless
from unittest.mock import patch

from django.core.management import call_command
from django.db import close_old_connections, connection, connections
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from apps.forms.tests.factories import UserFactory
from apps.workflow.models import (
    Instance,
    NotificationOutbox,
    State,
    Transition,
    WorkflowDefinition,
)


def _wf_with_due(code="notify-wf", due_hours=24):
    definition = WorkflowDefinition.objects.create(
        code=code, name="تست اعلان", is_active=True,
    )
    initial = State.objects.create(
        workflow_definition=definition, code="new", name="جدید",
        is_initial=True, default_due_hours=due_hours,
    )
    final = State.objects.create(
        workflow_definition=definition, code="done", name="پایان", is_final=True,
    )
    Transition.objects.create(
        workflow_definition=definition, from_state=initial, to_state=final,
        name="approve", allowed_role_codes=["manager"], kind="approve",
    )
    return definition, initial, final


class InboxFlowTests(TestCase):
    """create → transition queues outbox → flush delivers → inbox shows."""

    def setUp(self):
        from apps.accounts.models import Role

        for code in ("manager", "employee"):
            Role.objects.get_or_create(code=code, defaults={"name": code})
        self.employee = UserFactory(username="nb-employee", roles=["employee"])
        self.manager = UserFactory(username="nb-manager", roles=["manager"])
        self.definition, self.s_new, self.s_done = _wf_with_due("nb-wf")

    def _submit_flow(self):
        from apps.workflow.services import WorkflowEngineService

        engine = WorkflowEngineService()
        instance = engine.create_instance(
            workflow_code=self.definition.code, requester=self.employee, title="تست",
        )
        # manager task fan-out happens on the next state; approve notifies the
        # requester with the `approved` template.
        t = Transition.objects.get(workflow_definition=self.definition, name="approve")
        engine.execute_transition(instance.pk, t.pk, self.manager, comment="تایید شد")
        return instance

    def test_outbox_row_queued_for_requester(self):
        instance = self._submit_flow()
        row = NotificationOutbox.objects.get(recipient=self.employee)
        self.assertEqual(row.template, "approved")
        self.assertEqual(row.status, NotificationOutbox.Status.PENDING)

    def test_flush_delivers_then_inbox_lists(self):
        self._submit_flow()
        call_command("flush_notifications", stdout=io.StringIO())
        self.employee.refresh_from_db()
        self.client.force_login(self.employee)
        response = self.client.get("/api/notifications/")
        self.assertEqual(response.status_code, 200)
        items = response.json()["results"]
        self.assertEqual(len(items), 1)
        self.assertFalse(items[0]["is_read"])

        # unread=1 shows it; mark-read removes it from unread, keeps read_at.
        unread = self.client.get("/api/notifications/?unread=1").json()["results"]
        self.assertEqual(len(unread), 1)
        pk = items[0]["id"]
        r = self.client.post(f"/api/notifications/{pk}/read/")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["is_read"])
        self.assertEqual(
            len(self.client.get("/api/notifications/?unread=1").json()["results"]), 0
        )

    def test_read_all_bulk(self):
        self._submit_flow()
        self._submit_flow()
        call_command("flush_notifications", stdout=io.StringIO())
        self.client.force_login(self.employee)
        r = self.client.post("/api/notifications/read-all/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["marked_read"], 2)
        self.assertEqual(
            len(self.client.get("/api/notifications/?unread=1").json()["results"]), 0
        )

    def test_other_users_cannot_see_or_mark(self):
        self._submit_flow()
        call_command("flush_notifications", stdout=io.StringIO())
        outsider = UserFactory(username="nb-outsider", roles=["employee"])
        self.client.force_login(outsider)
        response = self.client.get("/api/notifications/")
        self.assertEqual(len(response.json()["results"]), 0)
        row = NotificationOutbox.objects.get(recipient=self.employee)
        probe = self.client.post(f"/api/notifications/{row.pk}/read/")
        self.assertEqual(probe.status_code, 404)
        row.refresh_from_db()
        self.assertFalse(row.is_read)

    def test_outbox_retries_then_moves_to_dead_letter(self):
        row = NotificationOutbox.objects.create(
            instance=self._submit_flow(),
            recipient=self.employee,
            channel=NotificationOutbox.Channel.EMAIL,
            template="retry-test",
            delivery_key="test:retry:dead-letter",
        )

        call_command(
            "flush_notifications", max_attempts=2, retry_base_seconds=1,
            stdout=io.StringIO(),
        )
        row.refresh_from_db()
        self.assertEqual(row.status, NotificationOutbox.Status.PENDING)
        self.assertEqual(row.attempts, 1)
        self.assertTrue(row.last_error)
        self.assertGreater(row.next_attempt_at, timezone.now())

        row.next_attempt_at = timezone.now() - datetime.timedelta(seconds=1)
        row.save(update_fields=["next_attempt_at", "updated_at"])
        call_command(
            "flush_notifications", max_attempts=2, retry_base_seconds=1,
            stdout=io.StringIO(),
        )
        row.refresh_from_db()
        self.assertEqual(row.status, NotificationOutbox.Status.DEAD_LETTER)
        self.assertEqual(row.attempts, 2)

    def test_delivery_key_is_database_unique(self):
        instance = self._submit_flow()
        key = "test:unique:delivery"
        NotificationOutbox.objects.create(
            instance=instance, recipient=self.employee, delivery_key=key,
        )
        from django.db import IntegrityError, transaction

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                NotificationOutbox.objects.create(
                    instance=instance, recipient=self.employee, delivery_key=key,
                )


class SLAScanTests(TestCase):
    def setUp(self):
        from apps.accounts.models import Role

        for code in ("manager", "employee"):
            Role.objects.get_or_create(code=code, defaults={"name": code})
        self.employee = UserFactory(username="sla-employee", roles=["employee"])
        self.manager = UserFactory(username="sla-manager", roles=["manager"])
        self.definition, self.s_new, self.s_done = _wf_with_due("sla2-wf", due_hours=24)

    def _pending_task(self, due):
        from apps.tasks.models import WorkflowTask

        instance = Instance.objects.create(
            workflow_definition=self.definition, current_state=self.s_new,
            requester=self.employee, title="تست SLA", status=Instance.Status.RUNNING,
        )
        task = WorkflowTask.objects.create(
            instance=instance, state=self.s_new,
            assignee=self.employee, status=WorkflowTask.Status.PENDING,
            due_date=due,
        )
        return instance, task

    def test_reminder_fires_once_in_lead_window(self):
        from apps.tasks.models import WorkflowTask

        due = timezone.now() + datetime.timedelta(hours=2)  # inside 4h lead
        _, task = self._pending_task(due)
        out = io.StringIO()
        call_command("scan_sla", stdout=out)
        rows = NotificationOutbox.objects.filter(
            template="sla_reminder", recipient=self.employee
        )
        self.assertEqual(rows.count(), 1)
        task.refresh_from_db()
        self.assertIsNotNone(task.reminder_sent_at)
        # Second scan must NOT re-fire (idempotent).
        call_command("scan_sla", stdout=io.StringIO())
        self.assertEqual(rows.count(), 1)

    def test_far_future_task_not_reminded(self):
        due = timezone.now() + datetime.timedelta(days=3)
        self._pending_task(due)
        call_command("scan_sla", stdout=io.StringIO())
        self.assertFalse(
            NotificationOutbox.objects.filter(template="sla_reminder").exists()
        )

    def test_escalation_notifies_manager_and_assignee_once(self):
        from apps.tasks.models import WorkflowTask

        due = timezone.now() - datetime.timedelta(hours=1)
        _, task = self._pending_task(due)
        call_command("scan_sla", stdout=io.StringIO())
        rows = NotificationOutbox.objects.filter(template="sla_escalated")
        # manager + assignee, two distinct recipients.
        self.assertEqual(set(rows.values_list("recipient_id", flat=True)),
                         {self.manager.pk, self.employee.pk})
        task.refresh_from_db()
        self.assertIsNotNone(task.escalated_at)
        call_command("scan_sla", stdout=io.StringIO())
        self.assertEqual(rows.count(), 2)  # no duplicates on re-scan

    def test_escalation_skips_self_when_assignee_is_only_manager(self):
        due = timezone.now() - datetime.timedelta(hours=1)
        from apps.tasks.models import WorkflowTask

        instance = Instance.objects.create(
            workflow_definition=self.definition, current_state=self.s_new,
            requester=self.employee, title="خود-ارفعایی",
        )
        WorkflowTask.objects.create(
            instance=instance, state=self.s_new, assignee=self.manager,
            status=WorkflowTask.Status.PENDING, due_date=due,
        )
        call_command("scan_sla", stdout=io.StringIO())
        rows = NotificationOutbox.objects.filter(template="sla_escalated")
        self.assertEqual(rows.count(), 1)  # only the assignee himself
        self.assertEqual(rows.first().recipient_id, self.manager.pk)

    def test_dry_run_writes_nothing(self):
        due = timezone.now() - datetime.timedelta(hours=1)
        self._pending_task(due)
        call_command("scan_sla", dry_run=True, stdout=io.StringIO())
        self.assertFalse(NotificationOutbox.objects.exists())

    def test_tasks_api_overdue_filter_and_ordering(self):
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType

        from apps.tasks.models import WorkflowTask

        self.employee.user_permissions.add(
            Permission.objects.get(
                content_type=ContentType.objects.get_for_model(WorkflowTask),
                codename="view_workflowtask",
            )
        )
        for attr in ("_user_perm_cache", "_group_perm_cache", "_perm_cache"):
            if hasattr(self.employee, attr):
                delattr(self.employee, attr)

        past = timezone.now() - datetime.timedelta(hours=1)
        future = timezone.now() + datetime.timedelta(days=1)
        self._pending_task(past)
        self._pending_task(future)
        self.client.force_login(self.employee)
        response = self.client.get("/api/tasks/?overdue=true&ordering=due_date")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 1)
        self.assertTrue(data["results"][0]["is_overdue"])
        response = self.client.get("/api/tasks/?overdue=false")
        ids = {r["id"] for r in response.json()["results"]}
        self.assertEqual(len(ids), 1)
        response = self.client.get("/api/tasks/?ordering=id),x--")
        self.assertEqual(response.status_code, 200)


@skipUnless(
    connection.features.has_select_for_update_skip_locked,
    "Concurrent outbox claim requires PostgreSQL SKIP LOCKED",
)
class NotificationClaimConcurrencyTests(TransactionTestCase):
    def setUp(self):
        from apps.accounts.models import Role

        Role.objects.get_or_create(code="employee", defaults={"name": "employee"})
        self.employee = UserFactory(username="claim-race-user", roles=["employee"])
        self.definition, self.state, _ = _wf_with_due("claim-race-wf")
        self.instance = Instance.objects.create(
            workflow_definition=self.definition,
            current_state=self.state,
            requester=self.employee,
            title="Claim race",
        )
        self.row = NotificationOutbox.objects.create(
            instance=self.instance, recipient=self.employee,
            delivery_key="test:claim-race",
        )

    def test_two_workers_deliver_a_claimed_row_once(self):
        from apps.workflow.management.commands.flush_notifications import Command

        entered_delivery = Event()
        release_delivery = Event()
        delivered = []

        def blocked_delivery(row):
            delivered.append(row.pk)
            entered_delivery.set()
            if not release_delivery.wait(timeout=5):
                raise AssertionError("test did not release the first worker")

        def run_worker():
            close_old_connections()
            try:
                call_command("flush_notifications", stdout=io.StringIO())
            finally:
                connections.close_all()

        with patch.object(Command, "_deliver", side_effect=blocked_delivery):
            with ThreadPoolExecutor(max_workers=2) as pool:
                first = pool.submit(run_worker)
                self.assertTrue(entered_delivery.wait(timeout=5))
                second = pool.submit(run_worker)
                second.result(timeout=5)
                release_delivery.set()
                first.result(timeout=5)

        self.row.refresh_from_db()
        self.assertEqual(delivered, [self.row.pk])
        self.assertEqual(self.row.status, NotificationOutbox.Status.SENT)
        self.assertEqual(self.row.attempts, 1)
