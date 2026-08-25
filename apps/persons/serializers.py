from __future__ import annotations

from rest_framework import serializers

from apps.core.fields import JalaliDateField, PersianCharField
from apps.persons.models import Person, StudentParent


class PersonListSerializer(serializers.ModelSerializer):
    """سریالایزر خلاصه برای لیست اشخاص."""

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


class PersonDetailSerializer(serializers.ModelSerializer):
    """سریالایزر کامل برای جزئیات شخص."""

    person_type_display = serializers.CharField(
        source="get_person_type_display", read_only=True
    )
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
        )

    def validate_national_code(self, value: str) -> str:
        if not value or not value.strip().isdigit():
            raise serializers.ValidationError("کد ملی باید فقط شامل ارقام باشد.")
        if len(value.strip()) != 10:
            raise serializers.ValidationError("کد ملی باید ۱۰ رقمی باشد.")
        return value.strip()

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


class StudentParentSerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(
        source="parent.__str__", read_only=True
    )
    student_name = serializers.CharField(
        source="student.__str__", read_only=True
    )
    created_at = PersianCharField(source="created_at_jalali", read_only=True)

    class Meta:
        model = StudentParent
        fields = (
            "id",
            "parent",
            "parent_name",
            "student",
            "student_name",
            "relation",
            "is_active",
            "created_at",
        )
        read_only_fields = ("created_at",)
