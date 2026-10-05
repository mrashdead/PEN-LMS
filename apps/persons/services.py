from __future__ import annotations

import logging
from typing import Optional

from django.conf import settings
from django.db import IntegrityError, transaction

from apps.core.utils import english_numbers
from apps.persons.models import Person, PersonTypeAssignment, StudentGuardian
from apps.persons.validation import is_valid_iranian_mobile, national_code_error

logger = logging.getLogger(__name__)

#: Roles that may read the full (unmasked) identity of any person.
PERSON_DETAIL_ELEVATED_ROLES = {"manager", "hr", "workflow_admin"}


def student_account_creation_missing_fields(person) -> list[str]:
    """Return requirements matching the manual student-definition form."""
    missing = []
    required_values = (
        ("نام", person.first_name),
        ("نام خانوادگی", person.last_name),
    )
    for label, value in required_values:
        if not (value or "").strip():
            missing.append(label)

    if national_code_error(person.national_code, require_location=True):
        missing.append("کد ملی معتبر")
    if not is_valid_iranian_mobile(english_numbers(person.mobile)):
        missing.append("شماره همراه دانش‌آموز معتبر")
    if person.gender not in dict(Person.Gender.choices):
        missing.append("جنسیت")

    profile = getattr(person, "student_profile", None)
    parents = {
        "father": {
            "label": "پدر",
            "first_name": getattr(profile, "father_first_name", "") or "",
            "last_name": getattr(profile, "father_last_name", "") or "",
            "phone": getattr(profile, "father_phone", "") or "",
        },
        "mother": {
            "label": "مادر",
            "first_name": getattr(profile, "mother_first_name", "") or "",
            "last_name": getattr(profile, "mother_last_name", "") or "",
            "phone": getattr(profile, "mother_phone", "") or "",
        },
    }
    links = StudentGuardian.objects.filter(
        student=person,
        is_active=True,
        is_deleted=False,
        relation__in=("father", "mother"),
    ).select_related("guardian")
    for link in links:
        parent = parents.get(link.relation)
        if parent is None:
            continue
        guardian = link.guardian
        parent["first_name"] = parent["first_name"] or guardian.first_name
        parent["last_name"] = parent["last_name"] or guardian.last_name
        parent["phone"] = parent["phone"] or link.phone_override or guardian.mobile

    valid_parent_phone_found = False
    invalid_parent_phones = []
    missing_parent_names = []
    for parent in parents.values():
        phone = english_numbers(parent["phone"]).strip()
        if not phone:
            continue
        if not is_valid_iranian_mobile(phone):
            invalid_parent_phones.append(parent["label"])
            continue
        valid_parent_phone_found = True
        if not parent["first_name"].strip():
            missing_parent_names.append(f"نام {parent['label']}")
        if not parent["last_name"].strip():
            missing_parent_names.append(f"نام خانوادگی {parent['label']}")
    if not valid_parent_phone_found:
        missing.append("نام، نام خانوادگی و شماره همراه معتبرِ حداقل یکی از والدین")
    else:
        if invalid_parent_phones:
            missing.append(
                "شماره همراه معتبر " + " و ".join(invalid_parent_phones)
            )
        missing.extend(missing_parent_names)

    return list(dict.fromkeys(missing))


def can_view_full_person_detail(user, person) -> bool:
    """
    بول «حافظ کامل» — آیا این کاربر می‌تواند جزئیات هویتی کامل (کد ملی،
    آدرس، تماس) شخص هدف را ببیند؟

    مجاز: سوپرایوزر؛ نقش‌های ارتقائی؛ خودِ شخص.
    هر کس دیگری باید نسخه‌ی ماسک‌شده را ببیند (رفع B1).
    """
    if user is None or not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    # Belt-and-braces: the seeded Django group permission "view_person_detail"
    # is honoured even if the business role isn't elevated (an HR user added
    # to the گروه manager without a role code assignment, for example).
    try:
        if user.has_perm("persons.view_person_detail"):
            return True
    except Exception:  # pragma: no cover
        pass
    try:
        roles = user.role_codes()
    except Exception:  # pragma: no cover - defensive (AnonymousUser never here)
        return False
    if roles & PERSON_DETAIL_ELEVATED_ROLES:
        return True
    if person is not None and person.user_id == user.pk:
        return True
    # Custodian-by-law: an ACTIVE guardian link makes the FULL identity of the
    # ward visible (name, national code, contact) — the intake contract. The
    # check is per-row, never role-wide, so a guardian still sees strangers
    # masked.
    if person is not None and "guardian" in roles:
        self_person = getattr(user, "person", None)
        if self_person is not None and StudentGuardian.objects.filter(
            guardian=self_person, student=person,
            is_active=True, is_deleted=False,
        ).exists():
            return True
    return False


def mask_identifier(value: str) -> str:
    """3 رقم اول + ماسک + 2 رقم آخر (برای کد ملی/موبایل/تلفن)."""
    v = str(value or "")
    if not v:
        return v
    if len(v) <= 5:
        return "*" * len(v)
    return f"{v[:3]}{'*' * (len(v) - 5)}{v[-2:]}"


def mask_email(value: str) -> str:
    v = str(value or "")
    if not v:
        return v
    local, sep, domain = v.partition("@")
    if not sep:
        return "***"
    return f"{local[:1]}***@{domain[:1]}***"


def mask_address(value: str) -> str:
    return "پنهان" if str(value or "").strip() else ""


def persons_visible_to(user):
    """
    QuerySet of persons this user may address through the persons API (B1).

    Replaces the previous "everyone active" catch-all that let a student
    enumerate every profile:

      - elevated / superuser      → all persons
      - teacher                   → themselves + all active students
                                    (needed for class/enrollment pickers)
      - employee                  → themselves + all active persons (staff dir)
      - student / other end-users → themselves only

    PII is still masked in the serializers for anyone who is not a full
    custodian of the specific row, so this scoping and the masking are
    complementary layers.
    """
    from django.db import models as dj_models

    if user is None or not getattr(user, "is_authenticated", False):
        return Person.objects.none()
    if getattr(user, "is_superuser", False):
        return Person.objects.all()

    roles = user.role_codes()
    self_person = getattr(user, "person", None)

    if roles & PERSON_DETAIL_ELEVATED_ROLES:
        return Person.objects.all()

    # Everyone's own record, when they have one.
    own = {"pk": self_person.pk} if self_person is not None else {"pk": None}

    if "teacher" in roles or "employee" in roles:
        # Staff directory: themselves + the active population they work with.
        return Person.objects.filter(
            dj_models.Q(**own) | dj_models.Q(is_active=True)
        )

    if "guardian" in roles:
        # A guardian sees themselves + ONLY their own wards (the docstring's
        # promise, previously unimplemented). No ward link → no rows beyond
        # their own record, so a parent account can never enumerate students.
        from apps.academics.scoping import ward_student_ids_for

        wards = ward_student_ids_for(user)
        return Person.objects.filter(
            dj_models.Q(**own) | dj_models.Q(pk__in=wards)
        )

    # student / unknown end-user role → only their own record.
    return Person.objects.filter(**own)


class PersonServiceError(Exception):
    """Base exception for Person service."""


class DuplicateNationalCodeError(PersonServiceError):
    """کد ملی (یا کد دانش‌آموزی/پرسنلی) تکراری در میان اشخاص زنده."""


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
        password: Optional[str] = None,
        grant_role: Optional[str] = None,
    ) -> Person:
        """ثبت شخص جدید و در صورت درخواست، ساخت حساب کاربری."""
        # Soft-deleted twins keep their unique key in the DB only through the
        # partial (live-only) constraints — a normal create() on a duplicate
        # would surface as a raw IntegrityError (HTTP 500). Map it to a
        # caller-friendly 400 first (B5).
        normalized_nc = english_numbers(national_code).strip()
        national_error = national_code_error(normalized_nc, require_location=True)
        if national_error:
            raise PersonServiceError(national_error)
        normalized_mobile = english_numbers(mobile).strip()
        if not is_valid_iranian_mobile(normalized_mobile):
            raise PersonServiceError("شماره موبایل باید دقیقاً ۱۱ رقم و با ۰۹ شروع شود.")
        if Person.objects.filter(national_code=normalized_nc, is_deleted=False).exists():
            raise DuplicateNationalCodeError(
                "شخصی با این کد ملی از قبل ثبت شده است."
            )
        try:
            person = Person.objects.create(
                national_code=normalized_nc,
                first_name=first_name,
                last_name=last_name,
                father_name=father_name,
                birth_date=birth_date,
                gender=gender,
                mobile=normalized_mobile,
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
        except IntegrityError as exc:
            # Pre-check passed but another transaction won the race on one of
            # the live-only unique keys (national/student/employee code).
            raise DuplicateNationalCodeError(
                "کد ملی یا کد دانش‌آموزی/پرسنلی تکراری است."
            ) from exc
        if auto_create_user:
            self._create_user_for_person(person, password=password, grant_role=grant_role)
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
        if person.has_type(Person.Type.STUDENT):
            missing = student_account_creation_missing_fields(person)
            if missing:
                raise PersonServiceError(
                    "اطلاعات لازم برای ساخت حساب کامل نیست: " + "، ".join(missing)
                )
        self._create_user_for_person(person, username=username, password=password)
        logger.info("User created for person %s %s by %s", person.first_name, person.last_name, created_by)
        return person

    def _create_user_for_person(
        self,
        person: Person,
        username: Optional[str] = None,
        password: Optional[str] = None,
        grant_role: Optional[str] = None,
    ) -> None:
        from apps.accounts.models import User

        final_username = english_numbers(username or person.national_code).strip()
        final_password = english_numbers(password or person.national_code).strip()

        # The national code is the stable default login identifier. Never
        # silently suffix it: a collision must be reported and the enclosing
        # transaction must roll back instead of creating a surprising login.
        if not username and User.objects.filter(username=final_username).exists():
            raise PersonServiceError(
                "نام کاربری پیش‌فرض (کد ملی) قبلاً استفاده شده است."
            )
        if username:
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

        # Provision roles/groups for EVERY effective type — primary type plus
        # time-bound additional assignments (criterion §13-1: a teacher who is
        # also an employee must get BOTH roles from ONE Person row).
        role_map = {
            Person.Type.STUDENT: "student",
            Person.Type.TEACHER: "teacher",
            Person.Type.EMPLOYEE: "employee",
            # A guardian gets the read-mostly parent role. It grants NOTHING by
            # itself — rows arrive only through an active StudentGuardian link
            # (see apps.academics.scoping + apps.persons.services).
            Person.Type.GUARDIAN: "guardian",
        }
        group_map = {
            Person.Type.STUDENT: "دانش‌آموز",
            Person.Type.TEACHER: "معلم / مدرس",
            Person.Type.EMPLOYEE: "کارمند",
            Person.Type.GUARDIAN: "والدین",
        }
        from django.contrib.auth.models import Group

        for type_code in sorted(person.type_codes()):
            role_code = role_map.get(type_code)
            if role_code:
                user.assign_role(role_code, assigned_by=person.registered_by)
            group_name = group_map.get(type_code)
            if group_name:
                group = Group.objects.filter(name=group_name).first()
                if group:
                    user.groups.add(group)
                else:
                    logger.warning(
                        "Group '%s' not found (run `seed_groups` first) for user %s",
                        group_name, user.username,
                    )

        # Optional extra role (e.g. creating a manager/supervisor: person_type
        # is employee, grant_role adds the leadership role). Validated against
        # the seeded Role table so a typo can't silently no-op.
        if grant_role:
            from apps.accounts.models import Role

            role = Role.objects.filter(
                code=grant_role.strip().lower(), is_active=True, is_deleted=False
            ).first()
            if role is None:
                raise PersonServiceError(f"نقش نامعتبر: {grant_role}")
            user.assign_role(role.code, assigned_by=person.registered_by)

        person.user = user
        person.save(update_fields=["user", "updated_at"])

    def add_person_type(
        self,
        *,
        person: Person,
        type_code: str,
        valid_from=None,
        valid_to=None,
        assigned_by=None,
        provision_user_roles: bool = True,
    ) -> PersonTypeAssignment:
        """
        افزودن نوع دوم به یک شخص (مثلاً مدرسِ کارمند). اگر شخص حساب داشته
        باشد، نقش/گروه متناظر هم بلافاصله اعطا می‌شود.
        """
        type_code = (type_code or "").strip().lower()
        if type_code not in dict(Person.Type.choices):
            raise PersonServiceError(f"نوع نامعتبر: {type_code}")
        assignment, created = PersonTypeAssignment.objects.update_or_create(
            person=person,
            type=type_code,
            is_deleted=False,
            defaults={
                "is_active": True,
                "valid_from": valid_from,
                "valid_to": valid_to,
                "assigned_by": assigned_by,
            },
        )
        if provision_user_roles and person.user_id and created:
            role_map = {
                Person.Type.STUDENT: "student",
                Person.Type.TEACHER: "teacher",
                Person.Type.EMPLOYEE: "employee",
                Person.Type.GUARDIAN: "guardian",
            }
            role_code = role_map.get(type_code)
            if role_code:
                person.user.assign_role(role_code, assigned_by=assigned_by)
        logger.info(
            "person %s += type %s (%s)", person.pk, type_code,
            "created" if created else "updated",
        )
        return assignment

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

#: Module-level singleton — views and tests import this.
person_service = PersonService()
