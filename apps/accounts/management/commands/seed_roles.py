# apps/accounts/management/commands/seed_roles.py
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import Role

DEFAULT_ROLES: list[dict[str, object]] = [
    {"code": "employee", "name": "کارمند", "priority": 100},
    {"code": "manager", "name": "مدیر مستقیم", "priority": 50},
    {"code": "hr", "name": "منابع انسانی", "priority": 40},
    {"code": "workflow_admin", "name": "مدیر فرآیند", "priority": 10},
]


class Command(BaseCommand):
    help = "Seed default workflow roles (idempotent)"

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        for item in DEFAULT_ROLES:
            obj, created = Role.objects.update_or_create(
                code=item["code"],
                defaults={
                    "name": item["name"],
                    "priority": item["priority"],
                    "is_active": True,
                    "is_deleted": False,
                },
            )
            state = "created" if created else "updated"
            self.stdout.write(f"[{state}] {obj.code}")
        self.stdout.write(self.style.SUCCESS("roles ready"))
