"""
Serializers for the dynamic forms API.

Response conventions follow the rest of the project (Persian labels in help
texts, Jalali timestamps via ``PersianCharField``, UUID ids). Client-controlled
protected fields — submitter, workflow instance, status, audit timestamps,
submission number — are read-only or excluded from inputs entirely.
"""
from __future__ import annotations

from rest_framework import serializers

from apps.core.fields import PersianCharField
from apps.core.serializers import CRUDActionsMixin
from apps.forms.models import (
    FormAttachment,
    FormComment,
    FormSchema,
    FormSubmission,
)


class FormSchemaSerializer(serializers.ModelSerializer):
    """Read serializer for schemas exposed to their allowed audiences."""

    created_at = PersianCharField(source="created_at_jalali", read_only=True)
    fields_definition = serializers.JSONField(source="fields", read_only=True)

    class Meta:
        model = FormSchema
        fields = (
            "id", "slug", "title", "description", "version", "is_active",
            "fields_definition", "published_at", "metadata",
            "created_at",
        )
        read_only_fields = fields


class FormSchemaSummarySerializer(serializers.ModelSerializer):
    created_at = PersianCharField(source="created_at_jalali", read_only=True)

    class Meta:
        model = FormSchema
        fields = ("id", "slug", "title", "version", "is_active", "created_at")
        read_only_fields = fields


class FormSubmissionListSerializer(CRUDActionsMixin, serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    schema_slug = serializers.SlugRelatedField(
        source="form_schema", slug_field="slug", read_only=True
    )
    schema_title = serializers.SlugRelatedField(
        source="form_schema", slug_field="title", read_only=True
    )
    submitter_username = serializers.SlugRelatedField(
        source="submitted_by", slug_field="username", read_only=True
    )
    created_at = PersianCharField(source="created_at_jalali", read_only=True)

    class Meta:
        model = FormSubmission
        fields = (
            "id", "submission_number", "schema_slug", "schema_title",
            "submitter_username", "status", "submitted_at",
            "created_at", "actions",
        )
        read_only_fields = fields


class FormSubmissionDetailSerializer(CRUDActionsMixin, serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    schema_slug = serializers.SlugRelatedField(
        source="form_schema", slug_field="slug", read_only=True
    )
    schema_version = serializers.IntegerField(
        source="schema_version_snapshot", read_only=True
    )
    submitter_username = serializers.SlugRelatedField(
        source="submitted_by", slug_field="username", read_only=True
    )
    reviewer_username = serializers.SlugRelatedField(
        source="reviewed_by", slug_field="username", read_only=True, allow_null=True
    )
    workflow_instance_id = serializers.UUIDField(read_only=True, allow_null=True)
    #: The card-table's quote-able code (REQ-2026-000042) — surfaced here so
    #: "my requests" never needs a second round-trip to /api/workflow/.
    tracking_number = serializers.SerializerMethodField()
    #: Live workflow state (running/completed/…) — richer than the synced
    #: submission.status for pure tracking purposes.
    workflow_status = serializers.SerializerMethodField()
    attachment_count = serializers.SerializerMethodField()
    created_at = PersianCharField(source="created_at_jalali", read_only=True)

    class Meta:
        model = FormSubmission
        fields = (
            "id", "submission_number", "schema_slug", "schema_version",
            "submitter_username", "data", "status", "notes",
            "workflow_instance_id", "tracking_number", "workflow_status",
            "submitted_at", "reviewed_at",
            "reviewer_username", "attachment_count", "created_at", "actions",
        )
        read_only_fields = fields

    def get_tracking_number(self, obj) -> str:
        return getattr(obj.workflow_instance, "tracking_number", "") or ""

    def get_workflow_status(self, obj) -> str:
        return getattr(obj.workflow_instance, "status", "") or ""

    def get_attachment_count(self, obj) -> int:
        return obj.attachments.count()


class FormSubmissionCreateSerializer(serializers.Serializer):
    """Input contract for creating a draft. The submitter is always request.user."""

    schema_slug = serializers.SlugField(max_length=120)
    data = serializers.JSONField(required=False, default=dict)
    notes = serializers.CharField(required=False, allow_blank=True, default="", max_length=2000)


class FormSubmissionUpdateSerializer(serializers.Serializer):
    """Input contract for draft updates."""

    data = serializers.JSONField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=2000)


class FormCommentSerializer(serializers.ModelSerializer):
    """Output for comments; internal ones are filtered out for unauthorized users."""

    author_username = serializers.SlugRelatedField(
        source="author", slug_field="username", read_only=True
    )
    created_at = PersianCharField(source="created_at_jalali", read_only=True)

    class Meta:
        model = FormComment
        fields = (
            "id", "author_username", "body", "is_internal",
            "parent", "created_at",
        )
        read_only_fields = fields


class FormCommentCreateSerializer(serializers.Serializer):
    body = serializers.CharField(max_length=5000, allow_blank=False)
    is_internal = serializers.BooleanField(required=False, default=False)
    parent = serializers.UUIDField(required=False, allow_null=True, default=None)


class FormAttachmentSerializer(serializers.ModelSerializer):
    """
    Attachment metadata. ``file`` (the storage path) is deliberately NOT
    exposed — downloads go through the permission-checked download view.
    """

    uploaded_by_username = serializers.SlugRelatedField(
        source="uploaded_by", slug_field="username", read_only=True
    )
    uploaded_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = FormAttachment
        fields = (
            "id", "submission", "field_key", "original_filename",
            "mime_type", "file_size", "checksum",
            "uploaded_by_username", "uploaded_at",
        )
        read_only_fields = fields
