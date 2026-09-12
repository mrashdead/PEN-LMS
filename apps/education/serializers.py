from __future__ import annotations

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
        fields = ("id", "code", "title", "description", "syllabus", "duration_hours",
                  "department", "prerequisites", "assessment_method",
                  "required_equipment", "learning_resources", "tuition",
                  "is_active", "version", "legacy_id", "created_at", "updated_at")
        read_only_fields = ("created_at", "updated_at")


class CourseLessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseLesson
        fields = ("id", "course", "lesson", "order", "required", "hours")


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ("id", "code", "title", "description", "objectives",
                  "department", "is_active", "legacy_id", "created_at", "updated_at")
        read_only_fields = ("created_at", "updated_at")


class CourseOfferingSerializer(serializers.ModelSerializer):
    seats_left = serializers.IntegerField(read_only=True, allow_null=True)
    seats_left_display = serializers.CharField(read_only=True)
    start_date = JalaliDateField(required=False, allow_null=True)
    end_date = JalaliDateField(required=False, allow_null=True)

    class Meta:
        model = CourseOffering
        fields = ("id", "course", "title", "department", "capacity",
                  "enrolled_count", "seats_left", "seats_left_display",
                  "start_date", "end_date", "location", "instructor", "status",
                  "tuition", "is_active", "legacy_id", "created_at", "updated_at")
        read_only_fields = ("created_at", "updated_at", "enrolled_count")


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
