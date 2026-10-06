"""Serializers for the call-log API."""
from __future__ import annotations

from rest_framework import serializers

from apps.core.serializers import CRUDActionsMixin
from apps.calls.models import (
    CallResult,
    CallFollowUpLog,
    CallSubject,
    FollowUpStatus,
    InboundCall,
    NEW_CALL_RESULT_CHOICES,
)


class InboundCallSerializer(CRUDActionsMixin, serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    called_at = serializers.DateTimeField()
    next_follow_up_at = serializers.DateTimeField(required=False, allow_null=True)
    receiver_display = serializers.SerializerMethodField()
    assignee_display = serializers.SerializerMethodField()
    needs_follow_up = serializers.BooleanField(read_only=True)
    is_overdue_follow_up = serializers.BooleanField(read_only=True)
    caller_display = serializers.CharField(read_only=True)
    result_display = serializers.CharField(source="get_result_display", read_only=True)
    follow_up_display = serializers.CharField(source="get_follow_up_status_display", read_only=True)
    direction_display = serializers.CharField(source="get_direction_display", read_only=True)

    class Meta:
        model = InboundCall
        fields = (
            "id", "caller_name", "caller_display", "caller_phone", "person",
            "receiver", "receiver_display", "department", "department_ref",
            "direction", "direction_display", "called_at", "subject", "subject_ref",
            "description", "result", "result_display", "follow_up_status",
            "follow_up_display", "assignee", "assignee_display",
            "next_follow_up_at", "needs_follow_up", "is_overdue_follow_up",
            "follow_up_note", "related_lead", "created_at", "updated_at",
            "actions",
        )
        read_only_fields = (
            "id", "receiver", "needs_follow_up", "is_overdue_follow_up",
            "caller_display", "created_at", "updated_at", "actions",
        )

    def get_receiver_display(self, obj) -> str:
        return _label_of(obj.receiver)

    def get_assignee_display(self, obj) -> str:
        return _label_of(obj.assignee)

class CallFollowUpLogSerializer(serializers.ModelSerializer):
    actor_display = serializers.SerializerMethodField()
    previous_status_display = serializers.CharField(source="get_previous_status_display", read_only=True)
    new_status_display = serializers.CharField(source="get_new_status_display", read_only=True)

    class Meta:
        model = CallFollowUpLog
        fields = ("actor_display", "previous_status_display", "new_status_display", "note", "next_follow_up_at", "created_at")

    def get_actor_display(self, obj) -> str:
        return _label_of(obj.actor)


class CallDetailSerializer(InboundCallSerializer):
    person_display = serializers.SerializerMethodField()
    department_ref_display = serializers.SerializerMethodField()
    subject_ref_display = serializers.SerializerMethodField()
    related_lead_display = serializers.SerializerMethodField()
    follow_up_history = serializers.SerializerMethodField()

    class Meta(InboundCallSerializer.Meta):
        fields = InboundCallSerializer.Meta.fields + (
            "person_display", "department_ref_display", "subject_ref_display",
            "related_lead_display", "follow_up_history",
        )

    def get_person_display(self, obj) -> str:
        return str(obj.person) if obj.person_id else ""

    def get_department_ref_display(self, obj) -> str:
        return str(obj.department_ref) if obj.department_ref_id else ""

    def get_subject_ref_display(self, obj) -> str:
        return str(obj.subject_ref) if obj.subject_ref_id else ""

    def get_related_lead_display(self, obj) -> str:
        return str(obj.related_lead) if obj.related_lead_id else ""

    def get_follow_up_history(self, obj):
        logs = obj.follow_up_logs.select_related("actor").order_by("-created_at")
        return CallFollowUpLogSerializer(logs, many=True).data


def _label_of(user) -> str:
    if user is None:
        return "—"
    full = " ".join(n for n in (getattr(user, "first_name", ""), getattr(user, "last_name", "")) if n)
    return full or getattr(user, "username", "—")


class CallSubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = CallSubject
        fields = ("id", "code", "name", "department", "is_active")
        read_only_fields = ("id",)


class CallSubjectField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        return CallSubject.objects.filter(is_active=True, is_deleted=False)


class DepartmentRefField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        from apps.education.models import Department

        return Department.objects.filter(is_active=True, is_deleted=False)


class CallPersonField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        from apps.persons.models import Person

        return Person.objects.filter(is_deleted=False)


class CallAssigneeField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        from django.contrib.auth import get_user_model

        return get_user_model().objects.filter(is_active=True, is_deleted=False)


class FollowUpAssigneeField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        from django.contrib.auth import get_user_model

        return get_user_model().objects.filter(is_active=True, is_deleted=False)


class CallCreateSerializer(serializers.Serializer):
    caller_name = serializers.CharField(max_length=256, required=False, allow_blank=True)
    caller_phone = serializers.CharField(max_length=20)
    called_at = serializers.DateTimeField(required=False)
    subject = serializers.CharField(max_length=256)
    subject_ref = CallSubjectField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True)
    result = serializers.ChoiceField(
        choices=NEW_CALL_RESULT_CHOICES, default=CallResult.ANSWERED, required=False,
    )
    direction = serializers.ChoiceField(
        choices=InboundCall.Direction.choices,
        default=InboundCall.Direction.INBOUND, required=False,
    )
    department = serializers.CharField(max_length=128, required=False, allow_blank=True)
    department_ref = DepartmentRefField(required=False, allow_null=True)
    person = CallPersonField(required=False, allow_null=True)
    assignee = CallAssigneeField(required=False, allow_null=True)
    next_follow_up_at = serializers.DateTimeField(required=False, allow_null=True)

    def validate_caller_phone(self, value):
        from apps.core.utils import english_numbers
        from apps.persons.validation import is_valid_iranian_mobile

        phone = english_numbers(value or "").strip()
        if not is_valid_iranian_mobile(phone):
            raise serializers.ValidationError("شماره تماس باید دقیقاً ۱۱ رقم و با ۰۹ شروع شود.")
        return phone

    def validate(self, attrs):
        if not (attrs.get("caller_name") or "").strip() and not attrs.get("person"):
            # Anonymous calls are allowed, but the UI should be explicit about
            # it — a recorded caller name or a linked person is required.
            attrs.setdefault("caller_name", "ناشناس")
        return attrs


class FollowUpSerializer(serializers.Serializer):
    new_status = serializers.ChoiceField(choices=FollowUpStatus.choices)
    note = serializers.CharField(required=False, allow_blank=True)
    next_follow_up_at = serializers.DateTimeField(required=False, allow_null=True)
    assignee = FollowUpAssigneeField(required=False, allow_null=True)
