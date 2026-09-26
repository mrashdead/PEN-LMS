"""
Seed the call-subject catalog — the normalized picklist for
``InboundCall.subject`` so the report's "by subject" breakdown is stable and
filterable, instead of free-text drift.

    python manage.py seed_call_subjects

Idempotent: stored as ``CallSubject`` rows (one table = one source of truth;
the model is intentionally tiny so the report can JOIN it).
"""
from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.calls.models import CallSubject

CALL_SUBJECTS: list[dict[str, Any]] = [
    {"code": "registration", "name": "ثبت‌نام و هزینه‌ها", "department": "آموزش"},
    {"code": "tuition", "name": "استعلام شهریه", "department": "مالی"},
    {"code": "attendance", "name": "غیبت و حضور", "department": "آموزش"},
    {"code": "grades", "name": "نتیجه و کارنامه", "department": "آموزش"},
    {"code": "schedule", "name": "تغییر زمان کلاس", "department": "آموزش"},
    {"code": "placement", "name": "تعیین سطح", "department": "پذیرش"},
    {"code": "admission", "name": "پذیرش و مشاوره", "department": "پذیرش"},
    {"code": "complaint", "name": "انتقاد و شکایت", "department": "مدیریت"},
    {"code": "certificate", "name": "گواهی اتمام دوره", "department": "آموزش"},
    {"code": "refund", "name": "عودت وجه", "department": "مالی"},
    {"code": "general", "name": "سایر موارد", "department": ""},
]


class Command(BaseCommand):
    help = "Seed the call-subject catalog (idempotent)"

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        for spec in CALL_SUBJECTS:
            obj, created = CallSubject.objects.get_or_create(
                code=spec["code"],
                defaults={"name": spec["name"], "department": spec["department"]},
            )
            if not created and (obj.name != spec["name"] or obj.department != spec["department"]):
                obj.name = spec["name"]
                obj.department = spec["department"]
                obj.save(update_fields=["name", "department", "updated_at"])
                self.stdout.write(f"[updated] {obj.code}")
            else:
                self.stdout.write(
                    f"[{'created' if created else 'exists'}] {obj.code}"
                )
        self.stdout.write(self.style.SUCCESS("call subjects ready"))
