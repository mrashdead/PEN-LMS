from __future__ import annotations

from django.db import transaction
from rest_framework import serializers

from apps.core.fields import JalaliDateField, PersianCharField
from apps.education.models import (
    AttendanceRecord,
    ClassSession,
    Course,
    CourseLesson,
    CourseOffering,
    Department,
    GradeRecord,
    Lesson,
    Location,
    OfferingEnrollment,
)


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ("id", "code", "name", "description", "parent", "is_active", "legacy_id")


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ("id", "code", "name", "building", "capacity", "equipment",
                  "is_active", "legacy_id")


class LessonSerializer(serializers.ModelSerializer):
    prerequisites = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Lesson.objects.all(), required=False
    )

    class Meta:
        model = Lesson
        fields = ("id", "code", "title", "title_en", "description", "syllabus",
                  "duration_hours", "audience_age",
                  "space_type", "department", "prerequisites",
                  "required_equipment", "learning_resources", "tuition",
                  "is_active", "version", "legacy_id", "created_at", "updated_at")
        # code is auto-generated (ls-0001) on save — never client-supplied.
        read_only_fields = ("id", "code", "created_at", "updated_at", "version")


class CourseLessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseLesson
        fields = ("id", "course", "lesson", "order", "required", "hours")


class CourseSerializer(serializers.ModelSerializer):
    # lessons is the M2M through CourseLesson — DRF can't write a through-M2M
    # directly, so we accept a flat id list and manage rows in create/update.
    lessons = serializers.ListField(
        child=serializers.UUIDField(), required=False, write_only=True
    )
    lesson_titles = serializers.SerializerMethodField()
    total_tuition = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ("id", "code", "title", "description", "objectives",
                  "department", "tuition", "lessons", "lesson_titles",
                  "total_tuition", "is_active", "legacy_id", "created_at", "updated_at")
        read_only_fields = ("id", "code", "created_at", "updated_at")

    def get_lesson_titles(self, obj) -> list:
        return [
            {"id": str(l.id), "title": l.title, "tuition": l.tuition or 0}
            for l in obj.lessons.all()
        ]

    def get_total_tuition(self, obj) -> int:
        """Sum of the linked lessons' tuition (the course bundle price)."""
        return sum(l.tuition or 0 for l in obj.lessons.all())

    def _sync_lessons(self, course, lesson_ids):
        """Replace the course's lessons, preserving submitted order.

        Delete-then-recreate avoids the (course, order) unique-constraint
        collision that in-place renumbering would hit mid-update.
        """
        wanted = list(Lesson.objects.filter(pk__in=lesson_ids))
        by_id = {str(l.pk): l for l in wanted}
        ordered = [by_id[str(pk)] for pk in lesson_ids if str(pk) in by_id]
        course.course_lessons.all().delete()
        CourseLesson.objects.bulk_create([
            CourseLesson(course=course, lesson=lesson, order=i + 1)
            for i, lesson in enumerate(ordered)
        ])

    @transaction.atomic
    def create(self, validated_data):
        lesson_ids = validated_data.pop("lessons", [])
        course = Course.objects.create(**validated_data)
        self._sync_lessons(course, lesson_ids)
        return course

    @transaction.atomic
    def update(self, instance, validated_data):
        lesson_ids = validated_data.pop("lessons", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if lesson_ids is not None:
            self._sync_lessons(instance, lesson_ids)
        return instance


class CourseOfferingSerializer(serializers.ModelSerializer):
    seats_left = serializers.IntegerField(read_only=True, allow_null=True)
    seats_left_display = serializers.CharField(read_only=True)
    start_date = JalaliDateField(required=False, allow_null=True)
    end_date = JalaliDateField(required=False, allow_null=True)
    course_title = serializers.CharField(source="course.title", read_only=True)
    course_tuition = serializers.IntegerField(source="course.tuition", read_only=True)
    lesson_titles = serializers.SerializerMethodField()

    class Meta:
        model = CourseOffering
        fields = ("id", "course", "course_title", "course_tuition", "title",
                  "department", "capacity", "enrolled_count", "seats_left",
                  "seats_left_display", "start_date", "end_date", "location",
                  "instructor", "schedule", "lesson_titles", "status",
                  "tuition", "is_active", "legacy_id", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at", "enrolled_count")

    def get_lesson_titles(self, obj) -> list:
        """The offering's course lessons — shown read-only in the offering form."""
        course = getattr(obj, "course", None)
        if course is None:
            return []
        return [
            {"id": str(l.id), "title": l.title, "tuition": l.tuition or 0}
            for l in course.lessons.all()
        ]


class ClassSessionSerializer(serializers.ModelSerializer):
    session_date = JalaliDateField()

    class Meta:
        model = ClassSession
        fields = ("id", "offering", "class_group", "lesson", "session_number",
                  "title", "session_date", "start_time", "end_time", "teacher",
                  "location", "status", "legacy_id", "created_at", "updated_at")
        read_only_fields = ("created_at", "updated_at")


class AttendanceRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceRecord
        fields = ("id", "session", "student", "status", "note",
                  "recorded_by", "created_at")
        read_only_fields = ("created_at",)


class GradeRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradeRecord
        fields = ("id", "student", "session", "offering", "lesson", "result",
                  "teacher_note", "evaluated_by", "created_at", "updated_at")
        read_only_fields = ("created_at", "updated_at")


class OfferingEnrollmentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.get_full_name", read_only=True)
    offering_title = serializers.CharField(source="offering.title", read_only=True)
    enrolled_at = JalaliDateField(required=False)

    class Meta:
        model = OfferingEnrollment
        fields = ("id", "offering", "offering_title", "student", "student_name",
                  "course_amount", "discount_type", "discount_value", "final_amount",
                  "payment_method", "cheque_count", "cheques", "reference",
                  "enrolled_at", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "final_amount", "created_at", "updated_at")

    def validate(self, attrs):
        # Mirror the model's single rule so the API returns field errors, not 500.
        offering = attrs.get("offering") or (self.instance.offering if self.instance else None)
        student = attrs.get("student") or (self.instance.student if self.instance else None)
        if offering is not None and student is not None:
            course_amount = attrs.get("course_amount")
            if course_amount in (None, 0):
                attrs["course_amount"] = sum(l.tuition or 0 for l in offering.course.lessons.all())
        dt = attrs.get("discount_type", getattr(self.instance, "discount_type", "none"))
        dv = attrs.get("discount_value", getattr(self.instance, "discount_value", 0)) or 0
        if dt == OfferingEnrollment.DiscountType.PERCENT and dv > 100:
            raise serializers.ValidationError({"discount_value": "درصد تخفیف نمی‌تواند بیش از ۱۰۰ باشد."})
        pm = attrs.get("payment_method", getattr(self.instance, "payment_method", "cash"))
        cheques = attrs.get("cheques", getattr(self.instance, "cheques", []))
        if pm == OfferingEnrollment.PaymentMethod.CHEQUE and not cheques:
            raise serializers.ValidationError({"cheques": "برای پرداخت چک، حداقل یک چک وارد کنید."})
        # compute final_amount server-side (never trust client)
        base = attrs.get("course_amount", getattr(self.instance, "course_amount", 0)) or 0
        if dt == OfferingEnrollment.DiscountType.PERCENT:
            attrs["_final"] = base - int(round(base * min(max(dv, 0), 100) / 100))
        elif dt == OfferingEnrollment.DiscountType.AMOUNT:
            attrs["_final"] = max(base - dv, 0)
        else:
            attrs["_final"] = base
        return attrs

    def create(self, validated_data):
        final = validated_data.pop("_final", 0)
        validated_data["final_amount"] = final
        return super().create(validated_data)

    def update(self, instance, validated_data):
        final = validated_data.pop("_final", None)
        if final is not None:
            validated_data["final_amount"] = final
        return super().update(instance, validated_data)
