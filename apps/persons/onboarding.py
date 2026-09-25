"""
Dynamic (multi-step) user onboarding.

Two responsibilities, both derived from ONE contract so the UI can never offer
a field the server will reject, and the server can never accept a field the UI
never showed:

  1. ``FIELD_SPECS`` — the per-target field profile used by step 2 of the
     create-user wizard (which extra sections/fields unlock once the actor has
     picked a role tier). ``GET /api/persons/onboarding/schema/?target=...``
     renders it; ``OnboardingSerializer`` re-validates against it.

  2. ``PersonOnboardingService`` — the ONLY sanctioned write path. It runs the
     hierarchy guard (``hierarchy.can_create`` / ``can_grant_role``) *inside*
     the transaction, then creates Person + profile rows + guardian links +
     User + roles atomically. A failure anywhere rolls the whole intake back,
     so there is no half-created student without a parent record.

Design notes
------------
* The step-1 role picker is filtered server-side by the actor's role set — the
  matrix in ``hierarchy.CREATE_MATRIX`` is the single source of truth; the UI
  merely renders ``allowed_targets_ordered()``.
* ``required`` on a field spec means "required *for that target*", not globally.
* Guardian intake is deliberately not a separate wizard: creating a student
  already collects father/mother, and a standalone guardian would need to pick
  which ward to link. ``target=guardian`` is therefore a *link-existing-student*
  flow (``guards_student`` field appears) rather than a new-person flow.
* Nothing here touches Django models; all persistence goes through
  ``PersonService`` so the soft-delete / unique-key collision handling written
  in the B5 round is inherited, not duplicated.
"""
from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, replace
from typing import Any, Optional

from django.db import transaction

from apps.persons import hierarchy
from apps.persons.models import (
    GuardianProfile,
    Person,
    StaffProfile,
    StudentGuardian,
    StudentProfile,
)
from apps.persons.services import PersonService, PersonServiceError

logger = logging.getLogger(__name__)

person_service = PersonService()


class OnboardingPermissionError(PersonServiceError):
    """Actor may not create this target/role (HTTP 403, not 400 — it is authz)."""


class OnboardingValidationError(PersonServiceError):
    """Required dynamic fields missing / invalid (HTTP 400)."""


# ─────────────────────────────────────────────────────────────────────────────
# 1) Field specs — step 2 of the wizard
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class FormField:
    """One input the step-2 form must render."""

    name: str
    label: str
    type: str = "text"          # text|tel|date|select|textarea|checkbox|number|repeater
    required: bool = False
    choices: tuple[tuple[str, str], ...] = ()
    help_text: str = ""
    #: Validators the server enforces too (kept declarative so UI + API agree).
    pattern: str = ""
    max_length: int = 0
    min: Optional[int] = None
    max: Optional[int] = None

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FormSection:
    """A group of fields (rendered as a card/step fragment by the UI)."""

    key: str
    label: str
    fields: tuple[FormField, ...] = ()
    #: A repeater section (guardians) renders N copies of ``fields``.
    repeatable: bool = False
    min_items: int = 0
    max_items: int = 1
    description: str = ""

    def to_json(self) -> dict[str, Any]:
        d = asdict(self)
        d["fields"] = [f.to_json() for f in self.fields]
        return d


# ── reusable field fragments ────────────────────────────────────────────────

_IDENT = (
    FormField("first_name", "نام", required=True, max_length=128),
    FormField("last_name", "نام خانوادگی", required=True, max_length=128),
    FormField(
        "national_code", "کد ملی", required=True, type="text",
        pattern=r"^\d{10}$", help_text="۱۰ رقم بدون خط تیره.", max_length=10,
    ),
    FormField("father_name", "نام پدر", required=True, max_length=128),
    FormField("birth_date", "تاریخ تولد (شمسی)", type="date"),
    FormField(
        "gender", "جنسیت", type="select",
        choices=(("male", "مرد"), ("female", "زن"), ("unspecified", "مشخص نشده")),
    ),
)

_CONTACT = (
    FormField("mobile", "موبایل", type="tel", required=True,
              pattern=r"^0\d{10}$", max_length=11),
    FormField("phone", "تلفن ثابت", type="tel"),
    FormField("email", "پست الکترونیک", type="text"),
    FormField("address", "نشانی", type="textarea"),
    FormField("postal_code", "کد پستی", max_length=20),
)

_STUDENT = (
    FormField("student_code", "کد دانش‌آموزی", required=True, max_length=32,
              help_text="یکتا در میان دانش‌آموزان زنده."),
    FormField("grade_level", "پایه تحصیلی", max_length=32),
    FormField("class_section", "شعبه"),
    FormField("school_year", "سال تحصیلی", help_text="مثال ۱۴۰۵-۱۴۰۶"),
    FormField("enrollment_date", "تاریخ ثبت‌نام (شمسی)", type="date"),
    FormField("birth_certificate_no", "شماره شناسنامه"),
    FormField("health_notes", "notes بهداشتی/پزشکی", type="textarea",
              help_text="محرمانه — فقط حافظان کامل می‌بینند."),
    FormField("has_special_needs", "نیاز ویژه دارد", type="checkbox"),
)

#: پدر و مادر (و قیم) به‌صورت Repeater: هر ردیف یک ولی + نسبت + تکفل.
_GUARDIAN_ROW = (
    FormField("relation", "نسبت", type="select", required=True,
              choices=tuple(GuardianProfile.Relation.choices)),
    FormField("first_name", "نام ولی", required=True),
    FormField("last_name", "نام خانوادگی ولی", required=True),
    FormField("national_code", "کد ملی ولی", pattern=r"^\d{10}$",
              help_text="اختیاری؛ اگر دانش‌آموز قبلاً ولی‌اش ثبت شده، همین را بگذارید."),
    FormField("mobile", "موبایل ولی", type="tel", required=True),
    FormField("phone", "تلفن ثابت ولی", type="tel"),
    FormField("occupation", "شغل"),
    FormField("education_level", "مقطع تحصیلی ولی"),
    FormField("custody_status", "وضعیت تکفل", type="select",
              choices=tuple(StudentGuardian.Custody.choices),
              help_text="تحت تکفل / تکفل با والد دیگر / ولایت کامل / فقط ملاقات."),
    FormField("is_primary", "ولی اصلی این دانش‌آموز", type="checkbox"),
    FormField("can_submit_requests", "اجازه ثبت درخواست", type="checkbox"),
    FormField("can_receive_billing", "دریافت اعلان مالی", type="checkbox"),
)

#: کارمند/مدرس — قرارداد، تخصص، سوابق، مدارک.
_STAFF_CONTRACT = (
    FormField("employee_code", "کد پرسنلی", required=True, max_length=32),
    FormField("department", "دپارتمان/واحد", type="text",
              help_text="نام دپارتمان؛ اگر در فهرست واحدها باشد، به آن لینک می‌شود."),
    FormField("job_title", "عنوان شغلی"),
    FormField("hire_date", "تاریخ استخدام (شمسی)", type="date"),
    FormField("contract_no", "شماره قرارداد"),
    FormField("contract_type", "نوع قرارداد", type="select",
              choices=(("", "—"), ("رسمی", "رسمی"), ("پیمانی", "پیمانی"),
                       ("حق‌التدریس", "حق‌التدریس"), ("پروژه‌ای", "پروژه‌ای"))),
    FormField("contract_start", "شروع قرارداد", type="date"),
    FormField("contract_end", "پایان قرارداد", type="date"),
    FormField("hourly_rate", "حق‌التدریس ساعتی (تومان)", type="number", min=0),
    FormField("weekly_max_hours", "سقف ساعات هفتگی", type="number", min=0, max=80,
              help_text="ورودی موتور زمان‌بندی: از تخصیص بیش از سقف جلوگیری می‌کند."),
)

_STAFF_EXPERTISE = (
    FormField("specialization", "تخصص / حوزه تدریس", type="textarea"),
    FormField("academic_degree", "مدرک تحصیلی"),
    FormField("experience_years", "سابقه (سال)", type="number", min=0, max=70),
    FormField("bio", "سوابق و رزومه", type="textarea"),
    FormField("staff_kind", "نوع پرسنل", type="select",
              choices=tuple(StaffProfile.Kind.choices)),
)

_ACCOUNT = (
    FormField("auto_create_user", "ساخت حساب کاربری (نام‌کاربری/رمز = کد ملی)",
              type="checkbox"),
    FormField("username", "نام کاربری (اختیاری)",
              help_text="خالی = کد ملی."),
    FormField("grant_role", "نقش رهبری اضافی", type="select",
              choices=(("", "—"), ("supervisor", "سرپرست"), ("manager", "مدیر")),
              help_text="فقط اگر سطح دسترسی شما اجازه دهد."),
)


def _acct(required: bool) -> FormSection:
    """Account section without the leadership-role picker (grant is implicit).

    ``required=True`` makes auto_create_user mandatory for leadership targets:
    roles live on the User, so an account-less supervisor would silently be a
    plain employee (see PersonOnboardingService.create's matching guard).
    """
    return FormSection("account", "حساب کاربری", tuple(
        replace(f, required=True) if (required and f.name == "auto_create_user") else f
        for f in _ACCOUNT[:2]
    ))


#: target → sections shown in step 2.
FIELD_SPECS: dict[str, tuple[FormSection, ...]] = {
    "student": (
        FormSection("identity", "مشخصات فردی دانش‌آموز", _IDENT),
        FormSection("contact", "تماس و نشانی", _CONTACT),
        FormSection("student", "اطلاعات تحصیلی", _STUDENT),
        FormSection(
            "guardians", "اطلاعات ولیین (پدر / مادر / قیم)", _GUARDIAN_ROW,
            repeatable=True, min_items=1, max_items=4,
            description=(
                "کمترین یک ولی لازم است. اگر ولی با همین کد ملی از قبل وجود "
                "دارد، فقط کد ملی را بگذارید تا پیوند تکفل ساخته شود."
            ),
        ),
        FormSection("account", "حساب کاربری", _ACCOUNT),
    ),
    "teacher": (
        FormSection("identity", "مشخصات فردی مدرس", _IDENT),
        FormSection("contact", "تماس و نشانی", _CONTACT),
        FormSection("contract", "قرارداد و تخصیص کاری", _STAFF_CONTRACT),
        FormSection("expertise", "تخصص و سوابق", _STAFF_EXPERTISE),
        FormSection("credentials", "مدارک", (
            FormField("degrees", "مدارک/گواهینامه‌ها", type="textarea",
                      help_text="هر خط: عنوان مدرک — صادرکننده — تاریخ."),
        )),
        FormSection("account", "حساب کاربری", _ACCOUNT),
    ),
    "employee": (
        FormSection("identity", "مشخصات فردی کارمند", _IDENT),
        FormSection("contact", "تماس و نشانی", _CONTACT),
        FormSection("contract", "قرارداد و تخصیص کاری", _STAFF_CONTRACT),
        FormSection("expertise", "تخصص و سوابق", _STAFF_EXPERTISE),
        FormSection("account", "حساب کاربری", _ACCOUNT),
    ),
    # Leadership targets are employees + a granted role — same fields, and the
    # grant_role select is constrained by hierarchy.GRANT_RIGHTS downstream.
    "supervisor": (
        FormSection("identity", "مشخصات فردی سرپرست", _IDENT),
        FormSection("contact", "تماس و نشانی", _CONTACT),
        FormSection("contract", "قرارداد و تخصیص کاری", _STAFF_CONTRACT),
        FormSection("expertise", "تخصص و سوابق", _STAFF_EXPERTISE),
        _acct(required=True),
    ),
    "manager": (
        FormSection("identity", "مشخصات فردی مدیر", _IDENT),
        FormSection("contact", "تماس و نشانی", _CONTACT),
        FormSection("contract", "قرارداد و تخصیص کاری", _STAFF_CONTRACT),
        FormSection("expertise", "تخصص و سوابق", _STAFF_EXPERTISE),
        _acct(required=True),
    ),
    # A standalone guardian must point at an existing ward.
    "guardian": (
        FormSection("identity", "مشخصات فردی ولی", _IDENT),
        FormSection("contact", "تماس و نشانی", _CONTACT),
        FormSection("guardianship", "دانش‌آموز تحت تکفل", (
            FormField("guards_student", "کد ملی یا کد دانش‌آموزی دانش‌آموز",
                      required=True,
                      help_text="ولی جدید به یک دانش‌آموز موجود متصل می‌شود."),
            FormField("relation", "نسبت", type="select", required=True,
                      choices=tuple(GuardianProfile.Relation.choices)),
            FormField("custody_status", "وضعیت تکفل", type="select",
                      choices=tuple(StudentGuardian.Custody.choices)),
            FormField("is_primary", "ولی اصلی این دانش‌آموز", type="checkbox"),
        )),
        FormSection("account", "حساب کاربری", _ACCOUNT),
    ),
}


def validate_target_fields(target: str, payload: dict[str, Any]) -> dict[str, str]:
    """
    Server-side mirror of the step-2 spec: returns {field: message} for every
    required field the payload leaves empty. The serializer turns that into
    DRF errors, so a client that skips step 2 gets 400 instead of a Person row
    with an empty student_code.
    """
    sections = FIELD_SPECS.get(target) or ()
    errors: dict[str, str] = {}
    for s in sections:
        if s.repeatable:
            items = payload.get(s.key) or []
            if not isinstance(items, list):
                errors[s.key] = "قالب این بخش باید فهرست باشد."
                continue
            if len(items) < s.min_items:
                errors[s.key] = (
                    f"کمترین {s.min_items} ردیف برای «{s.label}» لازم است."
                )
            for idx, row in enumerate(items):
                row = row if isinstance(row, dict) else {}
                for f in s.fields:
                    if f.required and not str(row.get(f.name) or "").strip():
                        errors[f"{s.key}[{idx}].{f.name}"] = (
                            f"«{f.label}» در ردیف {idx + 1} الزامی است."
                        )
            continue
        for f in s.fields:
            if not f.required:
                continue
            if target == "student" and f.name == "father_name":
                # father_name is required on the identity section for staff, but
                # for a student the guardian block carries the parents — and a
                # one-parent household must still be creatable.
                continue
            if not str(payload.get(f.name) or "").strip():
                errors[f.name] = f"«{f.label}» الزامی است."
    return errors


def schema_for(target: str, *, actor_roles: set[str], is_superuser: bool = False) -> Optional[dict[str, Any]]:
    """
    JSON contract for step 2 of the wizard. ``None`` when the actor may not
    create ``target`` — the endpoint then answers 403 rather than leaking the
    form's shape.
    """
    if not hierarchy.can_create(actor_roles, target, is_superuser=is_superuser):
        return None
    sections = FIELD_SPECS.get(target) or ()
    # Constrain the "grant leadership role" select to what THIS actor may grant,
    # so the UI cannot present an option the service will refuse.
    grantable = sorted(
        r for r in hierarchy.GRANTABLE_ROLES
        if hierarchy.can_grant_role(actor_roles, r, is_superuser=is_superuser)
    )
    rendered: list[dict[str, Any]] = []
    for section in sections:
        d = section.to_json()
        for fd in d["fields"]:
            if fd["name"] == "grant_role":
                fd["choices"] = [("", "—")] + [
                    (r, {"supervisor": "سرپرست", "manager": "مدیر"}.get(r, r))
                    for r in grantable
                ]
        rendered.append(d)
    return {"target": target, "sections": rendered, "grantable_roles": grantable}


# ─────────────────────────────────────────────────────────────────────────────
# 2) The service
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class GuardianInput:
    """One row of the student-wizard repeater."""

    relation: str = GuardianProfile.Relation.OTHER
    first_name: str = ""
    last_name: str = ""
    national_code: str = ""
    mobile: str = ""
    phone: str = ""
    occupation: str = ""
    education_level: str = ""
    custody_status: str = StudentGuardian.Custody.UNDER_CUSTODY
    is_primary: bool = False
    can_submit_requests: bool = True
    can_receive_billing: bool = False

    @classmethod
    def from_payload(cls, raw: Any) -> "GuardianInput":
        raw = raw if isinstance(raw, dict) else {}
        known = {f.name for f in _GUARDIAN_ROW}
        kwargs = {k: v for k, v in raw.items() if k in known}
        # Accept the Persian-friendly aliases the seeded form schemas use.
        if "father" in raw and not kwargs.get("first_name"):
            kwargs.update(relation=GuardianProfile.Relation.FATHER,
                          first_name=raw["father"] or "")
        if "mother" in raw and not kwargs.get("first_name"):
            kwargs.update(relation=GuardianProfile.Relation.MOTHER,
                          first_name=raw["mother"] or "")
        return cls(**kwargs)


class PersonOnboardingService:
    """
    Atomic, hierarchy-guarded creation of a person + their role-specific
    profile rows + their user account.

    Every public method is a single ``transaction.atomic`` block: the guard,
    the Person insert, the profile insert, the guardian links and the account
    provisioning either all commit or none do. ``select_for_update`` on the
    national_code path is not needed because the live-only unique constraint
    (B5) plus ``PersonService``'s IntegrityError mapping already serialise the
    race into a clean 400.
    """

    def __init__(self, *, person_service: Optional[PersonService] = None):
        self.person_service = person_service or PersonService()

    # ── guard (exposed for views/serializers that want the 403 early) ──

    def assert_can_create(self, actor, target: str) -> None:
        roles = set(actor.role_codes()) if hasattr(actor, "role_codes") else set()
        if not hierarchy.can_create(roles, target,
                                    is_superuser=bool(getattr(actor, "is_superuser", False))):
            raise OnboardingPermissionError(
                "شما مجاز به ایجاد کاربر با این نوع/نقش نیستید."
            )

    def assert_can_grant(self, actor, grant_role: str) -> None:
        if not grant_role:
            return
        roles = set(actor.role_codes()) if hasattr(actor, "role_codes") else set()
        if not hierarchy.can_grant_role(roles, grant_role,
                                        is_superuser=bool(getattr(actor, "is_superuser", False))):
            raise OnboardingPermissionError(
                f"شما مجاز به اعطای نقش «{grant_role}» نیستید."
            )

    # ── main entry point ─────────────────────────────────────────────────

    @transaction.atomic
    def create(self, *, actor, target: str, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Create one person of ``target`` kind from the wizard payload.

        Returns ``{"person", "user", "guardians", "profile"}`` — enough for the
        success step of the wizard to show what was provisioned.
        """
        target = (target or "").strip().lower()
        if target not in FIELD_SPECS:
            raise OnboardingValidationError(f"نوع نامعتبر: {target}")

        # 1) permission guard — BEFORE any write.
        self.assert_can_create(actor, target)

        # 2) dynamic field guard — mirrors the step-2 spec.
        errors = validate_target_fields(target, payload)
        if errors:
            raise OnboardingValidationError(errors)

        grant_role = str(payload.get("grant_role") or "").strip().lower()
        self.assert_can_grant(actor, grant_role)

        # Leadership roles live on the USER (accounts.UserRole). A supervisor
        # created WITHOUT an account would silently be a plain employee — the
        # matrix would be decorative. Refuse instead of half-doing it.
        if target in hierarchy.GRANTABLE_ROLES and not payload.get("auto_create_user"):
            raise OnboardingValidationError({
                "auto_create_user":
                    "برای نقش سرپرست/مدیر، ساخت حساب کاربری الزامی است "
                    "(نقش روی حساب می‌نشیند، نه روی شخص)."
            })

        # 3) the person itself.
        person_type = self._person_type_for(target)
        person = self.person_service.create_person(
            national_code=payload["national_code"],
            first_name=payload["first_name"],
            last_name=payload["last_name"],
            person_type=person_type,
            mobile=payload.get("mobile") or "",
            father_name=payload.get("father_name") or "",
            birth_date=self._as_date(payload.get("birth_date")),
            gender=payload.get("gender") or Person.Gender.NOT_SPECIFIED,
            email=payload.get("email") or "",
            phone=payload.get("phone") or "",
            address=payload.get("address") or "",
            postal_code=payload.get("postal_code") or "",
            student_code=payload.get("student_code") or None,
            employee_code=payload.get("employee_code") or None,
            department=payload.get("department") or "",
            job_title=payload.get("job_title") or "",
            hire_date=self._as_date(payload.get("hire_date")),
            photo=payload.get("photo") or None,
            registered_by=actor,
            auto_create_user=bool(payload.get("auto_create_user")),
            grant_role=grant_role or self._implied_role(target),
        )

        # 4) role-specific profile rows.
        profile = self._create_profile(target, person, payload)

        # 5) guardians (student wizard) / ward link (standalone guardian).
        guardians: list[Person] = []
        if target == "student":
            guardians = self._attach_guardians(
                student=person, rows=payload.get("guardians") or [], actor=actor,
            )
        elif target == "guardian":
            self._link_existing_ward(
                guardian=person, query=payload.get("guards_student") or "",
                relation=payload.get("relation") or GuardianProfile.Relation.OTHER,
                custody_status=payload.get("custody_status")
                or StudentGuardian.Custody.UNDER_CUSTODY,
                is_primary=bool(payload.get("is_primary")),
            )

        logger.info(
            "onboarding: %s created person %s (+%d guardians) by %s",
            target, person.pk, len(guardians), getattr(actor, "username", actor),
        )
        return {
            "person": person,
            "user": person.user if person.user_id else None,
            "guardians": guardians,
            "profile": profile,
        }

    # ── helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _person_type_for(target: str) -> str:
        """Leadership roles are people too: they are employees with a role."""
        return {
            "student": Person.Type.STUDENT,
            "teacher": Person.Type.TEACHER,
            "employee": Person.Type.EMPLOYEE,
            "supervisor": Person.Type.EMPLOYEE,
            "manager": Person.Type.EMPLOYEE,
            "guardian": Person.Type.GUARDIAN,
        }[target]

    @staticmethod
    def _implied_role(target: str) -> Optional[str]:
        """
        Role to grant when the actor did not ask for one explicitly.

        ``supervisor``/``manager`` are leadership *roles* riding on an employee
        person; without this the wizard would create a plain employee and the
        hierarchy matrix would be decorative.
        """
        if target in hierarchy.GRANTABLE_ROLES:
            return target
        return None

    @staticmethod
    def _as_date(value: Any):
        """
        Accept the formats the wizard actually sends: Jalali '1405-05-10' /
        '1405/05/10' (Persian or Latin digits), ISO Gregorian, or a date.
        Jalali is decided by a 13xx/14xx year — the Iranian range that can
        never be a plausible Gregorian birth/enrollment year here.
        """
        if not value:
            return None
        if not isinstance(value, str) and hasattr(value, "year"):
            return value
        import datetime

        from apps.core.utils import english_numbers

        text = english_numbers(str(value)).strip().replace("/", "-")
        year_part = text.split("-")[0] if text else ""
        if year_part[:2] in ("13", "14") and len(year_part) == 4:
            try:
                import jdatetime

                y, m, d = (int(x) for x in text.split("-", 2))
                return jdatetime.date(y, m, d).togregorian()
            except (ValueError, IndexError):
                raise OnboardingValidationError(
                    {"date": f"قالب تاریخ شمسی نامعتبر است: {value}"}
                )
        try:
            return datetime.date.fromisoformat(text)
        except ValueError:
            raise OnboardingValidationError(
                {"date": f"قالب تاریخ نامعتبر است: {value}"}
            )

    def _create_profile(self, target: str, person: Person, payload: dict[str, Any]):
        if target == "student":
            return StudentProfile.objects.create(
                person=person,
                grade_level=payload.get("grade_level") or "",
                class_section=payload.get("class_section") or "",
                school_year=payload.get("school_year") or "",
                enrollment_date=self._as_date(payload.get("enrollment_date")),
                birth_certificate_no=payload.get("birth_certificate_no") or "",
                health_notes=payload.get("health_notes") or "",
                has_special_needs=bool(payload.get("has_special_needs")),
            )
        if target == "guardian":
            return GuardianProfile.objects.create(
                person=person,
                occupation=payload.get("occupation") or "",
                education_level=payload.get("education_level") or "",
            )
        if target in ("teacher", "employee", "supervisor", "manager"):
            department = self._resolve_department(payload.get("department") or "")
            return StaffProfile.objects.create(
                person=person,
                kind=(payload.get("staff_kind")
                      or (StaffProfile.Kind.TEACHING if target == "teacher"
                          else StaffProfile.Kind.ADMINISTRATIVE)),
                contract_no=payload.get("contract_no") or "",
                contract_type=payload.get("contract_type") or "",
                contract_start=self._as_date(payload.get("contract_start")),
                contract_end=self._as_date(payload.get("contract_end")),
                hourly_rate=int(payload.get("hourly_rate") or 0),
                weekly_max_hours=int(payload.get("weekly_max_hours") or 0),
                specialization=payload.get("specialization") or "",
                department=department,
                academic_degree=payload.get("academic_degree") or "",
                experience_years=int(payload.get("experience_years") or 0),
                bio=payload.get("bio") or "",
            )
        return None

    @staticmethod
    def _resolve_department(name: str):
        """Link a free-text department to education.Department when it matches."""
        if not name:
            return None
        from apps.education.models import Department

        return (
            Department.objects.filter(name__iexact=name.strip(), is_deleted=False).first()
        )

    def _attach_guardians(self, *, student: Person, rows: list[Any], actor) -> list[Person]:
        """
        Create-or-link the guardians collected in the wizard repeater.

        Match on national_code first (a returning parent must not become a
        duplicate Person), then on full name + mobile. The custody row is
        always (re)written so the intake's تکفل answer is never lost.
        """
        created: list[Person] = []
        if sum(bool(item.get("is_primary")) for item in rows if isinstance(item, dict)) > 1:
            raise OnboardingValidationError(
                {"guardians": "برای هر دانش‌آموز فقط یک ولی اصلی انتخاب کنید."}
            )
        for raw in rows:
            gi = GuardianInput.from_payload(raw)
            if not (gi.first_name or gi.mobile):
                continue
            guardian = self._find_or_create_guardian(gi, actor=actor, student=student)
            if gi.is_primary:
                StudentGuardian.objects.filter(
                    student=student, is_primary=True, is_deleted=False,
                ).exclude(guardian=guardian).update(is_primary=False)
            link, _c = StudentGuardian.objects.update_or_create(
                student=student, guardian=guardian, is_deleted=False,
                defaults={
                    "relation": gi.relation or GuardianProfile.Relation.OTHER,
                    "custody_status": gi.custody_status
                    or StudentGuardian.Custody.UNDER_CUSTODY,
                    "phone_override": gi.mobile if gi.mobile != guardian.mobile else "",
                    "can_submit_requests": gi.can_submit_requests,
                    "can_receive_billing": gi.can_receive_billing,
                    "is_primary": gi.is_primary,
                    "is_active": True,
                },
            )
            profile, _ = GuardianProfile.objects.get_or_create(
                person=guardian,
                defaults={
                    "occupation": gi.occupation,
                    "education_level": gi.education_level,
                },
            )
            # student_profile is created earlier in the same transaction for
            # target=student; getattr only guards a hand-misused caller.
            profile_row = getattr(student, "student_profile", None)
            if profile_row is not None and (
                link.custody_status != StudentGuardian.Custody.UNDER_CUSTODY
                and not profile_row.is_custody_case
            ):
                profile_row.is_custody_case = True
                profile_row.save(update_fields=["is_custody_case", "updated_at"])
            created.append(guardian)
        return created

    def _find_or_create_guardian(self, gi: GuardianInput, *, actor,
                                 student: Optional[Person] = None) -> Person:
        """
        Resolve a guardian Person by national code → name+mobile → create.

        Reusing an existing row is the whole point: a mother who is also a
        teacher must not be duplicated (§13-1 keeps one Person per human), and
        two siblings in the same institute share ONE guardian row.
        """
        from apps.core.utils import english_numbers

        nc = english_numbers(gi.national_code or "").strip()
        if nc:
            found = Person.objects.filter(
                national_code=nc, is_deleted=False
            ).first()
            if found is not None:
                if student is not None and found.pk == student.pk:
                    # Same national code as the student being created — the
                    # DB check (guardian != student) would surface as a raw
                    # IntegrityError/500. Say 400 in the repeater's language.
                    raise OnboardingValidationError({
                        "guardians": "کد ملی ولی نمی‌تواند همان کد ملی دانش‌آموز باشد."
                    })
                if found.person_type != Person.Type.GUARDIAN and not found.has_type(
                    Person.Type.GUARDIAN
                ):
                    # e.g. a mother who is also a teacher — she keeps her row
                    # and simply gains the guardian type.
                    self.person_service.add_person_type(
                        person=found, type_code=Person.Type.GUARDIAN,
                        assigned_by=actor, provision_user_roles=True,
                    )
                return found
        mobile = english_numbers(gi.mobile or "").strip()
        if mobile:
            found = Person.objects.filter(
                mobile=mobile, first_name__iexact=gi.first_name.strip(),
                last_name__iexact=gi.last_name.strip(), is_deleted=False,
            ).first()
            if found is not None:
                if student is not None and found.pk == student.pk:
                    raise OnboardingValidationError({
                        "guardians": "ولی نمی‌تواند خودِ دانش‌آموز باشد."
                    })
                # Same rule as the national-code path — a name+mobile match can
                # hit a person of another type (a teacher whose phone is also
                # the parent's); she must carry the guardian type so ward
                # scoping (which filters by the link, not the type) stays honest.
                if found.person_type != Person.Type.GUARDIAN and not found.has_type(
                    Person.Type.GUARDIAN
                ):
                    self.person_service.add_person_type(
                        person=found, type_code=Person.Type.GUARDIAN,
                        assigned_by=actor, provision_user_roles=True,
                    )
                return found
        if not nc:
            raise OnboardingValidationError({
                "guardians": "برای ثبت ولی، کد ملی او الزامی است."
            })
        # Truly new guardian — create it through the same service (so the
        # soft-delete-aware unique handling applies), without an account: the
        # wizard's `auto_create_user` decision belongs to the student, and a
        # guardian can be given login later via /persons/{id}/create-user/.
        return self.person_service.create_person(
            national_code=nc,
            first_name=gi.first_name,
            last_name=gi.last_name,
            person_type=Person.Type.GUARDIAN,
            mobile=gi.mobile or "",
            phone=gi.phone or "",
            father_name="",
            auto_create_user=False,
            registered_by=actor,
        )

    def _link_existing_ward(self, *, guardian: Person, query: str, relation: str,
                           custody_status: str, is_primary: bool) -> StudentGuardian:
        from apps.core.utils import english_numbers

        q = english_numbers(query or "").strip()
        if not q:
            raise OnboardingValidationError(
                {"guards_student": "کد ملی یا کد دانش‌آموزی دانش‌آموز را وارد کنید."}
            )
        from django.db.models import Q

        student = Person.objects.filter(
            Q(national_code=q) | Q(student_code=q),
            person_type=Person.Type.STUDENT, is_deleted=False,
        ).first()
        if student is None:
            raise OnboardingValidationError(
                {"guards_student": "دانش‌آموزی با این شناسه یافت نشد."}
            )
        if is_primary:
            StudentGuardian.objects.filter(
                student=student, is_primary=True, is_deleted=False,
            ).exclude(guardian=guardian).update(is_primary=False)
        link, _ = StudentGuardian.objects.update_or_create(
            student=student, guardian=guardian, is_deleted=False,
            defaults={"relation": relation, "custody_status": custody_status,
                      "is_primary": is_primary, "is_active": True},
        )
        return link
