"""
Seed default Django Groups with appropriate permissions.
Idempotent — safe to run multiple times.

Run: python manage.py seed_groups
"""

from __future__ import annotations

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction

# ─── Group definitions ──────────────────────────────────────────
# Each group has a list of permission codenames to grant.
# Format: "app_label.codename" — e.g. "persons.view_person"

GROUPS: dict[str, dict[str, object]] = {
    "مدیر سیستم": {
        "codename": "admin",
        "priority": 0,
        "perms": "*",  # full access via is_superuser
    },
    "مدیر مؤسسه": {
        "codename": "manager",
        "priority": 10,
        "perms": [
            "persons.view_person",
            "persons.view_person_detail",
            "persons.view_person_list",
            "persons.add_person",
            "persons.change_person",
            "persons.create_user_for_person",
            "persons.view_grades_report",
            "persons.view_attendance_report",
            "persons.view_financial_report",
            "workflow.view_workflow_definition",
            "workflow.manage_workflow_definition",
            "workflow.view_instance",
            "workflow.view_all_instances",
            "workflow.add_instance",
            "workflow.approve_instance",
            "workflow.cancel_any_instance",
            "academics.manage_term",
            "academics.manage_class_group",
            "academics.view_all_class_groups",
            "academics.manage_enrollment",
        ],
    },
    "کارمند": {
        "codename": "employee",
        "priority": 100,
        "perms": [
            "persons.view_person",
            "persons.view_person_list",
            "workflow.view_instance",
            "workflow.add_instance",
            "academics.view_classgroup",
            "academics.view_classenrollment",
        ],
    },
    "معلم / مدرس": {
        "codename": "teacher",
        "priority": 40,
        "perms": [
            "persons.view_person",
            "persons.view_person_detail",
            "persons.view_person_list",
            "persons.view_grades_report",
            "persons.view_attendance_report",
            "workflow.view_instance",
            "workflow.add_instance",
            "academics.view_classgroup",
            "academics.view_classenrollment",
        ],
    },
    "دانش‌آموز": {
        "codename": "student",
        "priority": 90,
        "perms": [
            "persons.view_person",
            "workflow.view_instance",
            "academics.view_classgroup",
            "academics.view_classenrollment",
        ],
    },
    "والدین": {
        "codename": "parent",
        "priority": 80,
        "perms": [
            "persons.view_person",
            "persons.view_attendance_report",
            "academics.view_classgroup",
            "academics.view_classenrollment",
        ],
    },
}


class Command(BaseCommand):
    help = "Seed default Django Groups with permissions (idempotent)"

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        for group_name, config in GROUPS.items():
            group, created = Group.objects.get_or_create(name=group_name)

            if config["perms"] == "*":
                # Admin: mark as superuser group — permissions are irrelevant
                self.stdout.write(f"[{'created' if created else 'updated'}] {group_name} (full access)")
                continue

            # Resolve permission objects
            perms_to_add: list[Permission] = []
            missing: list[str] = []
            for perm_str in config["perms"]:
                try:
                    app_label, codename = perm_str.strip().split(".")
                    perm = Permission.objects.get(
                        content_type__app_label=app_label,
                        codename=codename,
                    )
                    perms_to_add.append(perm)
                except Permission.DoesNotExist:
                    missing.append(perm_str)
                except ValueError:
                    missing.append(perm_str)

            if missing:
                self.stdout.write(
                    self.style.WARNING(
                        f"  [{group_name}] Permissions not found (will be available after migrate): {missing}"
                    )
                )

            group.permissions.set(perms_to_add)
            state = "created" if created else "updated"
            self.stdout.write(
                f"[{state}] {group_name} — {len(perms_to_add)} permission(s)"
            )

        self.stdout.write(self.style.SUCCESS("groups ready"))
