"""Application service for the Bootstrap/Django person definition wizard."""
from __future__ import annotations

from typing import Any

from django.db import transaction

from apps.persons import hierarchy
from apps.persons.models import Person, StaffProfile, StudentProfile
from apps.persons.services import PersonService, PersonServiceError


class PersonDefinitionPermissionError(PersonServiceError):
    """The actor is not allowed to create the requested target/role."""


class PersonDefinitionValidationError(PersonServiceError):
    """A valid Django form was bypassed or a cross-field rule failed."""


class PersonDefinitionService:
    """Create a Person, role-specific profile and login atomically."""

    def __init__(self, *, person_service: PersonService | None = None):
        self.person_service = person_service or PersonService()

    @transaction.atomic
    def create(self, *, actor, cleaned_data: dict[str, Any]) -> Person:
        target = str(cleaned_data.get("target") or "").strip().lower()
        roles = set(actor.role_codes()) if hasattr(actor, "role_codes") else set()
        is_superuser = bool(getattr(actor, "is_superuser", False))
        if not hierarchy.can_create(roles, target, is_superuser=is_superuser):
            raise PersonDefinitionPermissionError("شما مجاز به ایجاد این نوع کاربر نیستید.")

        employee_kind = cleaned_data.get("employee_kind") or "ordinary"
        grant_role = None
        if target == "employee" and employee_kind == "supervisor":
            grant_role = "supervisor"
        if target == "manager":
            grant_role = "manager"
        if grant_role and not hierarchy.can_grant_role(
            roles, grant_role, is_superuser=is_superuser
        ):
            raise PersonDefinitionPermissionError("شما مجاز به اعطای این نقش نیستید.")

        if target in {"employee", "manager"} and not cleaned_data.get("password"):
            raise PersonDefinitionValidationError(
                "برای کارمند و مدیریت، کلمه عبور اختصاصی الزامی است."
            )
        if target in {"employee", "manager"} and not cleaned_data.get("job_title"):
            raise PersonDefinitionValidationError(
                "عنوان سمت / پست سازمانی برای کارمند و مدیریت الزامی است."
            )

        person_type = Person.Type.STUDENT if target == "student" else (
            Person.Type.TEACHER if target == "teacher" else Person.Type.EMPLOYEE
        )
        national_code = cleaned_data["national_code"]
        person = self.person_service.create_person(
            national_code=national_code,
            first_name=cleaned_data["first_name"],
            last_name=cleaned_data["last_name"],
            person_type=person_type,
            mobile=cleaned_data["phone_number"],
            email=cleaned_data.get("email") or "",
            birth_date=self._as_date(cleaned_data.get("birth_date")),
            gender=cleaned_data.get("gender") or Person.Gender.NOT_SPECIFIED,
            job_title=cleaned_data.get("job_title") or "",
            student_code=f"STU-{national_code}" if target == "student" else None,
            employee_code=f"EMP-{national_code}" if target in {"teacher", "employee", "manager"} else None,
            registered_by=actor,
            auto_create_user=True,
            password=cleaned_data.get("password") or None,
            grant_role=grant_role,
        )

        if target == "student":
            parents = cleaned_data
            StudentProfile.objects.create(
                person=person,
                father_first_name=parents.get("father_first_name") or "",
                father_last_name=parents.get("father_last_name") or "",
                father_phone=parents.get("father_phone_number") or "",
                mother_first_name=parents.get("mother_first_name") or "",
                mother_last_name=parents.get("mother_last_name") or "",
                mother_phone=parents.get("mother_phone_number") or "",
                is_custody_case=bool(parents.get("is_custody_case")),
                custody_note=parents.get("custody_note") or "",
            )
        else:
            StaffProfile.objects.create(
                person=person,
                kind=(StaffProfile.Kind.TEACHING if target == "teacher"
                      else StaffProfile.Kind.ADMINISTRATIVE),
                specialization=cleaned_data.get("specialization") or "",
            )
        return person

    @staticmethod
    def _as_date(value: Any):
        if not value:
            return None
        from apps.persons.onboarding import PersonOnboardingService

        return PersonOnboardingService._as_date(value)
