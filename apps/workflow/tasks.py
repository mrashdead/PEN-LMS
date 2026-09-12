"""
Celery beat wiring for the notification/SLA pipeline (optional layer).

The pipeline works WITHOUT Celery: `flush_notifications` and `scan_sla`
are plain management commands runnable from cron. These thin tasks exist so
a Celery deployment gets the same behavior on a schedule with zero extra
config. If celery is not installed the imports degrade to a no-op module.

Suggested beat schedule (in the project-level celery app):

    from celery.schedules import crontab
    app.conf.beat_schedule = {
        "flush-notifications": {
            "task": "pen.workflow.flush_notifications",
            "schedule": 60.0,          # every minute
        },
        "scan-sla": {
            "task": "pen.workflow.scan_sla",
            "schedule": 300.0,         # every 5 minutes
        },
    }
"""
from __future__ import annotations

try:
    from celery import shared_task
except ImportError:  # pragma: no cover - Celery is optional by design
    def shared_task(*dargs, **dkwargs):
        def decorator(func):
            return func
        # Support both @shared_task and @shared_task(...)
        if dargs and callable(dargs[0]):
            return dargs[0]
        return decorator


@shared_task(name="pen.workflow.flush_notifications")
def flush_notifications_task(limit: int = 100) -> dict:
    """Deliver pending outbox rows; never raises (logged + counted)."""
    from django.core.management import call_command

    call_command("flush_notifications", limit=limit)
    return {"status": "ok"}


@shared_task(name="pen.workflow.scan_sla")
def scan_sla_task() -> dict:
    """Run one SLA scan pass; never raises (logged + counted)."""
    from django.core.management import call_command

    call_command("scan_sla")
    return {"status": "ok"}
