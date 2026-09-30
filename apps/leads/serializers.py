from __future__ import annotations

from django.utils import timezone
from rest_framework import serializers

from apps.education.models import Course, CourseLesson, Lesson
from apps.leads.selectors import assessors
from apps.leads.models import Lead
from apps.persons.models import Person
from apps.persons.validation import national_code_error


class ActiveTeacherField(serializers.PrimaryKeyRelatedField):
    """Resolve eligible teachers at request time, including timed type assignments."""

    def get_queryset(self):
        return assessors()


class LeadSerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(read_only=True)
    assessor_name = serializers.SerializerMethodField()
    course_title = serializers.CharField(source="course.title", read_only=True, allow_null=True)
    lesson_title = serializers.CharField(source="lesson.title", read_only=True, allow_null=True)
    enrolled_person_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Lead
        fields = (
            "id", "code", "student_name", "age", "phone", "neighborhood", "father_job", "mother_job",
            "allergy_notes", "assessment_date", "assessment_time", "assessor", "assessor_name",
            "course", "course_title", "lesson", "lesson_title", "status", "status_label",
            "assessment_score", "assessment_result", "recommendation", "enrolled_person",
            "enrolled_person_name", "created_by_name", "created_at",
        )
        read_only_fields = ("id", "code", "status", "created_at", "created_by")

    def get_assessor_name(self, obj):
        return obj.assessor.display_name if obj.assessor_id else ""

    def get_enrolled_person_name(self, obj):
        return obj.enrolled_person.display_name if obj.enrolled_person_id else ""

    def get_created_by_name(self, obj):
        user_name = obj.created_by.get_full_name()
        if user_name:
            return user_name
        person = getattr(obj.created_by, "person", None)
        return person.display_name if person else obj.created_by.username


class TeacherLeadSerializer(serializers.ModelSerializer):
    """Assessment-facing fields only; staff creator/report metadata stays private."""
    status_label = serializers.CharField(read_only=True)
    assessor_name = serializers.SerializerMethodField()
    course_title = serializers.CharField(source="course.title", read_only=True, allow_null=True)
    lesson_title = serializers.CharField(source="lesson.title", read_only=True, allow_null=True)

    class Meta:
        model = Lead
        fields = (
            "id", "code", "student_name", "age", "phone", "neighborhood", "allergy_notes",
            "assessment_date", "assessment_time", "assessor_name", "course_title", "lesson_title",
            "status", "status_label", "assessment_score", "assessment_result",
        )
        read_only_fields = fields

    def get_assessor_name(self, obj):
        return obj.assessor.display_name if obj.assessor_id else ""


class LeadCreateSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(max_length=200, required=True, trim_whitespace=True)
    age = serializers.IntegerField(min_value=0, max_value=120, required=True)
    neighborhood = serializers.CharField(max_length=160, required=True, trim_whitespace=True)
    assessment_date = serializers.DateField(required=True)
    assessment_time = serializers.TimeField(required=True)
    assessor = ActiveTeacherField(queryset=Person.objects.none(), required=True)

    class Meta:
        model = Lead
        fields = (
            "student_name", "age", "phone", "neighborhood", "father_job", "mother_job", "allergy_notes",
            "assessment_date", "assessment_time", "assessor", "course", "lesson",
        )

    def validate_phone(self, value):
        translation = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
        value = str(value).translate(translation).strip().replace(" ", "")
        if not value.startswith("09") or len(value) != 11 or not value.isdigit():
            raise serializers.ValidationError("شماره تماس باید ۱۱ رقم و با ۰۹ شروع شود.")
        return value

    def validate(self, attrs):
        session_date = attrs["assessment_date"]
        today = timezone.localdate()
        if session_date < today:
            raise serializers.ValidationError({"assessment_date": "تاریخ جلسه نمی‌تواند در گذشته باشد."})
        if session_date == today and attrs["assessment_time"] <= timezone.localtime().time().replace(second=0, microsecond=0):
            raise serializers.ValidationError({"assessment_time": "برای امروز، ساعتی بعد از زمان فعلی انتخاب کنید."})
        if attrs.get("course") and attrs.get("lesson"):
            if not CourseLesson.objects.filter(
                course=attrs["course"], lesson=attrs["lesson"]
            ).exists():
                raise serializers.ValidationError({"lesson": "این درس در دوره انتخاب‌شده وجود ندارد."})
        return attrs


class LeadAssessmentSerializer(serializers.Serializer):
    score = serializers.IntegerField(min_value=0, max_value=100, required=False, allow_null=True)
    result = serializers.CharField(required=True, allow_blank=False)


class LeadPersonCreateSerializer(serializers.Serializer):
    """Minimum identity fields needed to turn a qualified lead into a student."""
    national_code = serializers.CharField(max_length=10, min_length=10)
    student_code = serializers.CharField(max_length=32, required=True, allow_blank=False)
    father_name = serializers.CharField(max_length=128, required=False, allow_blank=True)

    def validate_national_code(self, value):
        translation = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
        value = str(value).translate(translation).strip()
        error = national_code_error(value, require_location=True)
        if error:
            raise serializers.ValidationError(error)
        return value


class LeadRecommendationSerializer(serializers.Serializer):
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all())
    lesson = serializers.PrimaryKeyRelatedField(queryset=Lesson.objects.all(), required=False, allow_null=True)
    recommendation = serializers.CharField(required=False, allow_blank=True)


class LeadEnrollmentSerializer(serializers.Serializer):
    enrolled_person = serializers.PrimaryKeyRelatedField(
        queryset=Person.objects.filter(person_type=Person.Type.STUDENT, is_active=True)
    )
