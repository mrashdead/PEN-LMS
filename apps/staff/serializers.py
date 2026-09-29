"""Serializers for the staff operations API."""
from __future__ import annotations

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


class LeaveRequestSerializer(CRUDActionsMixin, serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    start_date = JalaliDateField()
    end_date = JalaliDateField()
    duration_display = serializers.CharField(read_only=True)
    unit_display = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    leave_type_name = serializers.CharField(source="leave_type.name", read_only=True)
    user_display = serializers.SerializerMethodField()

    class Meta:
        model = LeaveRequest
        fields = (
            "id", "user", "user_display", "person", "leave_type", "leave_type_name",
            "start_date", "end_date", "unit", "unit_display", "duration",
            "duration_display", "description", "attachment", "status",
            "status_display", "reviewed_by", "reviewed_at", "rejection_reason",
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
    leave_type = serializers.PrimaryKeyRelatedField(queryset=LeaveType.objects.none())
    start_date = JalaliDateField()
    end_date = JalaliDateField()
    unit = serializers.ChoiceField(
        choices=LeaveRequest.Unit.choices, default=LeaveRequest.Unit.DAY,
    )
    description = serializers.CharField(required=False, allow_blank=True)
    attachment = serializers.FileField(required=False, allow_null=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only active leave types may be selected — the catalog is the source
        # of truth, never a free string.
        self.fields["leave_type"].queryset = LeaveType.objects.filter(
            is_active=True, is_deleted=False,
        )

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
        return attrs


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
