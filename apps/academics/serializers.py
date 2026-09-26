from __future__ import annotations

from rest_framework import serializers

from apps.academics.models import AcademicTerm, ClassEnrollment, ClassGroup
from apps.core.fields import JalaliDateField, PersianCharField
from apps.core.serializers import CRUDActionsMixin


class AcademicTermListSerializer(CRUDActionsMixin, serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    """سریالایزر خلاصه برای لیست ترم‌ها."""

    start_date = JalaliDateField()
    end_date = JalaliDateField()
    display_title = serializers.CharField(read_only=True)

    class Meta:
        model = AcademicTerm
        fields = (
            "id",
            "title",
            "display_title",
            "start_date",
            "end_date",
            "is_current",
            "is_active",
            "created_at",
            "updated_at",
            "actions",
        )


class AcademicTermDetailSerializer(CRUDActionsMixin, serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    """سریالایزر کامل ترم تحصیلی."""

    start_date = JalaliDateField()
    end_date = JalaliDateField()
    start_date_jalali = serializers.CharField(read_only=True)
    end_date_jalali = serializers.CharField(read_only=True)
    display_title = serializers.CharField(read_only=True)
    created_at = PersianCharField(source="created_at_jalali", read_only=True)
    updated_at = PersianCharField(source="updated_at_jalali", read_only=True)

    class Meta:
        model = AcademicTerm
        fields = (
            "id",
            "title",
            "display_title",
            "start_date",
            "end_date",
            "start_date_jalali",
            "end_date_jalali",
            "is_current",
            "is_active",
            "note",
            "created_at",
            "updated_at",
            "actions",
        )
        read_only_fields = ("created_at", "updated_at")


class AcademicTermCreateSerializer(serializers.ModelSerializer):
    """سریالایزر ساخت ترم جدید."""

    start_date = JalaliDateField()
    end_date = JalaliDateField()

    class Meta:
        model = AcademicTerm
        fields = (
            "title",
            "start_date",
            "end_date",
            "is_current",
            "is_active",
            "note",
        )


class ClassGroupListSerializer(CRUDActionsMixin, serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    """سریالایزر خلاصه برای لیست کلاس‌ها."""

    term_title = serializers.CharField(source="term.title", read_only=True)
    teacher_name = serializers.CharField(source="teacher.__str__", read_only=True, allow_null=True)
    display_name = serializers.CharField(read_only=True)
    enrollment_count = serializers.IntegerField(read_only=True)
    created_at = PersianCharField(source="created_at_jalali", read_only=True)

    class Meta:
        model = ClassGroup
        fields = (
            "id",
            "code",
            "name",
            "display_name",
            "term",
            "offering",
            "term_title",
            "teacher",
            "teacher_name",
            "room",
            "capacity",
            "schedule",
            "enrollment_count",
            "is_active",
            "created_at",
            "actions",
        )


class ClassGroupDetailSerializer(CRUDActionsMixin, serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    """سریالایزر کامل کلاس."""

    term_title = serializers.CharField(source="term.title", read_only=True)
    teacher_name = serializers.CharField(source="teacher.__str__", read_only=True, allow_null=True)
    display_name = serializers.CharField(read_only=True)
    display_capacity = serializers.CharField(read_only=True)
    enrollment_count = serializers.IntegerField(read_only=True)
    enrollment_count_display = serializers.CharField(read_only=True)
    created_at = PersianCharField(source="created_at_jalali", read_only=True)
    updated_at = PersianCharField(source="updated_at_jalali", read_only=True)

    class Meta:
        model = ClassGroup
        fields = (
            "id",
            "code",
            "name",
            "display_name",
            "term",
            "offering",
            "term_title",
            "teacher",
            "teacher_name",
            "room",
            "capacity",
            "display_capacity",
            "schedule",
            "enrollment_count",
            "enrollment_count_display",
            "is_active",
            "created_at",
            "updated_at",
            "actions",
        )
        read_only_fields = ("created_at", "updated_at")


class ClassGroupCreateSerializer(serializers.ModelSerializer):
    """سریالایزر ساخت کلاس جدید."""

    class Meta:
        model = ClassGroup
        fields = (
            "term",
            "offering",
            "code",
            "name",
            "teacher",
            "room",
            "capacity",
            "schedule",
            "is_active",
        )


class ClassEnrollmentListSerializer(CRUDActionsMixin, serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    """سریالایزر خلاصه ثبت‌نام."""

    class_group_name = serializers.CharField(source="class_group.name", read_only=True)
    student_name = serializers.CharField(source="student.__str__", read_only=True)
    student_code = serializers.CharField(source="student.student_code", read_only=True, allow_null=True)
    enrollment_date = JalaliDateField()
    created_at = PersianCharField(source="created_at_jalali", read_only=True)

    class Meta:
        model = ClassEnrollment
        fields = (
            "id",
            "class_group",
            "class_group_name",
            "student",
            "student_name",
            "student_code",
            "enrollment_date",
            "is_active",
            "created_at", "actions",
        )


class ClassEnrollmentCreateSerializer(serializers.ModelSerializer):
    """سریالایزر ثبت‌نام دانش‌آموز در کلاس."""

    enrollment_date = JalaliDateField(required=False)

    class Meta:
        model = ClassEnrollment
        fields = (
            "class_group",
            "student",
            "enrollment_date",
            "is_active",
        )
