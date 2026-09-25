"""Claim and deliver due notification outbox rows with bounded retries."""
from __future__ import annotations

import logging
from datetime import timedelta

from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone

from apps.workflow.models import NotificationOutbox

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Atomically claim and deliver due workflow notification outbox rows"

    def add_arguments(self, parser) -> None:
        parser.add_argument("--limit", type=int, default=100)
        parser.add_argument("--max-attempts", type=int, default=5)
        parser.add_argument("--retry-base-seconds", type=int, default=60)
        parser.add_argument("--max-retry-seconds", type=int, default=21600)
        parser.add_argument("--claim-lease-minutes", type=int, default=30)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options) -> None:
        if min(options["limit"], options["max_attempts"], options["retry_base_seconds"],
               options["max_retry_seconds"], options["claim_lease_minutes"]) < 1:
            raise CommandError("limits, retry values, and claim lease must be positive")

        now = timezone.now()
        due = NotificationOutbox.objects.filter(
            status=NotificationOutbox.Status.PENDING,
            next_attempt_at__lte=now,
        ).order_by("next_attempt_at", "created_at")
        if options["dry_run"]:
            rows = due.select_related("recipient", "instance")[:options["limit"]]
            for row in rows:
                self.stdout.write(
                    f"[dry-run] {row.channel} recipient={row.recipient_id} "
                    f"template={row.template} instance={row.instance_id}"
                )
            return

        claimed = self._claim_due(
            limit=options["limit"],
            now=now,
            lease=timedelta(minutes=options["claim_lease_minutes"]),
        )
        sent = failed = dead_lettered = 0
        for row, claim_time in claimed:
            try:
                self._deliver(row)
            except Exception as exc:  # one bad message must not stop the batch
                failed += 1
                dead = row.attempts >= options["max_attempts"]
                delay = min(
                    options["retry_base_seconds"] * (2 ** max(row.attempts - 1, 0)),
                    options["max_retry_seconds"],
                )
                status_value = (
                    NotificationOutbox.Status.DEAD_LETTER
                    if dead else NotificationOutbox.Status.PENDING
                )
                updated = NotificationOutbox.objects.filter(
                    pk=row.pk,
                    status=NotificationOutbox.Status.PROCESSING,
                    claimed_at=claim_time,
                ).update(
                    status=status_value,
                    next_attempt_at=now + timedelta(seconds=delay),
                    claimed_at=None,
                    last_error=str(exc)[:2000],
                    updated_at=timezone.now(),
                )
                if updated and dead:
                    dead_lettered += 1
                logger.error(
                    "notification delivery failed id=%s attempt=%s dead_letter=%s error=%s",
                    row.pk, row.attempts, dead, str(exc)[:500],
                )
                continue

            updated = NotificationOutbox.objects.filter(
                pk=row.pk,
                status=NotificationOutbox.Status.PROCESSING,
                claimed_at=claim_time,
            ).update(
                status=NotificationOutbox.Status.SENT,
                sent_at=timezone.now(),
                claimed_at=None,
                last_error="",
                updated_at=timezone.now(),
            )
            sent += int(bool(updated))

        pending = NotificationOutbox.objects.filter(
            status=NotificationOutbox.Status.PENDING,
        )
        oldest = pending.order_by("created_at").only("created_at").first()
        oldest_age = max((timezone.now() - oldest.created_at).total_seconds(), 0) if oldest else 0
        dead_letter_count = NotificationOutbox.objects.filter(
            status=NotificationOutbox.Status.DEAD_LETTER,
        ).count()
        logger.info(
            "notification_outbox_metrics pending=%s dead_letter=%s oldest_age_seconds=%.1f",
            pending.count(), dead_letter_count, oldest_age,
        )
        self.stdout.write(self.style.SUCCESS(
            f"notifications flushed: {sent} sent, {failed} failed, "
            f"{dead_lettered} dead-lettered"
        ))

    @staticmethod
    def _claim_due(*, limit: int, now, lease: timedelta):
        """Claim a batch in one transaction; concurrent workers skip locked rows."""
        stale_before = now - lease
        with transaction.atomic():
            NotificationOutbox.objects.filter(
                status=NotificationOutbox.Status.PROCESSING,
                claimed_at__lt=stale_before,
            ).update(
                status=NotificationOutbox.Status.PENDING,
                claimed_at=None,
                next_attempt_at=now,
                updated_at=now,
            )
            qs = NotificationOutbox.objects.filter(
                status=NotificationOutbox.Status.PENDING,
                next_attempt_at__lte=now,
            ).order_by("next_attempt_at", "created_at")
            if connection.features.has_select_for_update_skip_locked:
                qs = qs.select_for_update(skip_locked=True)
            elif connection.features.has_select_for_update:
                qs = qs.select_for_update()
            rows = list(qs.select_related("recipient", "instance")[:limit])
            claimed = []
            for row in rows:
                row.status = NotificationOutbox.Status.PROCESSING
                row.claimed_at = now
                row.attempts += 1
                row.save(update_fields=["status", "claimed_at", "attempts", "updated_at"])
                claimed.append((row, now))
        return claimed

    def _deliver(self, row: NotificationOutbox) -> None:
        payload = row.payload or {}
        title = payload.get("title", "اعلان سیستمی")
        body_lines = [str(title)]
        for key, label in (
            ("actor", "اقدام‌کننده"), ("transition", "اقدام"),
            ("comment", "توضیح"), ("from", "از طرف"), ("note", "یادداشت"),
        ):
            if payload.get(key):
                body_lines.append(f"{label}: {payload[key]}")
        body = "\n".join(body_lines)

        if row.channel == NotificationOutbox.Channel.EMAIL:
            if not row.recipient.email:
                raise ValueError("recipient has no email address")
            send_mail(
                subject=f"[Pen LMS] {title}",
                message=body,
                from_email=None,
                recipient_list=[row.recipient.email],
                fail_silently=False,
            )
        elif row.channel == NotificationOutbox.Channel.SMS:
            raise NotImplementedError("SMS gateway delivery is not implemented")
        # IN_APP rows are durable inbox entries; successful claim is delivery.
