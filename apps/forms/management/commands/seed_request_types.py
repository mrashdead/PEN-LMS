"""Seed the business request catalog used by the unified form pipeline."""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import Role
from apps.forms.management.commands.seed_form_schemas import SCHEMA_CATALOG
from apps.forms.models import RequestType
from apps.workflow.models import WorkflowDefinition


class Command(BaseCommand):
    help = "Create/update RequestType catalog entries from the form catalog"

    def add_arguments(self, parser) -> None:
        parser.add_argument("--force", action="store_true", help="Update existing catalog rows.")
        parser.add_argument("--dry-run", action="store_true", help="Validate without writing.")

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        rows = []
        for slug, item in SCHEMA_CATALOG.items():
            workflow = WorkflowDefinition.objects.filter(
                code=item.get("workflow_code"), is_active=True
            ).first() if item.get("workflow_code") else None
            rows.append((slug, item, workflow))
        missing = [slug for slug, item, workflow in rows if item.get("workflow_code") and workflow is None]
        if missing:
            self.stderr.write(
                "workflow definition(s) missing; run seed_form_workflows first: "
                + ", ".join(missing)
            )
            return
        if options["dry_run"]:
            for slug, _item, _workflow in rows:
                self.stdout.write(f"[dry-run] {slug}")
            return

        for slug, item, workflow in rows:
            code = item.get("request_type_code", slug)
            request_type, created = RequestType.objects.get_or_create(
                code=code,
                defaults={
                    "title": item["title"],
                    "description": item["description"],
                    "workflow_definition": workflow,
                    "metadata": item.get("metadata") or {},
                },
            )
            if options["force"] and not created:
                request_type.title = item["title"]
                request_type.description = item["description"]
                request_type.workflow_definition = workflow
                request_type.metadata = item.get("metadata") or {}
                request_type.is_active = True
                request_type.save(update_fields=[
                    "title", "description", "workflow_definition", "metadata", "is_active", "updated_at"
                ])
            request_type.allowed_roles.set(Role.objects.filter(code__in=item.get("allowed_roles", [])))
            self.stdout.write(f"[{'created' if created else 'ready'}] {code}")
        self.stdout.write(self.style.SUCCESS("request types ready"))
