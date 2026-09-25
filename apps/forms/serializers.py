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
    Request,
    RequestType,
)


class FormSchemaSerializer(serializers.ModelSerializer):
    """Read serializer for schemas exposed to their allowed audiences."""

    created_at = PersianCharField(source="created_at_jalali", read_only=True)
    fields_definition = serializers.JSONField(source="fields", read_only=True)
    request_type_code = serializers.SlugRelatedField(
        source="request_type", slug_field="code", read_only=True, allow_null=True,
    )
    request_type_title = serializers.SlugRelatedField(
        source="request_type", slug_field="title", read_only=True, allow_null=True,
    )
    workflow_code = serializers.SlugRelatedField(
        source="workflow_definition", slug_field="code", read_only=True, allow_null=True,
    )

    class Meta:
        model = FormSchema
        fields = (
            "id", "slug", "title", "description", "version", "is_active",
            "fields_definition", "published_at", "metadata",
            "request_type_code", "request_type_title", "workflow_code",
            "created_at",
        )
        read_only_fields = fields


class FormSchemaSummarySerializer(serializers.ModelSerializer):
    created_at = PersianCharField(source="created_at_jalali", read_only=True)
    request_type_code = serializers.SlugRelatedField(
        source="request_type", slug_field="code", read_only=True, allow_null=True,
    )
    request_type_title = serializers.SlugRelatedField(
        source="request_type", slug_field="title", read_only=True, allow_null=True,
    )

    class Meta:
        model = FormSchema
        fields = (
            "id", "slug", "title", "version", "is_active",
            "request_type_code", "request_type_title", "created_at",
        )
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
    request_number = serializers.SerializerMethodField()

    class Meta:
        model = FormSubmission
        fields = (
            "id", "submission_number", "schema_slug", "schema_title",
            "submitter_username", "status", "submitted_at",
            "request_number", "created_at", "actions",
        )
        read_only_fields = fields

    def get_request_number(self, obj) -> str:
        try:
            request = obj.business_request
        except Request.DoesNotExist:
            return ""
        return request.request_number or ""


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

    def get_request_number(self, obj) -> str:
        try:
            request = obj.business_request
        except Request.DoesNotExist:
            return ""
        return request.request_number or ""


class FormSubmissionCreateSerializer(serializers.Serializer):
    """Input contract for creating a draft. The submitter is always request.user."""

    schema_slug = serializers.SlugField(max_length=120)
    data = serializers.JSONField(required=False, default=dict)
    notes = serializers.CharField(required=False, allow_blank=True, default="", max_length=2000)


class RequestTypeSerializer(serializers.ModelSerializer):
    """Business request catalog exposed to the unified request UI."""

    workflow_code = serializers.SlugRelatedField(
        source="workflow_definition", slug_field="code", read_only=True,
        allow_null=True,
    )
    schema_slugs = serializers.SerializerMethodField()
    schemas = serializers.SerializerMethodField()

    class Meta:
        model = RequestType
        fields = (
            "id", "code", "title", "description", "kind", "is_active",
            "workflow_code", "metadata",
            "schema_slugs", "schemas",
        )
        read_only_fields = fields

    def get_schema_slugs(self, obj):
        return list(
            obj.form_schemas.filter(is_active=True, is_deleted=False)
            .order_by("-version")
            .values_list("slug", flat=True)
        )

    def get_schemas(self, obj):
        return list(
            obj.form_schemas.filter(is_active=True, is_deleted=False)
            .order_by("-version")
            .values("slug", "title", "version")
        )


class RequestListSerializer(CRUDActionsMixin, serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    request_type_code = serializers.SlugRelatedField(
        source="request_type", slug_field="code", read_only=True,
    )
    request_type_title = serializers.SlugRelatedField(
        source="request_type", slug_field="title", read_only=True,
    )
    requester_username = serializers.SlugRelatedField(
        source="requester", slug_field="username", read_only=True,
    )
    tracking_number = serializers.SerializerMethodField()
    current_state_code = serializers.SerializerMethodField()
    current_state_title = serializers.SerializerMethodField()
    workflow_instance_id = serializers.SerializerMethodField()
    created_at = PersianCharField(source="created_at_jalali", read_only=True)

    class Meta:
        model = Request
        fields = (
            "id", "request_number", "request_type_code", "request_type_title",
            "requester_username", "status", "tracking_number",
            "current_state_code", "current_state_title", "workflow_instance_id", "submitted_at",
            "created_at", "actions",
        )
        read_only_fields = fields

    def get_tracking_number(self, obj) -> str:
        return getattr(obj.workflow_instance, "tracking_number", "") or obj.request_number or ""

    def get_current_state_code(self, obj) -> str:
        return getattr(obj.current_state, "code", "") or ""

    def get_current_state_title(self, obj) -> str:
        return getattr(obj.current_state, "name", "") or ""

    def get_workflow_instance_id(self, obj):
        return str(obj.workflow_instance_id) if obj.workflow_instance_id else None

    def get_actions(self, obj):
        """Expose request actions, not legacy submission CRUD actions.

        A request is cancelled or sent through its business lifecycle; it is
        not deleted through the old workflow-instance delete endpoint.
        """
        request = self.context.get("request")
        user = getattr(request, "user", None)
        is_requester = bool(user and getattr(user, "pk", None) == obj.requester_id)
        editable = is_requester and obj.status in {
            Request.Status.DRAFT,
            Request.Status.CHANGES_REQUESTED,
        }
        cancellable = is_requester and not obj.is_terminal
        return {
            "view": True,
            "edit": editable,
            "delete": False,
            "submit": editable,
            "cancel": cancellable,
        }


class RequestDetailSerializer(RequestListSerializer):
    subject_person_id = serializers.UUIDField(read_only=True, allow_null=True)
    submission_id = serializers.UUIDField(source="form_submission_id", read_only=True, allow_null=True)
    workflow_instance_id = serializers.UUIDField(read_only=True, allow_null=True)
    workflow_status = serializers.SerializerMethodField()
    data = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()
    form_schema = serializers.SerializerMethodField()
    history = serializers.SerializerMethodField()
    available_transitions = serializers.SerializerMethodField()
    pending_tasks = serializers.SerializerMethodField()

    class Meta(RequestListSerializer.Meta):
        fields = RequestListSerializer.Meta.fields + (
            "subject_person_id", "submission_id", "workflow_instance_id",
            "workflow_status", "data", "notes", "form_schema", "history",
            "metadata", "last_action_at", "completed_at",
            "available_transitions", "pending_tasks",
        )

    def get_workflow_status(self, obj) -> str:
        return getattr(obj.workflow_instance, "status", "") or ""

    def get_data(self, obj):
        data = dict(obj.form_submission.data or {}) if obj.form_submission else {}
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user is None or not getattr(user, "is_authenticated", False):
            return {}
        roles = set(user.role_codes()) if hasattr(user, "role_codes") else set()
        if {
            "manager", "workflow_admin"
        } & roles or obj.requester_id == user.pk:
            return data
        subject_user_id = getattr(obj.subject_person, "user_id", None)
        if subject_user_id and subject_user_id == user.pk:
            return data
        schema = obj.form_submission.form_schema if obj.form_submission else None
        sensitive = set((schema.metadata or {}).get("sensitive_fields", [])) if schema else set()
        if schema:
            sensitive.update(
                field.get("key")
                for field in (schema.fields or [])
                if isinstance(field, dict)
                and (
                    field.get("sensitive")
                    or any(token in str(field.get("key", "")).lower() for token in ("health", "medical", "national_code"))
                )
            )
        return {
            key: ("[محرمانه]" if key in sensitive else value)
            for key, value in data.items()
        }

    def get_notes(self, obj):
        return obj.form_submission.notes if obj.form_submission else ""

    def get_form_schema(self, obj):
        schema = obj.form_submission.form_schema if obj.form_submission else None
        if schema is None:
            return None
        return {
            "slug": schema.slug,
            "title": schema.title,
            "version": schema.version,
            "fields": schema.effective_fields() if hasattr(schema, "effective_fields") else schema.fields,
        }

    def get_history(self, obj):
        instance = obj.workflow_instance
        if instance is None:
            return []
        return [
            {
                "id": str(log.pk),
                "action": log.action,
                "actor_username": getattr(log.actor, "username", ""),
                "from_state_code": getattr(log.from_state, "code", None),
                "to_state_code": getattr(log.to_state, "code", None),
                "from_state_title": getattr(log.from_state, "name", None),
                "to_state_title": getattr(log.to_state, "name", None),
                "comment": log.comment,
                "created_at": log.created_at_jalali,
            }
            for log in instance.action_logs.select_related(
                "actor", "from_state", "to_state"
            ).order_by("created_at")[:100]
        ]

    def get_available_transitions(self, obj):
        instance = obj.workflow_instance
        user = (self.context.get("request") or {}).user if self.context.get("request") else None
        if instance is None or user is None or not getattr(user, "is_authenticated", False):
            return []
        from apps.workflow.services import WorkflowEngineService

        return [
            {
                "id": str(transition.pk),
                "name": transition.name,
                "kind": transition.kind,
                "requires_comment": transition.requires_comment,
                "to_state": transition.to_state.code,
                "to_state_title": transition.to_state.name,
            }
            for transition in WorkflowEngineService().get_available_transitions(instance, user)
        ]

    def get_pending_tasks(self, obj):
        instance = obj.workflow_instance
        if instance is None:
            return []
        from apps.tasks.models import WorkflowTask

        return [
            {
                "id": str(task.pk),
                "assignee_id": str(task.assignee_id),
                "assignee_username": getattr(task.assignee, "username", ""),
                "state_code": task.state.code,
                "state_title": task.state.name,
                "status": task.status,
                "due_date": task.due_date.isoformat() if task.due_date else None,
            }
            for task in WorkflowTask.objects.filter(
                instance=instance,
                status=WorkflowTask.Status.PENDING,
                is_deleted=False,
            ).select_related("state", "assignee")
        ]


class RequestCreateSerializer(serializers.Serializer):
    schema_slug = serializers.SlugField(max_length=120)
    data = serializers.JSONField(required=False, default=dict)
    notes = serializers.CharField(required=False, allow_blank=True, default="", max_length=2000)


class RequestUpdateSerializer(serializers.Serializer):
    data = serializers.JSONField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=2000)


class RequestTransitionSerializer(serializers.Serializer):
    transition_id = serializers.UUIDField()
    comment = serializers.CharField(required=False, allow_blank=True, default="", max_length=5000)
    metadata = serializers.JSONField(required=False, default=dict)
    idempotency_key = serializers.CharField(required=False, allow_blank=False, max_length=200)


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
