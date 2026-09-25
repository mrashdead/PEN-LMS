"""Celery jobs whose durable work is implemented by management commands."""
from __future__ import annotations

from celery import shared_task


@shared_task(
    name="pen.workflow.flush_notifications",
    autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def flush_notifications_task(limit: int = 100) -> dict:
    """Deliver one bounded batch; Celery retries unexpected worker failures."""
    from django.core.management import call_command

    call_command("flush_notifications", limit=limit)
    return {"status": "ok"}


@shared_task(
    name="pen.workflow.scan_sla",
    autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def scan_sla_task() -> dict:
    """Run one idempotent SLA scan; Celery retries unexpected worker failures."""
    from django.core.management import call_command

    call_command("scan_sla")
    return {"status": "ok"}
