"""Retry failed attendance-form projections into typed education records."""
from __future__ import annotations

import logging

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone

from apps.forms.models import FormSubmission
from apps.forms.services import FormSubmissionService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Reconcile submitted attendance forms that are not projected yet"

    def add_arguments(self, parser) -> None:
        parser.add_argument("--limit", type=int, default=50)
        parser.add_argument("--max-attempts", type=int, default=5)

    def handle(self, *args, **options) -> None:
        if min(options["limit"], options["max_attempts"]) < 1:
            raise CommandError("limit and max-attempts must be positive")

        now = timezone.now()
        with transaction.atomic():
            qs = FormSubmission.objects.filter(
                form_schema__slug="attendance",
                projection_status__in=(
                    FormSubmission.ProjectionStatus.PENDING,
                    FormSubmission.ProjectionStatus.FAILED,
                ),
                projection_attempts__lt=options["max_attempts"],
                projection_next_attempt_at__lte=now,
                submitted_at__isnull=False,
            ).select_related("form_schema", "submitted_by").order_by(
                "projection_next_attempt_at", "submitted_at",
            )
            if connection.features.has_select_for_update_skip_locked:
                qs = qs.select_for_update(skip_locked=True)
            elif connection.features.has_select_for_update:
                qs = qs.select_for_update()
            rows = list(qs[:options["limit"]])
            service = FormSubmissionService()
            for submission in rows:
                submission.projection_status = FormSubmission.ProjectionStatus.PROCESSING
                submission.save(update_fields=["projection_status", "updated_at"])
                service._project_into_education(submission, submission.submitted_by)

        completed = sum(
            row.projection_status == FormSubmission.ProjectionStatus.COMPLETE
            for row in rows
        )
        failed = len(rows) - completed
        logger.info(
            "education_projection_reconciliation attempted=%s completed=%s failed=%s",
            len(rows), completed, failed,
        )
        self.stdout.write(self.style.SUCCESS(
            f"education projections reconciled: {completed} completed, {failed} failed"
        ))
