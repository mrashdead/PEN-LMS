from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.core.utils import english_numbers
from apps.persons.models import Person


class Command(BaseCommand):
    help = "Normalize national-code usernames and reset default passwords for linked persons"

    @transaction.atomic
    def handle(self, *args, **options):
        updated = 0
        skipped = 0
        for person in Person.objects.select_related("user").filter(user__isnull=False):
            user = person.user
            national_code = english_numbers(person.national_code).strip()
            username = english_numbers(user.username).strip()
            changed = False

            # کاربرانی که username آن‌ها کد ملی یا نسخه فارسی آن است اصلاح شوند.
            if username == national_code or username != user.username and username.isdigit():
                if user.username != username:
                    user.username = username
                    changed = True

            # فقط حساب‌هایی که username برابر کد ملی است password پیش‌فرض دارند.
            # این رفتار برای داده‌های اولیه پروژه طراحی شده است.
            if username == national_code:
                user.set_password(national_code)
                changed = True

            if changed:
                user.save(update_fields=["username", "password", "updated_at"])
                updated += 1
            else:
                skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f"credentials normalized: {updated} updated, {skipped} unchanged"
        ))
