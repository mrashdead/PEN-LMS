from __future__ import annotations

from rest_framework import serializers

from apps.workflow.models import ActionLog, Instance, Transition, WorkflowDefinition


class WorkflowDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowDefinition
        fields = ("id", "code", "name", "description", "is_active", "version", "created_at", "updated_at")


class InstanceListSerializer(serializers.ModelSerializer):
    workflow_definition_code = serializers.SlugRelatedField(
        source="workflow_definition", slug_field="code", read_only=True
    )
    current_state_code = serializers.SlugRelatedField(
        source="current_state", slug_field="code", read_only=True, allow_null=True
    )
    requester_username = serializers.SlugRelatedField(
        source="requester", slug_field="username", read_only=True
    )

    class Meta:
        model = Instance
        fields = (
            "id",
            "workflow_definition_code",
            "current_state_code",
            "requester_username",
            "title",
            "description",
            "status",
            "created_at",
            "updated_at",
        )


class InstanceDetailSerializer(serializers.ModelSerializer):
    workflow_definition = WorkflowDefinitionSerializer(read_only=True)
    current_state_code = serializers.SlugRelatedField(
        source="current_state", slug_field="code", read_only=True, allow_null=True
    )
    requester_username = serializers.SlugRelatedField(
        source="requester", slug_field="username", read_only=True
    )
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = Instance
        fields = (
            "id",
            "workflow_definition",
            "current_state_code",
            "requester_username",
            "title",
            "description",
            "status",
            "task_count",
            "created_at",
            "updated_at",
        )

    def get_task_count(self, obj) -> dict:
        from apps.tasks.models import WorkflowTask

        pending = WorkflowTask.objects.filter(instance=obj, status=WorkflowTask.Status.PENDING).count()
        total = WorkflowTask.objects.filter(instance=obj).count()
        return {"pending": pending, "total": total}


class CreateInstanceSerializer(serializers.Serializer):
    workflow_code = serializers.SlugField()
    title = serializers.CharField(max_length=512)
    description = serializers.CharField(required=False, allow_blank=True, default="")


class TransitionSerializer(serializers.ModelSerializer):
    from_state_code = serializers.SlugRelatedField(
        source="from_state", slug_field="code", read_only=True
    )
    to_state_code = serializers.SlugRelatedField(
        source="to_state", slug_field="code", read_only=True
    )

    class Meta:
        model = Transition
        fields = (
            "id",
            "name",
            "from_state_code",
            "to_state_code",
            "allowed_role_codes",
            "requires_comment",
        )


class ExecuteTransitionSerializer(serializers.Serializer):
    transition_id = serializers.UUIDField()
    comment = serializers.CharField(required=False, allow_blank=True, default="")
    metadata = serializers.JSONField(required=False, default=dict)


class CancelInstanceSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default="")


class ActionLogSerializer(serializers.ModelSerializer):
    from_state_code = serializers.SlugRelatedField(
        source="from_state", slug_field="code", read_only=True, allow_null=True
    )
    to_state_code = serializers.SlugRelatedField(
        source="to_state", slug_field="code", read_only=True, allow_null=True
    )
    actor_username = serializers.SlugRelatedField(
        source="actor", slug_field="username", read_only=True
    )

    class Meta:
        model = ActionLog
        fields = (
            "id",
            "action",
            "actor_username",
            "from_state_code",
            "to_state_code",
            "comment",
            "metadata",
            "created_at",
        )
        read_only_fields = fields
