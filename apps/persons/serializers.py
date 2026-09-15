from __future__ import annotations

from rest_framework import serializers

from apps.core.fields import JalaliDateField, PersianCharField
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


class PersonListSerializer(PersonPIIMaskingMixin, serializers.ModelSerializer):
    """سریالایزر خلاصه برای لیست اشخاص (PII ماسک‌شده برای غیرمتولیان)."""

    person_type_display = serializers.CharField(
        source="get_person_type_display", read_only=True
    )
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
            "birth_date",
            "mobile",
            "email",
            "is_active",
            "has_user",
            "created_at",
        )


class PersonDetailSerializer(PersonPIIMaskingMixin, serializers.ModelSerializer):
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
            "updated_at",
        )
        read_only_fields = (
            "created_at",
            "updated_at",
            "display_name",
            "display_national_code",
            "display_mobile",
        )


class PersonCreateSerializer(serializers.ModelSerializer):
    """سریالایزر ایجاد شخص جدید."""

    auto_create_user = serializers.BooleanField(
        default=False,
        help_text="آیا برای این شخص کاربر ساخته شود؟ (پیش‌فرض: خیر)",
    )
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
            "grant_role",
        )

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
