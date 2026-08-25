from __future__ import annotations

import logging
from typing import Optional

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.persons.models import Person

logger = logging.getLogger(__name__)


class PersonServiceError(Exception):
    """Base exception for Person service."""


class PersonService:
    """
    سرویس مدیریت اشخاص — ایجاد Person و (اختیاری) User.
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
        registered_by: Optional[settings.AUTH_USER_MODEL] = None,  # type: ignore[valid-type]
        auto_create_user: bool = False,
    ) -> Person:
        """
        ثبت شخص جدید.

        اگر auto_create_user=True باشد و person_type اجازه دهد،
        یک User نیز برای شخص ساخته می‌شود.
        """
        person = Person.objects.create(
            national_code=national_code,
            first_name=first_name,
            last_name=last_name,
            father_name=father_name,
            birth_date=birth_date,
            gender=gender,
            mobile=mobile,
            email=email,
            phone=phone,
            address=address,
            postal_code=postal_code,
            person_type=person_type,
            student_code=student_code,
            employee_code=employee_code,
            department=department,
            job_title=job_title,
            hire_date=hire_date,
            photo=photo,
            registered_by=registered_by,
            is_active=True,
        )

        if auto_create_user:
            self._create_user_for_person(person)

        logger.info(
            "Person created: %s %s (%s) by %s",
            first_name,
            last_name,
            person_type,
            registered_by,
        )
        return person

    @transaction.atomic
    def create_user_for_person(
        self,
        person_id: str,
        *,
        username: Optional[str] = None,
        password: Optional[str] = None,
        created_by: Optional[settings.AUTH_USER_MODEL] = None,  # type: ignore[valid-type]
    ) -> Person:
        """
        ساخت User برای یک Person موجود.
        اگر username داده نشود، از کد ملی استفاده می‌کند.
        اگر password داده نشود، از کد ملی استفاده می‌کند.
        """
        person = Person.objects.select_for_update().get(pk=person_id)
        if person.user_id:
            raise PersonServiceError("این شخص قبلاً کاربر دارد.")

        self._create_user_for_person(person, username=username, password=password)
        logger.info(
            "User created for person %s %s by %s",
            person.first_name,
            person.last_name,
            created_by,
        )
        return person

    # ──────────────────────────────────────────────
    #  Internal
    # ──────────────────────────────────────────────

    def _create_user_for_person(
        self,
        person: Person,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        from apps.accounts.models import User

        final_username = username or person.national_code

        # Ensure unique username
        base = final_username
        suffix = 1
        while User.objects.filter(username=final_username).exists():
            final_username = f"{base}_{suffix}"
            suffix += 1

        final_password = password or person.national_code

        user = User.objects.create_user(
            username=final_username,
            email=person.email or "",
            password=final_password,
            first_name=person.first_name,
            last_name=person.last_name,
            is_active=True,
        )

        # Assign role based on person_type
        role_map = {
            Person.Type.STUDENT: "student",
            Person.Type.TEACHER: "teacher",
            Person.Type.EMPLOYEE: "employee",
            Person.Type.PARENT: "parent",
        }
        role_code = role_map.get(person.person_type)
        if role_code:
            try:
                user.assign_role(role_code, assigned_by=person.registered_by)
            except Exception as e:
                logger.warning("Could not assign role %s: %s", role_code, e)

        # Assign Django Group based on person_type
        group_map = {
            Person.Type.STUDENT: "دانش‌آموز",
            Person.Type.TEACHER: "معلم / مدرس",
            Person.Type.EMPLOYEE: "کارمند",
            Person.Type.PARENT: "والدین",
        }
        group_name = group_map.get(person.person_type)
        if group_name:
            try:
                from django.contrib.auth.models import Group
                group = Group.objects.get(name=group_name)
                user.groups.add(group)
                logger.info(
                    "User %s added to group '%s'",
                    user.username,
                    group_name,
                )
            except Group.DoesNotExist:
                logger.warning(
                    "Group '%s' not found (run `seed_groups` first) for user %s",
                    group_name,
                    user.username,
                )
            except Exception as e:
                logger.warning("Could not add user %s to group %s: %s", user.username, group_name, e)

        # Link person to user
        person.user = user
        person.save(update_fields=["user", "updated_at"])

    def _generate_temp_password(self) -> str:
        import secrets
        import string

        chars = string.ascii_letters + string.digits
        return "".join(secrets.choice(chars) for _ in range(12))
