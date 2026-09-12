"""
Deliver queued notifications (B6 outbox worker).

    python manage.py flush_notifications [--limit N] [--dry-run]

Processes NotificationOutbox rows with status=pending: renders the payload,
attempts delivery through Django's email backend for the email channel, and
marks the row sent/failed with attempt counting. An IN_APP row is marked sent
once written (it is consumed by the UI's unread list).

Key invariant (report §6/§13): this runs OUTSIDE the workflow transaction, so
a failing mailer never rolls back a committed transition. Failures are recorded
per-row with ``attempts`` + ``last_error`` and retried on the next run.
"""
from __future__ import annotations

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.workflow.models import NotificationOutbox


class Command(BaseCommand):
    help = "Deliver pending workflow notification outbox rows"

    def add_arguments(self, parser) -> None:
        parser.add_argument("--limit", type=int, default=100,
                            help="Max rows per run (default 100).")
        parser.add_argument("--max-attempts", type=int, default=5,
                            help="Rows failing this many times are marked "
                                 "failed and skipped afterwards.")
        parser.add_argument("--dry-run", action="store_true",
                            help="Report what would be sent without sending.")

    def handle(self, *args, **options) -> None:
        qs = (
            NotificationOutbox.objects.filter(
                status=NotificationOutbox.Status.PENDING
            )
            .select_related("recipient", "instance")
            .order_by("created_at")[: options["limit"]]
        )
        sent = failed = 0
        for row in qs:
            row.attempts += 1
            if options["dry_run"]:
                self.stdout.write(
                    f"[dry-run] {row.channel} → {row.recipient} "
                    f"template={row.template} instance={row.instance_id}"
                )
                continue
            try:
                self._deliver(row)
            except Exception as exc:  # noqa: BLE001 - one bad row must not kill the run
                failed += 1
                row.status = (
                    NotificationOutbox.Status.FAILED
                    if row.attempts >= options["max_attempts"]
                    else NotificationOutbox.Status.PENDING
                )
                row.last_error = str(exc)[:2000]
                row.save(update_fields=["attempts", "status", "last_error", "updated_at"])
                self.stderr.write(f"notify {row.pk} failed (attempt {row.attempts}): {exc}")
                continue
            row.status = NotificationOutbox.Status.SENT
            row.sent_at = timezone.now()
            row.last_error = ""
            row.save(update_fields=["attempts", "status", "sent_at", "last_error", "updated_at"])
            sent += 1

        if not options["dry_run"]:
            self.stdout.write(self.style.SUCCESS(
                f"notifications flushed: {sent} sent, {failed} failed"
            ))

    def _deliver(self, row: NotificationOutbox) -> None:
        payload = row.payload or {}
        title = payload.get("title", "اعلان سیستمی")
        body_lines = [str(title)]
        if payload.get("actor"):
            body_lines.append(f"اقدام‌کننده: {payload['actor']}")
        if payload.get("transition"):
            body_lines.append(f"اقدام: {payload['transition']}")
        if payload.get("comment"):
            body_lines.append(f"توضیح: {payload['comment']}")
        if payload.get("from"):
            body_lines.append(f"از طرف: {payload['from']}")
        if payload.get("note"):
            body_lines.append(f"یادداشت: {payload['note']}")
        body = "\n".join(body_lines)

        if row.channel == NotificationOutbox.Channel.EMAIL:
            if not row.recipient.email:
                raise ValueError("recipient has no email address")
            send_mail(
                subject=f"[Pen LMS] {title}",
                message=body,
                from_email=None,  # DEFAULT_FROM_EMAIL
                recipient_list=[row.recipient.email],
                fail_silently=False,
            )
        # IN_APP / SMS: the row itself is the inbox record (UI reads pending→
        # sent); SMS needs a gateway integration and is intentionally not
        # silently "sent" — it raises until a backend is wired.
        elif row.channel == NotificationOutbox.Channel.SMS:
            raise NotImplementedError("SMS gateway not configured")
        # IN_APP: no external side effect; success = row flipped to sent.
