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

from apps.accounts.permission_policy import GROUPS


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
