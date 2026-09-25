from __future__ import annotations

from celery import shared_task
from django.core.management import call_command


@shared_task(
    name="pen.forms.reconcile_education_projections",
    autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def reconcile_education_projections_task(limit: int = 50) -> dict:
    """Run an idempotent batch of attendance projection reconciliation."""
    call_command("reconcile_education_projections", limit=limit)
    return {"status": "ok"}
