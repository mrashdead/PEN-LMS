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
    {"code": "student", "name": "دانش‌آموز", "priority": 90},
    {"code": "teacher", "name": "معلم / مدرس", "priority": 40},
    {"code": "parent", "name": "والدین", "priority": 80},
]


class Command(BaseCommand):
    help = "Seed default workflow roles (idempotent)"

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        for item in DEFAULT_ROLES:
            code = str(item["code"]).strip().lower()
            # The business key is unique only among live rows now (partial
            # unique index), so an explicit live-then-resurrect lookup is used
            # instead of update_or_create, which could raise
            # MultipleObjectsReturned when a soft-deleted twin exists.
            obj = (
                Role.objects.filter(code=code, is_deleted=False).first()
                or Role.all_objects.filter(code=code, is_deleted=True).first()
            )
            created = obj is None
            if created:
                obj = Role(code=code)
            obj.name = str(item["name"])
            obj.priority = item["priority"]
            obj.is_active = True
            obj.is_deleted = False
            obj.deleted_at = None
            obj.save()
            state = "created" if created else "updated"
            self.stdout.write(f"[{state}] {obj.code}")
        self.stdout.write(self.style.SUCCESS("roles ready"))
