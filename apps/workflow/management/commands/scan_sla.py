"""
SLA scan — reminders before deadlines + escalations after them (§15-9).

    python manage.py scan_sla [--reminder-lead-hours N] [--escalation-role CODE]
                              [--dry-run]

For every PENDING WorkflowTask with a due_date:

  - reminder — due within SLA_REMINDER_LEAD_HOURS (default 4h) and
    ``reminder_sent_at`` still NULL → one in-app `sla_reminder` outbox row,
    then stamp the flag (never re-fires for the same task);
  - escalation — due_date in the past and ``escalated_at`` still NULL → one
    in-app `sla_escalated` row to every active holder of the escalation role
    (default: manager) + one to the assignee, then stamp the flag.

Design rules:
  - This NEVER mutates workflow state — it is an observer, not a participant.
  - It only writes outbox rows + its own liveness flags; delivery stays in
    flush_notifications (outside any workflow transaction).
  - Idempotent per task by construction (flag + FOR UPDATE SKIP LOCKED), so
    running it every few minutes is safe and two overlapping scans cannot
    double-notify.
"""
from __future__ import annotations

from datetime import timedelta

from django.conf import settings as project_settings
from django.core.management.base import BaseCommand
from django.db import models, transaction
from django.utils import timezone

from apps.tasks.models import WorkflowTask
from apps.workflow.models import NotificationOutbox


def _time_valid_q():
    """Role-validity filter shared with the engine's task fan-out."""
    now = timezone.now()
    return (
        models.Q(valid_from__isnull=True) | models.Q(valid_from__lte=now)
    ) & (
        models.Q(valid_to__isnull=True) | models.Q(valid_to__gte=now)
    )


class Command(BaseCommand):
    help = "Send SLA reminders (near due) and escalations (past due) for pending workflow tasks"

    def add_arguments(self, parser) -> None:
        parser.add_argument("--reminder-lead-hours", type=int, default=None,
                            help="Override SLA_REMINDER_LEAD_HOURS.")
        parser.add_argument("--escalation-role", type=str, default=None,
                            help="Override SLA_ESCALATION_ROLE.")
        parser.add_argument("--dry-run", action="store_true",
                            help="Report what would fire without writing.")

    def handle(self, *args, **options) -> None:
        lead_hours = options["reminder_lead_hours"]
        if lead_hours is None:
            lead_hours = getattr(project_settings, "SLA_REMINDER_LEAD_HOURS", 4)
        escalation_role = options["escalation_role"] or getattr(
            project_settings, "SLA_ESCALATION_ROLE", "manager"
        )
        dry = options["dry_run"]

        reminded = self._scan_reminders(lead_hours, dry)
        escalated = self._scan_escalations(escalation_role, dry)

        if not dry:
            self.stdout.write(self.style.SUCCESS(
                f"SLA scan: {reminded} reminder(s), {escalated} escalation(s)"
            ))

    # ── reminders ────────────────────────────────────────────────────────

    def _scan_reminders(self, lead_hours: int, dry: bool) -> int:
        now = timezone.now()
        window_end = now + timedelta(hours=lead_hours)
        base = WorkflowTask.objects.filter(
            status=WorkflowTask.Status.PENDING,
            due_date__isnull=False,
            due_date__gt=now,
            due_date__lte=window_end,
            reminder_sent_at__isnull=True,
        ).select_related("instance", "assignee")
        # A dry run must not take row locks — only the real pass serializes.
        candidates = base if dry else self._locked(base)
        count = 0

        def work():
            nonlocal count
            for task in candidates:
                if dry:
                    self.stdout.write(
                        f"[dry-run] reminder task={task.pk} "
                        f"assignee={task.assignee_id} due={task.due_date.isoformat()}"
                    )
                    count += 1
                    continue
                NotificationOutbox.objects.create(
                    instance=task.instance,
                    recipient=task.assignee,
                    channel=NotificationOutbox.Channel.IN_APP,
                    template="sla_reminder",
                    payload={
                        "title": task.instance.title,
                        "note": "مهلت انجام این کار رو به پایان است.",
                        "due_date": task.due_date.isoformat(),
                    },
                )
                task.reminder_sent_at = now
                task.save(update_fields=["reminder_sent_at", "updated_at"])
                count += 1

        if dry:
            work()
        else:
            with transaction.atomic():
                work()
        return count

    @staticmethod
    def _locked(qs):
        # SKIP LOCKED is the race-safe mode (two concurrent scans, two
        # workers); degrade gracefully where the driver lacks it (sqlite
        # test DBs) — single-process runs stay correct without the lock.
        from django.db import connection

        feats = connection.features
        if getattr(feats, "has_select_for_update_skip_locked", False):
            return qs.select_for_update(skip_locked=True)
        if getattr(feats, "has_select_for_update", False):
            return qs.select_for_update()
        return qs

    # ── escalations ──────────────────────────────────────────────────────

    def _scan_escalations(self, escalation_role: str, dry: bool) -> int:
        from apps.accounts.models import UserRole

        now = timezone.now()
        count = 0
        # Resolve escalation targets once (not per task).
        manager_ids = list(
            UserRole.objects.filter(
                role__code=escalation_role,
                is_active=True,
                role__is_active=True,
                role__is_deleted=False,
                user__is_active=True,
                user__is_deleted=False,
            )
            .filter(_time_valid_q())
            .values_list("user_id", flat=True)
            .distinct()
        )
        base = WorkflowTask.objects.filter(
            status=WorkflowTask.Status.PENDING,
            due_date__isnull=False,
            due_date__lt=now,
            escalated_at__isnull=True,
        ).select_related("instance", "assignee")
        candidates = base if dry else self._locked(base)

        def work():
            nonlocal count
            for task in candidates:
                if dry:
                    self.stdout.write(
                        f"[dry-run] escalate task={task.pk} overdue_since="
                        f"{task.due_date.isoformat()} → {escalation_role}:{manager_ids}"
                    )
                    count += 1
                    continue
                rows = [
                    NotificationOutbox(
                        instance=task.instance,
                        recipient_id=uid,
                        channel=NotificationOutbox.Channel.IN_APP,
                        template="sla_escalated",
                        payload={
                            "title": task.instance.title,
                            "note": "یک کار از مهلت تعیین‌شده گذشته است؛ لطفاً پیگیری کنید.",
                            "due_date": task.due_date.isoformat(),
                            "assignee": str(task.assignee_id),
                        },
                    )
                    for uid in manager_ids
                    if uid != task.assignee_id
                ]
                rows.append(
                    NotificationOutbox(
                        instance=task.instance,
                        recipient=task.assignee,
                        channel=NotificationOutbox.Channel.IN_APP,
                        template="sla_escalated",
                        payload={
                            "title": task.instance.title,
                            "note": "مهلت انجام این کار گذشته است.",
                            "due_date": task.due_date.isoformat(),
                        },
                    )
                )
                NotificationOutbox.objects.bulk_create(rows)
                task.escalated_at = now
                task.save(update_fields=["escalated_at", "updated_at"])
                count += 1

        if dry:
            work()
        else:
            with transaction.atomic():
                work()
        return count
