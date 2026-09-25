from __future__ import annotations

from rest_framework import serializers

from apps.core.fields import JalaliDateField, PersianCharField
from apps.core.serializers import CRUDActionsMixin
from apps.persons.models import Person
from apps.persons.services import (
    can_view_full_person_detail,
    mask_address,
    mask_email,
    mask_identifier,
)

#: Fields whose raw values are protected identity/contact data (B1).
#: These are masked in the SERIALIZED OUTPUT only — input validation on
#: write paths is untouched, so custodians can still edit real values.
#: student_code / employee_code are also institution-unique identifiers and
#: are masked for the same reason.
PII_FIELDS = (
    "national_code", "mobile", "email", "phone", "address", "postal_code",
    "student_code", "employee_code",
)


def _request_user(serializer) -> object | None:
    request = serializer.context.get("request") if serializer.context else None
    return getattr(request, "user", None)


class PersonPIIMaskingMixin:
    """
    Mixin: when the requesting user is not a full custodian of the person,
    replace protected identity/contact fields with masked forms.
    """

    #: Only the DETAIL serializer audits masked reads (a list would otherwise
    #: write one event per row — §13-4 keeps the trail meaningful, not noisy).
    audit_masked_read = False

    def to_representation(self, instance):
        data = super().to_representation(instance)
        user = _request_user(self)
        if can_view_full_person_detail(user, instance):
            return data
        # §13-4: a masked read means someone just saw that a person EXISTS
        # while being denied their raw identifiers — that denial is a
        # queryable security event (best-effort, never raises).
        if self.audit_masked_read:
            from apps.core.models import AuditEvent

            request = self.context.get("request") if self.context else None
            AuditEvent.record(
                kind=AuditEvent.Kind.SENSITIVE_READ,
                summary=f"خواندن ماسک‌شده‌ی PII شخص {instance.pk}",
                actor=user if getattr(user, "is_authenticated", False) else None,
                obj=instance,
                request=request,
                metadata={"masked_fields": list(PII_FIELDS)},
            )
        for field in PII_FIELDS:
            if field not in data:
                continue
            value = data.get(field)
            if value in (None, ""):
                continue
            if field in {"address"}:
                data[field] = mask_address(value)
            elif field == "email":
                data[field] = mask_email(value)
            elif field == "postal_code":
                data[field] = mask_identifier(value)
            else:
                data[field] = mask_identifier(value)
        # The Persian display mirrors must not leak the unmasked value either.
        if "display_national_code" in data and data.get("display_national_code"):
            data["display_national_code"] = mask_identifier(str(instance.national_code))
        if "display_mobile" in data and data.get("display_mobile"):
            data["display_mobile"] = mask_identifier(str(instance.mobile))
        # username defaults to the national code in provisioning — leaking it
        # would re-leak the identifier through a side door (B1/B2 pairing).
        if data.get("username"):
            data["username"] = mask_identifier(str(data["username"]))
        return data


class PersonListSerializer(CRUDActionsMixin, PersonPIIMaskingMixin, serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    """سریالایزر خلاصه برای لیست اشخاص (PII ماسک‌شده برای غیرمتولیان)."""

    person_type_display = serializers.CharField(
        source="get_person_type_display", read_only=True
    )
    role_display = serializers.SerializerMethodField()
    has_user = serializers.BooleanField(source="user_id", read_only=True)
    birth_date = JalaliDateField(allow_null=True, required=False)
    created_at = PersianCharField(source="created_at_jalali", read_only=True)

    class Meta:
        model = Person
        fields = (
            "id",
            "national_code",
            "first_name",
            "last_name",
            "person_type",
            "person_type_display",
            "role_display",
            "birth_date",
            "mobile",
            "email",
            "is_active",
            "has_user",
            "created_at", "actions",
        )

    def get_role_display(self, obj) -> str:
        leadership_labels = {
            "manager": "مدیریت",
            "supervisor": "کارمند سرپرست",
        }
        links = getattr(getattr(obj, "user", None), "active_role_links", ())
        for link in links:
            label = leadership_labels.get(link.role.code)
            if label:
                return label
        return obj.get_person_type_display()


class PersonDetailSerializer(CRUDActionsMixin, PersonPIIMaskingMixin, serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    """سریالایزر کامل برای جزئیات شخص (PII ماسک‌شده برای غیرمتولیان)."""

    audit_masked_read = True

    person_type_display = serializers.CharField(
        source="get_person_type_display", read_only=True
    )
    person_types_display = serializers.CharField(read_only=True)
    gender_display = serializers.CharField(
        source="get_gender_display", read_only=True
    )
    has_user = serializers.BooleanField(source="user_id", read_only=True)
    username = serializers.CharField(
        source="user.username", read_only=True, allow_null=True
    )
    birth_date = JalaliDateField(allow_null=True, required=False)
    hire_date = JalaliDateField(allow_null=True, required=False)
    created_at = PersianCharField(source="created_at_jalali", read_only=True)
    updated_at = PersianCharField(source="updated_at_jalali", read_only=True)
    display_name = serializers.CharField(read_only=True)
    display_national_code = serializers.CharField(read_only=True)
    display_mobile = serializers.CharField(read_only=True)
    student_profile_summary = serializers.SerializerMethodField()
    staff_profile_summary = serializers.SerializerMethodField()
    guardian_profile_summary = serializers.SerializerMethodField()

    class Meta:
        model = Person
        fields = (
            "id",
            "national_code",
            "first_name",
            "last_name",
            "display_name",
            "display_national_code",
            "display_mobile",
            "father_name",
            "birth_date",
            "gender",
            "gender_display",
            "mobile",
            "email",
            "phone",
            "address",
            "postal_code",
            "person_type",
            "person_type_display",
            "person_types_display",
            "student_code",
            "employee_code",
            "department",
            "job_title",
            "hire_date",
            "photo",
            "is_active",
            "has_user",
            "username",
            "created_at",
            "updated_at", "actions",
            "student_profile_summary", "staff_profile_summary", "guardian_profile_summary",
        )
        read_only_fields = (
            "created_at",
            "updated_at",
            "display_name",
            "display_national_code",
            "display_mobile",
            "national_code",
            "person_type",
            "actions",
        )

    def get_student_profile_summary(self, obj):
        profile = getattr(obj, "student_profile", None)
        if not profile:
            return None
        return {
            "grade_level": profile.grade_level,
            "class_section": profile.class_section,
            "school_year": profile.school_year,
            "parents": {
                "father": f"{profile.father_first_name} {profile.father_last_name}".strip(),
                "mother": f"{profile.mother_first_name} {profile.mother_last_name}".strip(),
            },
            "has_special_needs": profile.has_special_needs,
            "is_custody_case": profile.is_custody_case,
        }

    def get_staff_profile_summary(self, obj):
        profile = getattr(obj, "staff_profile", None)
        if not profile:
            return None
        return {
            "kind": profile.get_kind_display(),
            "specialization": profile.specialization,
            "academic_degree": profile.academic_degree,
            "experience_years": profile.experience_years,
            "is_verified": profile.is_verified,
        }

    def get_guardian_profile_summary(self, obj):
        profile = getattr(obj, "guardian_profile", None)
        if not profile:
            return None
        return {
            "occupation": profile.occupation,
            "education_level": profile.education_level,
            "preferred_contact": profile.preferred_contact,
        }


class PersonCreateSerializer(serializers.ModelSerializer):
    """سریالایزر ایجاد شخص جدید."""

    auto_create_user = serializers.BooleanField(
        default=True,
        write_only=True,
        help_text="برای سازگاری API نگه داشته شده؛ حساب کاربری به‌صورت پیش‌فرض ساخته می‌شود.",
    )
    password = serializers.CharField(
        required=False, allow_blank=True, write_only=True,
        min_length=8,
        help_text="برای کارمند/مدیریت الزامی؛ برای دانش‌آموز/استاد خالی = کد ملی.",
    )
    mobile = serializers.CharField(max_length=11)
    email = serializers.EmailField(required=False, allow_blank=True)
    grant_role = serializers.CharField(
        required=False, allow_blank=True, max_length=64, write_only=True,
        help_text="نقش اضافه پس از ساخت کاربر (مثلاً supervisor یا manager) — فقط مدیر/مدیرسیستم.",
    )
    birth_date = JalaliDateField(allow_null=True, required=False)
    hire_date = JalaliDateField(allow_null=True, required=False)

    class Meta:
        model = Person
        fields = (
            "national_code",
            "first_name",
            "last_name",
            "father_name",
            "birth_date",
            "gender",
            "mobile",
            "email",
            "phone",
            "address",
            "postal_code",
            "person_type",
            "student_code",
            "employee_code",
            "department",
            "job_title",
            "hire_date",
            "photo",
            "auto_create_user",
            "password",
            "grant_role",
        )

    def validate_mobile(self, value: str) -> str:
        from apps.core.utils import english_numbers

        normalized = english_numbers(value).strip()
        if len(normalized) != 11 or not normalized.isdigit() or not normalized.startswith("09"):
            raise serializers.ValidationError("شماره موبایل باید دقیقاً ۱۱ رقم و با ۰۹ شروع شود.")
        return normalized

    def validate_national_code(self, value: str) -> str:
        from apps.core.utils import english_numbers

        normalized = english_numbers(value).strip()
        if not normalized or not normalized.isdigit():
            raise serializers.ValidationError("کد ملی باید فقط شامل ارقام باشد (انگلیسی یا فارسی).")
        if len(normalized) != 10:
            raise serializers.ValidationError("کد ملی باید ۱۰ رقمی باشد.")
        return normalized

    def validate(self, attrs):
        person_type = attrs.get("person_type")
        if person_type == Person.Type.STUDENT and not attrs.get("student_code"):
            raise serializers.ValidationError(
                {"student_code": "برای دانش‌آموز کد دانش‌آموزی الزامی است."}
            )
        if person_type in (Person.Type.EMPLOYEE, Person.Type.TEACHER):
            if not attrs.get("employee_code"):
                raise serializers.ValidationError(
                    {"employee_code": "برای کارمند/معلم کد پرسنلی الزامی است."}
                )
        if person_type == Person.Type.EMPLOYEE and not attrs.get("password"):
            raise serializers.ValidationError(
                {"password": "برای کارمند، کلمه عبور اختصاصی الزامی است."}
            )
        # Creation hierarchy: the actor may only create the person types their
        # role tier permits (مدیرسیستم > مدیریت > سرپرست > کارمند عادی).
        request = self.context.get("request")
        actor = getattr(request, "user", None)
        if actor is not None and getattr(actor, "is_authenticated", False) and person_type:
            from apps.persons import hierarchy

            roles = set(actor.role_codes()) if hasattr(actor, "role_codes") else set()
            if not hierarchy.can_create(roles, person_type, is_superuser=actor.is_superuser):
                raise serializers.ValidationError(
                    {"person_type": "شما مجاز به ثبت این نوع شخص نیستید."}
                )
            grant_role = (attrs.get("grant_role") or "").strip().lower()
            if grant_role and not hierarchy.can_grant_role(
                roles, grant_role, is_superuser=actor.is_superuser
            ):
                raise serializers.ValidationError(
                    {"grant_role": "شما مجاز به اعطای این نقش نیستید."}
                )
        return attrs


class CreateUserForPersonSerializer(serializers.Serializer):
    """سریالایزر ساخت User برای شخص موجود."""

    username = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="نام کاربری (اختیاری — پیش‌فرض کد ملی)",
    )
    password = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
        help_text="رمز عبور (اختیاری — پیش‌فرض کد ملی)",
    )
