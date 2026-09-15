"""
Seed Django Groups with model permissions.

Run after migrations:
    python manage.py seed_groups

Business roles are checked by apps.core.permissions. These groups provide the
second, model-level authorization layer used by API views.
"""
from __future__ import annotations

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction


COMMON = [
    "accounts.view_user",
    "persons.view_person",
    "tasks.view_workflowtask",
]

GROUPS: dict[str, dict[str, object]] = {
    "مدیر سیستم": {
        "codename": "admin",
        "priority": 0,
        "perms": "*",
    },
    "مدیر مؤسسه": {
        "codename": "manager",
        "priority": 10,
        "perms": COMMON + [
            "accounts.add_user",
            "persons.view_person_detail",
            "persons.view_person_list",
            "persons.add_person",
            "persons.change_person",
            "persons.view_studentparent",
            "persons.add_studentparent",
            "persons.change_studentparent",
            "persons.delete_studentparent",
            "persons.view_grades_report",
            "persons.view_attendance_report",
            "persons.view_financial_report",
            "workflow.view_workflowdefinition",
            "workflow.view_instance",
            "workflow.add_instance",
            "workflow.change_instance",
            "workflow.view_actionlog",
            "workflow.manage_workflow_definition",
            "workflow.view_all_instances",
            "workflow.approve_instance",
            "workflow.cancel_any_instance",
            "academics.view_academicterm",
            "academics.add_academicterm",
            "academics.change_academicterm",
            "academics.view_classgroup",
            "academics.add_classgroup",
            "academics.change_classgroup",
            "academics.view_all_class_groups",
            "academics.manage_class_group",
            "academics.view_classenrollment",
            "academics.add_classenrollment",
            "academics.change_classenrollment",
            "academics.delete_classenrollment",
            "academics.manage_term",
            "academics.manage_enrollment",
            "forms.view_formschema",
            "forms.add_formschema",
            "forms.change_formschema",
            "forms.view_formsubmission",
            "forms.add_formsubmission",
            "forms.change_formsubmission",
            "forms.view_formattachment",
            "forms.add_formattachment",
            "forms.view_formcomment",
            "forms.add_formcomment",
        ],
    },
    "کارمند": {
        "codename": "employee",
        "priority": 100,
        "perms": COMMON + [
            "persons.view_person_list",
            "workflow.view_instance",
            "workflow.add_instance",
            "academics.view_academicterm",
            "academics.view_classgroup",
            "academics.view_classenrollment",
        ],
    },
    "معلم / مدرس": {
        "codename": "teacher",
        "priority": 40,
        "perms": COMMON + [
            "persons.view_person_detail",
            "persons.view_person_list",
            "persons.view_grades_report",
            "persons.view_attendance_report",
            "workflow.view_instance",
            "workflow.add_instance",
            "academics.view_academicterm",
            "academics.view_classgroup",
            "academics.view_classenrollment",
        ],
    },
    "دانش‌آموز": {
        "codename": "student",
        "priority": 90,
        "perms": COMMON + [
            "workflow.view_instance",
            "academics.view_academicterm",
            "academics.view_classgroup",
            "academics.view_classenrollment",
        ],
    },
}


class Command(BaseCommand):
    help = "Seed default Django Groups with model permissions (idempotent)"

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        for group_name, config in GROUPS.items():
            group, created = Group.objects.get_or_create(name=group_name)
            perms_config = config["perms"]

            if perms_config == "*":
                group.permissions.set(Permission.objects.all())
                self.stdout.write(
                    f"[{'created' if created else 'updated'}] {group_name} (all permissions)"
                )
                continue

            perms_to_add: list[Permission] = []
            missing: list[str] = []
            for perm_str in perms_config:
                try:
                    app_label, codename = perm_str.strip().split(".", 1)
                    permission = Permission.objects.get(
                        content_type__app_label=app_label,
                        codename=codename,
                    )
                    perms_to_add.append(permission)
                except (Permission.DoesNotExist, ValueError):
                    missing.append(perm_str)

            group.permissions.set(perms_to_add)
            if missing:
                self.stdout.write(
                    self.style.WARNING(
                        f"[{group_name}] permissions not found: {missing}"
                    )
                )
            self.stdout.write(
                f"[{'created' if created else 'updated'}] "
                f"{group_name} — {len(perms_to_add)} permission(s)"
            )

        self.stdout.write(self.style.SUCCESS("groups ready"))
