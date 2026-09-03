from __future__ import annotations

import logging
from typing import Optional

from django.conf import settings
from django.db import transaction

from apps.core.utils import english_numbers
from apps.persons.models import Person

logger = logging.getLogger(__name__)


class PersonServiceError(Exception):
    """Base exception for Person service."""


class PersonService:
    """
    سرویس مدیریت اشخاص.

    کد ملی و شماره تماس همیشه به اعداد انگلیسی نرمال می‌شوند تا
    کاربر با هر صفحه‌کلیدی بتواند وارد شود.
    """

    @transaction.atomic
    def create_person(
        self,
        *,
        national_code: str,
        first_name: str,
        last_name: str,
        person_type: str,
        mobile: str,
        father_name: str = "",
        birth_date=None,
        gender: str = "unspecified",
        email: str = "",
        phone: str = "",
        address: str = "",
        postal_code: str = "",
        student_code: Optional[str] = None,
        employee_code: Optional[str] = None,
        department: str = "",
        job_title: str = "",
        hire_date=None,
        photo=None,
        registered_by: Optional[settings.AUTH_USER_MODEL] = None,
        auto_create_user: bool = False,
    ) -> Person:
        """ثبت شخص جدید و در صورت درخواست، ساخت حساب کاربری."""
        person = Person.objects.create(
            national_code=english_numbers(national_code).strip(),
            first_name=first_name,
            last_name=last_name,
            father_name=father_name,
            birth_date=birth_date,
            gender=gender,
            mobile=english_numbers(mobile).strip(),
            email=email,
            phone=phone,
            address=address,
            postal_code=english_numbers(postal_code).strip(),
            person_type=person_type,
            student_code=english_numbers(student_code).strip() if student_code else None,
            employee_code=english_numbers(employee_code).strip() if employee_code else None,
            department=department,
            job_title=job_title,
            hire_date=hire_date,
            photo=photo,
            registered_by=registered_by,
            is_active=True,
        )
        if auto_create_user:
            self._create_user_for_person(person)
        logger.info("Person created: %s %s (%s) by %s", first_name, last_name, person_type, registered_by)
        return person

    @transaction.atomic
    def create_user_for_person(
        self,
        person_id: str,
        *,
        username: Optional[str] = None,
        password: Optional[str] = None,
        created_by: Optional[settings.AUTH_USER_MODEL] = None,
    ) -> Person:
        """ساخت User برای Person موجود. پیش‌فرض username/password = کد ملی نرمال‌شده."""
        person = Person.objects.select_for_update().get(pk=person_id)
        if person.user_id:
            raise PersonServiceError("این شخص قبلاً کاربر دارد.")
        self._create_user_for_person(person, username=username, password=password)
        logger.info("User created for person %s %s by %s", person.first_name, person.last_name, created_by)
        return person

    def _create_user_for_person(
        self,
        person: Person,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        from apps.accounts.models import User

        final_username = english_numbers(username or person.national_code).strip()
        final_password = english_numbers(password or person.national_code).strip()

        # یگانه‌سازی name کاربری
        base = final_username
        suffix = 1
        while User.objects.filter(username=final_username).exists():
            final_username = f"{base}_{suffix}"
            suffix += 1

        user = User.objects.create_user(
            username=final_username,
            email=person.email or "",
            password=final_password,
            first_name=person.first_name,
            last_name=person.last_name,
            is_active=True,
        )

        role_map = {
            Person.Type.STUDENT: "student",
            Person.Type.TEACHER: "teacher",
            Person.Type.EMPLOYEE: "employee",
            Person.Type.PARENT: "parent",
        }
        role_code = role_map.get(person.person_type)
        if role_code:
            user.assign_role(role_code, assigned_by=person.registered_by)

        group_map = {
            Person.Type.STUDENT: "دانش‌آموز",
            Person.Type.TEACHER: "معلم / مدرس",
            Person.Type.EMPLOYEE: "کارمند",
            Person.Type.PARENT: "والدین",
        }
        group_name = group_map.get(person.person_type)
        if group_name:
            from django.contrib.auth.models import Group

            group = Group.objects.filter(name=group_name).first()
            if group:
                user.groups.add(group)
            else:
                logger.warning("Group '%s' not found (run `seed_groups` first) for user %s", group_name, user.username)

        person.user = user
        person.save(update_fields=["user", "updated_at"])

    def _generate_temp_password(self) -> str:
        import secrets
        import string

        chars = string.ascii_letters + string.digits
        return "".join(secrets.choice(chars) for _ in range(12))


class PersonLoginSupport:
    """ابزارهای پشتیبانی ورود — نرمال‌سازی و بازنشانی رمز."""

    @staticmethod
    def normalize_credentials(value: str) -> str:
        return english_numbers(value).strip()

    @classmethod
    def reset_person_password(cls, person: Person) -> None:
        """بازنشانی رمز و نام کاربری یک Person موجود به کد ملی نرمال‌شده."""
        if not person.user_id:
            raise PersonServiceError("این شخص هنوز کاربر ندارد.")
        person.user.set_password(english_numbers(person.national_code).strip())
        person.user.username = english_numbers(person.user.username).strip()
        person.user.save(update_fields=["password", "username", "updated_at"])