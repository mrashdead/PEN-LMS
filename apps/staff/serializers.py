"""Serializers for the staff operations API."""
from __future__ import annotations

import datetime as dt

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from apps.core.fields import JalaliDateField
from apps.core.serializers import CRUDActionsMixin
from apps.staff.models import (
    LeaveRequest,
    LeaveType,
    ReviewStatus,
    TimesheetEntry,
    WorkReport,
)


class TimesheetEntrySerializer(CRUDActionsMixin, serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    work_date = JalaliDateField()
    duration_minutes = serializers.SerializerMethodField()
    duration_hours = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    user_display = serializers.SerializerMethodField()

    class Meta:
        model = TimesheetEntry
        fields = (
            "id", "user", "user_display", "work_date", "kind", "check_in", "check_out",
            "duration_minutes", "duration_hours", "note", "status",
            "status_display", "reviewed_by", "reviewed_at", "rejection_reason",
            "is_open", "created_at", "updated_at", "actions",
        )
        read_only_fields = (
            "id", "user", "duration_minutes", "duration_hours", "status",
            "status_display", "reviewed_by", "reviewed_at", "rejection_reason",
            "is_open", "created_at", "updated_at", "actions",
        )

    def get_duration_minutes(self, obj) -> int | None:
        return obj.duration_minutes

    def get_duration_hours(self, obj) -> float | None:
        return obj.duration_hours

    def get_status_display(self, obj) -> str:
        return obj.get_status_display()

    def get_user_display(self, obj) -> str:
        person = obj.person
        if person:
            return person.display_name
        full_name = " ".join(
            part for part in (obj.user.first_name, obj.user.last_name) if part
        )
        return full_name or obj.user.username


class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = ("id", "code", "name", "accrual", "accrual_display",
                  "default_days", "requires_document", "is_active")
        read_only_fields = ("id",)

    accrual_display = serializers.CharField(source="get_accrual_display", read_only=True)


class TeacherOptionSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ("id", "display_name")

    def get_display_name(self, obj):
        person = getattr(obj, "person", None)
        if person:
            return person.display_name
        full = " ".join(part for part in (obj.first_name, obj.last_name) if part)
        return full or obj.username


class ManualTimesheetSerializer(serializers.Serializer):
    """Manual time entry for a teacher, expressed in the project's local time."""
    user = serializers.PrimaryKeyRelatedField(queryset=get_user_model().objects.filter(
        roles__code="teacher", is_active=True, is_deleted=False,
    ).distinct())
    work_date = JalaliDateField()
    check_in_time = serializers.TimeField()
    check_out_time = serializers.TimeField(required=False, allow_null=True)
    kind = serializers.ChoiceField(choices=TimesheetEntry.Kind.choices, default=TimesheetEntry.Kind.REGULAR)
    note = serializers.CharField(max_length=500, required=False, allow_blank=True)

    def validate_user(self, value):
        if "teacher" not in value.role_codes():
            raise serializers.ValidationError("کاربر انتخاب‌شده مدرس فعال نیست.")
        return value

    def validate(self, attrs):
        instance = self.instance
        day = attrs.get("work_date", instance.work_date if instance else None)
        user = attrs.get("user", instance.user if instance else None)
        kind = attrs.get("kind", instance.kind if instance else TimesheetEntry.Kind.REGULAR)
        check_in = attrs.get("check_in_time")
        check_out = attrs.get("check_out_time")
        if instance and check_in is None:
            check_in = timezone.localtime(instance.check_in).time()
        if instance and "check_out_time" not in attrs:
            check_out = timezone.localtime(instance.check_out).time() if instance.check_out else None
        if day and day > timezone.localdate():
            raise serializers.ValidationError({"work_date": "تاریخ کاری نمی‌تواند در آینده باشد."})
        if check_in and check_out and check_out <= check_in:
            raise serializers.ValidationError({"check_out_time": "ساعت خروج باید بعد از ساعت ورود باشد."})
        if day and user and check_in:
            existing = TimesheetEntry.objects.filter(
                user=user, work_date=day, kind=kind, is_deleted=False,
            )
            if instance:
                existing = existing.exclude(pk=instance.pk)
            for row in existing.only("check_in", "check_out"):
                other_start = timezone.localtime(row.check_in).time()
                other_end = timezone.localtime(row.check_out).time() if row.check_out else None
                overlaps = (
                    other_end is None
                    or (check_in < other_end if check_out is None else check_in < other_end and other_start < check_out)
                )
                if overlaps:
                    raise serializers.ValidationError({
                        "check_in_time": "این بازه با نوبت دیگری هم‌پوشانی دارد یا نوبت قبلی هنوز خروج ندارد.",
                    })
        if instance and instance.status != ReviewStatus.PENDING:
            raise serializers.ValidationError("فقط نوبت‌های در انتظار بررسی قابل ویرایش هستند.")
        return attrs

    @staticmethod
    def as_datetime(day, clock):
        return timezone.make_aware(dt.datetime.combine(day, clock), timezone.get_current_timezone())

    def save(self, **kwargs):
        data = {**self.validated_data, **kwargs}
        day = data.get("work_date", self.instance.work_date if self.instance else None)
        check_in_time = data.get("check_in_time")
        if check_in_time is None:
            check_in_time = timezone.localtime(self.instance.check_in).time()
        check_out_time = data.get("check_out_time")
        if self.instance and "check_out_time" not in data:
            check_out_time = timezone.localtime(self.instance.check_out).time() if self.instance.check_out else None
        if self.instance:
            entry = self.instance
            entry.work_date = day
            entry.check_in = self.as_datetime(day, check_in_time)
            entry.check_out = self.as_datetime(day, check_out_time) if check_out_time else None
            if "user" in data:
                entry.user = data["user"]
                entry.person = getattr(entry.user, "person", None)
            entry.kind = data.get("kind", entry.kind)
            entry.note = data.get("note", entry.note)
            entry.save(update_fields=["user", "person", "work_date", "check_in", "check_out", "kind", "note", "updated_at"])
            return entry
        user = data["user"]
        return TimesheetEntry.objects.create(
            user=user, person=getattr(user, "person", None), work_date=day,
            kind=data.get("kind", TimesheetEntry.Kind.REGULAR),
            check_in=self.as_datetime(day, check_in_time),
            check_out=self.as_datetime(day, check_out_time) if check_out_time else None,
            note=data.get("note", ""), status=ReviewStatus.PENDING,
        )


class LeaveRequestSerializer(CRUDActionsMixin, serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    start_date = JalaliDateField()
    end_date = JalaliDateField()
    start_time = serializers.TimeField(read_only=True)
    end_time = serializers.TimeField(read_only=True)
    duration_display = serializers.CharField(read_only=True)
    unit_display = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    leave_type_name = serializers.SerializerMethodField()
    user_display = serializers.SerializerMethodField()
    reviewed_by_display = serializers.SerializerMethodField()

    class Meta:
        model = LeaveRequest
        fields = (
            "id", "user", "user_display", "person", "leave_type", "leave_type_name",
            "start_date", "end_date", "start_time", "end_time", "unit", "unit_display", "duration",
            "duration_display", "description", "attachment", "status",
            "status_display", "reviewed_by", "reviewed_by_display", "reviewed_at", "rejection_reason",
            "created_at", "updated_at", "actions",
        )
        read_only_fields = (
            "id", "user", "person", "duration", "status", "status_display",
            "reviewed_by", "reviewed_at", "rejection_reason",
            "created_at", "updated_at", "actions",
        )

    def get_user_display(self, obj) -> str:
        user = obj.user
        full = " ".join(n for n in (getattr(user, "first_name", ""), getattr(user, "last_name", "")) if n)
        return full or getattr(user, "username", str(user.pk))

    def get_unit_display(self, obj) -> str:
        return obj.get_unit_display()

    def get_status_display(self, obj) -> str:
        return obj.get_status_display()

    def get_leave_type_name(self, obj) -> str | None:
        return obj.leave_type.name if obj.leave_type_id else None

    def get_reviewed_by_display(self, obj) -> str | None:
        user = obj.reviewed_by
        if not user:
            return None
        full = " ".join(n for n in (user.first_name, user.last_name) if n)
        return full or user.username


class WorkReportSerializer(CRUDActionsMixin, serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    report_date = JalaliDateField()
    spent_hours = serializers.SerializerMethodField()
    user_display = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = WorkReport
        fields = (
            "id", "user", "user_display", "person", "report_date", "title",
            "description", "spent_minutes", "spent_hours", "timesheet",
            "status", "status_display", "reviewed_by", "reviewed_at",
            "rejection_reason", "created_at", "updated_at", "actions",
        )
        read_only_fields = (
            "id", "user", "person", "status", "status_display", "reviewed_by",
            "reviewed_at", "rejection_reason", "created_at", "updated_at", "actions",
        )

    def get_spent_hours(self, obj) -> float:
        return obj.spent_hours

    def get_status_display(self, obj) -> str:
        return obj.get_status_display()

    def get_user_display(self, obj) -> str:
        user = obj.user
        full = " ".join(n for n in (getattr(user, "first_name", ""), getattr(user, "last_name", "")) if n)
        return full or getattr(user, "username", str(user.pk))


class ClockInSerializer(serializers.Serializer):
    work_date = JalaliDateField(required=False)
    kind = serializers.ChoiceField(
        choices=TimesheetEntry.Kind.choices, default=TimesheetEntry.Kind.REGULAR,
    )
    note = serializers.CharField(max_length=500, required=False, allow_blank=True)


class ReviewSerializer(serializers.Serializer):
    """Body for every approve/reject endpoint — one contract, three resources."""

    decision = serializers.ChoiceField(choices=["approved", "rejected"])
    comment = serializers.CharField(required=False, allow_blank=True)
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
    override_minutes = serializers.IntegerField(required=False, min_value=0, max_value=1440)


class LeaveRequestCreateSerializer(serializers.Serializer):
    start_date = JalaliDateField()
    end_date = JalaliDateField()
    start_time = serializers.TimeField(required=False, allow_null=True)
    end_time = serializers.TimeField(required=False, allow_null=True)
    unit = serializers.ChoiceField(
        choices=LeaveRequest.Unit.choices, default=LeaveRequest.Unit.DAY,
    )
    description = serializers.CharField(required=False, allow_blank=True)
    attachment = serializers.FileField(required=False, allow_null=True)

    def to_internal_value(self, data):
        if "leave_type" in data:
            raise serializers.ValidationError({"leave_type": "نوع مرخصی هنگام بررسی توسط مسئول تعیین می‌شود."})
        return super().to_internal_value(data)

    def validate(self, attrs):
        start, end = attrs.get("start_date"), attrs.get("end_date")
        if start and end and end < start:
            raise serializers.ValidationError(
                {"end_date": "تاریخ پایان باید بعد از شروع باشد."}
            )
        if attrs.get("unit") == LeaveRequest.Unit.HALF_DAY and start != end:
            raise serializers.ValidationError(
                {"unit": "مرخصی نیم‌روز فقط برای یک روز مجاز است."}
            )
        unit = attrs.get("unit", LeaveRequest.Unit.DAY)
        start_time, end_time = attrs.get("start_time"), attrs.get("end_time")
        if unit == LeaveRequest.Unit.HOUR:
            if start != end:
                raise serializers.ValidationError(
                    {"end_date": "مرخصی ساعتی باید برای یک روز باشد."}
                )
            if not start_time or not end_time:
                raise serializers.ValidationError(
                    {"start_time": "ساعت شروع و پایان را برای مرخصی ساعتی وارد کنید."}
                )
            if start_time.second or start_time.microsecond or end_time.second or end_time.microsecond:
                raise serializers.ValidationError(
                    {"start_time": "ساعت را با دقت دقیقه وارد کنید."}
                )
            if end_time <= start_time:
                raise serializers.ValidationError(
                    {"end_time": "ساعت پایان باید بعد از ساعت شروع باشد."}
                )
        elif start_time or end_time:
            raise serializers.ValidationError(
                {"start_time": "ساعت شروع و پایان فقط برای مرخصی ساعتی ثبت می‌شود."}
            )
        return attrs


class LeaveReviewSerializer(ReviewSerializer):
    leave_type = serializers.PrimaryKeyRelatedField(queryset=LeaveType.objects.filter(
        code__in=LeaveType.STAFF_REQUEST_CODES, is_active=True, is_deleted=False,
    ))


class WorkReportCreateSerializer(serializers.Serializer):
    report_date = JalaliDateField(required=False)
    title = serializers.CharField(max_length=256)
    description = serializers.CharField(required=False, allow_blank=True)
    spent_minutes = serializers.IntegerField(required=False, min_value=0, max_value=1440)
    timesheet = serializers.PrimaryKeyRelatedField(
        queryset=TimesheetEntry.objects.none(), required=False, allow_null=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request") if self.context else None
        user = getattr(request, "user", None)
        if user is not None and getattr(user, "is_authenticated", False):
            self.fields["timesheet"].queryset = TimesheetEntry.objects.filter(
                user=user, is_deleted=False,
            )
