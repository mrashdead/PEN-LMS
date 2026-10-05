from __future__ import annotations

from django.db import transaction
from rest_framework import serializers

from apps.core.fields import JalaliDateField, PersianCharField
from apps.core.serializers import CRUDActionsMixin
from apps.core.utils import english_numbers
from apps.persons.models import Person, StaffProfile, StudentGuardian, StudentProfile
from apps.persons.services import (
    can_view_full_person_detail,
    mask_address,
    mask_email,
    mask_identifier,
    student_account_creation_missing_fields,
)
from apps.persons.validation import is_valid_iranian_mobile, national_code_error

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


class StudentProfileEditSerializer(serializers.ModelSerializer):
    """Editable fields collected by the student create form."""

    class Meta:
        model = StudentProfile
        fields = (
            "father_first_name", "father_last_name", "father_phone",
            "mother_first_name", "mother_last_name", "mother_phone",
            "is_custody_case", "custody_note",
        )

    @staticmethod
    def _validate_parent_phone(value):
        from apps.core.utils import english_numbers

        normalized = english_numbers(value or "").strip()
        if normalized and not is_valid_iranian_mobile(normalized):
            raise serializers.ValidationError("شماره موبایل باید دقیقاً ۱۱ رقم و با ۰۹ شروع شود.")
        return normalized

    def validate_father_phone(self, value):
        return self._validate_parent_phone(value)

    def validate_mother_phone(self, value):
        return self._validate_parent_phone(value)


class StaffProfileEditSerializer(serializers.ModelSerializer):
    """Editable role-specific fields collected by the staff create form."""

    class Meta:
        model = StaffProfile
        fields = ("specialization",)


class PersonListSerializer(CRUDActionsMixin, PersonPIIMaskingMixin, serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    """سریالایزر خلاصه برای لیست اشخاص (PII ماسک‌شده برای غیرمتولیان)."""

    person_type_display = serializers.CharField(
        source="get_person_type_display", read_only=True
    )
    role_display = serializers.SerializerMethodField()
    has_user = serializers.BooleanField(source="user_id", read_only=True)
    user_is_active = serializers.BooleanField(
        source="user.is_active", read_only=True, allow_null=True
    )
    user_id = serializers.UUIDField(read_only=True, allow_null=True)
    department = serializers.SerializerMethodField()
    job_title = serializers.SerializerMethodField()
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
            "user_is_active",
            "user_id", "department", "job_title",
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

    def get_department(self, obj) -> str:
        return str(getattr(getattr(obj, "user", None), "department", "") or "")

    def get_job_title(self, obj) -> str:
        return str(getattr(getattr(obj, "user", None), "job_title", "") or "")


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
    user_is_active = serializers.BooleanField(
        source="user.is_active", read_only=True, allow_null=True
    )
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
    account_creation_missing_fields = serializers.SerializerMethodField()
    student_profile = StudentProfileEditSerializer(required=False, allow_null=True)
    staff_profile = StaffProfileEditSerializer(required=False, allow_null=True)
    person_type_codes = serializers.SerializerMethodField()
    user_role_codes = serializers.SerializerMethodField()
    can_manage_supervisor_role = serializers.SerializerMethodField()
    employee_kind = serializers.ChoiceField(
        choices=(("ordinary", "عادی"), ("supervisor", "سرپرست")),
        required=False,
        write_only=True,
    )
    mobile = serializers.CharField(max_length=11, required=False)

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
            "user_is_active",
            "username",
            "created_at",
            "updated_at", "actions",
            "student_profile_summary", "staff_profile_summary", "guardian_profile_summary",
            "account_creation_missing_fields",
            "student_profile", "staff_profile", "person_type_codes", "user_role_codes",
            "can_manage_supervisor_role", "employee_kind",
        )
        read_only_fields = (
            "created_at",
            "updated_at",
            "display_name",
            "display_national_code",
            "display_mobile",
            "person_type",
            "actions",
            "person_type_codes",
            "user_role_codes",
            "can_manage_supervisor_role",
        )

    def get_person_type_codes(self, obj):
        return sorted(obj.type_codes())

    def get_user_role_codes(self, obj):
        return sorted(obj.user.role_codes()) if obj.user_id else []

    def get_can_manage_supervisor_role(self, obj):
        from apps.persons import hierarchy

        actor = _request_user(self)
        actor_roles = set(actor.role_codes()) if actor and hasattr(actor, "role_codes") else set()
        return hierarchy.can_grant_role(
            actor_roles, "supervisor", is_superuser=bool(getattr(actor, "is_superuser", False))
        )

    def validate_mobile(self, value: str) -> str:
        from apps.core.utils import english_numbers

        normalized = english_numbers(value).strip()
        if len(normalized) != 11 or not normalized.isdigit() or not normalized.startswith("09"):
            raise serializers.ValidationError("شماره موبایل باید دقیقاً ۱۱ رقم و با ۰۹ شروع شود.")
        return normalized

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
            "custody_note": profile.custody_note,
        }

    def get_account_creation_missing_fields(self, obj):
        if not obj.has_type(Person.Type.STUDENT):
            return []
        return student_account_creation_missing_fields(obj)

    def validate_national_code(self, value):
        normalized = english_numbers(value).strip()
        error = national_code_error(normalized, require_location=True)
        if error:
            raise serializers.ValidationError(error)
        if self.instance and normalized != self.instance.national_code:
            if self.instance.user_id or not national_code_error(
                self.instance.national_code, require_location=True
            ):
                raise serializers.ValidationError("کد ملی فقط برای اصلاح مقدار نامعتبرِ فردِ بدون حساب قابل تغییر است.")
        duplicates = Person.objects.filter(national_code=normalized, is_deleted=False)
        if self.instance:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError("این کد ملی برای فرد دیگری ثبت شده است.")
        return normalized

    @transaction.atomic
    def update(self, instance, validated_data):
        student_data = validated_data.pop("student_profile", None)
        staff_data = validated_data.pop("staff_profile", None)
        employee_kind = validated_data.pop("employee_kind", None)

        instance = super().update(instance, validated_data)

        if student_data is not None:
            if not instance.has_type(Person.Type.STUDENT):
                raise serializers.ValidationError({
                    "student_profile": "این بخش فقط برای دانش‌آموز قابل ویرایش است."
                })
            profile, _ = StudentProfile.objects.get_or_create(person=instance)
            for field, value in student_data.items():
                setattr(profile, field, value)
            profile.save(update_fields=[*student_data.keys(), "updated_at"])
            self._sync_parent_contacts(instance, profile, student_data)

        if staff_data is not None:
            if not (instance.has_type(Person.Type.TEACHER) or instance.has_type(Person.Type.EMPLOYEE)):
                raise serializers.ValidationError({
                    "staff_profile": "این بخش فقط برای مدرس یا کارمند قابل ویرایش است."
                })
            profile, _ = StaffProfile.objects.get_or_create(
                person=instance,
                defaults={
                    "kind": (StaffProfile.Kind.TEACHING
                             if instance.person_type == Person.Type.TEACHER
                             else StaffProfile.Kind.ADMINISTRATIVE),
                },
            )
            for field, value in staff_data.items():
                setattr(profile, field, value)
            profile.save(update_fields=[*staff_data.keys(), "updated_at"])

        if employee_kind is not None:
            if not instance.has_type(Person.Type.EMPLOYEE) or not instance.user_id:
                raise serializers.ValidationError({
                    "employee_kind": "نقش سرپرستی فقط برای کارمند دارای حساب کاربری قابل تغییر است."
                })
            from apps.persons import hierarchy

            actor = _request_user(self)
            actor_roles = set(actor.role_codes()) if actor and hasattr(actor, "role_codes") else set()
            if not hierarchy.can_grant_role(
                actor_roles, "supervisor", is_superuser=bool(getattr(actor, "is_superuser", False))
            ):
                raise serializers.ValidationError({
                    "employee_kind": "شما مجاز به تغییر نقش سرپرستی نیستید."
                })
            if employee_kind == "supervisor":
                instance.user.assign_role("supervisor", assigned_by=actor)
            else:
                instance.user.revoke_role("supervisor")
        return instance

    @staticmethod
    def _sync_parent_contacts(student, profile, changed_fields):
        """Keep linked father/mother records aligned with the student editor."""
        if not set(changed_fields).intersection({
            "father_first_name", "father_last_name", "father_phone",
            "mother_first_name", "mother_last_name", "mother_phone",
        }):
            return
        links = StudentGuardian.objects.filter(
            student=student,
            relation__in=("father", "mother"),
            is_deleted=False,
            is_active=True,
        ).select_related("guardian")
        for link in links:
            prefix = "father" if link.relation == "father" else "mother"
            guardian = link.guardian
            identity_fields = []
            for field in ("first_name", "last_name"):
                profile_field = f"{prefix}_{field}"
                if profile_field in changed_fields:
                    setattr(guardian, field, getattr(profile, profile_field))
                    identity_fields.append(field)
            if identity_fields:
                guardian.save(update_fields=[*identity_fields, "updated_at"])
            phone_field = f"{prefix}_phone"
            if phone_field in changed_fields:
                phone = getattr(profile, phone_field)
                link.phone_override = phone if phone and phone != guardian.mobile else ""
                link.save(update_fields=["phone_override", "updated_at"])
    def to_representation(self, instance):
        data = super().to_representation(instance)
        profile_data = data.get("student_profile")
        if instance.has_type(Person.Type.STUDENT):
            if profile_data is None:
                profile_data = {
                    "father_first_name": "", "father_last_name": "", "father_phone": "",
                    "mother_first_name": "", "mother_last_name": "", "mother_phone": "",
                    "is_custody_case": False, "custody_note": "",
                }
                data["student_profile"] = profile_data
            links = StudentGuardian.objects.filter(
                student=instance, is_deleted=False, is_active=True,
                relation__in=("father", "mother"),
            ).select_related("guardian")
            for link in links:
                prefix = "father" if link.relation == "father" else "mother"
                guardian = link.guardian
                for field, value in (
                    (f"{prefix}_first_name", guardian.first_name),
                    (f"{prefix}_last_name", guardian.last_name),
                    (f"{prefix}_phone", link.phone_override or guardian.mobile),
                ):
                    profile_data[field] = value
        if not can_view_full_person_detail(_request_user(self), instance):
            if profile_data:
                for field in ("father_phone", "mother_phone"):
                    if profile_data.get(field):
                        profile_data[field] = mask_identifier(profile_data[field])
        return data

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
        error = national_code_error(normalized, require_location=True)
        if error:
            raise serializers.ValidationError(error)
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
