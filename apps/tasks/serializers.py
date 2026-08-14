from __future__ import annotations

from rest_framework import serializers

from apps.tasks.models import WorkflowTask


class WorkflowTaskListSerializer(serializers.ModelSerializer):
    instance_title = serializers.CharField(source="instance.title", read_only=True)
    instance_id = serializers.UUIDField(read_only=True)
    state_code = serializers.SlugRelatedField(
        source="state", slug_field="code", read_only=True
    )
    workflow_definition_code = serializers.SlugRelatedField(
        source="instance.workflow_definition", slug_field="code", read_only=True
    )

    class Meta:
        model = WorkflowTask
        fields = (
            "id",
            "instance_id",
            "instance_title",
            "workflow_definition_code",
            "state_code",
            "status",
            "due_date",
            "completed_at",
            "created_at",
        )


class WorkflowTaskDetailSerializer(serializers.ModelSerializer):
    instance_title = serializers.CharField(source="instance.title", read_only=True)
    instance_description = serializers.CharField(source="instance.description", read_only=True)
    instance_status = serializers.CharField(source="instance.status", read_only=True)
    state_code = serializers.SlugRelatedField(
        source="state", slug_field="code", read_only=True
    )
    assignee_username = serializers.SlugRelatedField(
        source="assignee", slug_field="username", read_only=True
    )
    assigned_by_username = serializers.SlugRelatedField(
        source="assigned_by", slug_field="username", read_only=True, allow_null=True
    )
    workflow_definition_code = serializers.SlugRelatedField(
        source="instance.workflow_definition", slug_field="code", read_only=True
    )

    class Meta:
        model = WorkflowTask
        fields = (
            "id",
            "instance_id",
            "instance_title",
            "instance_description",
            "instance_status",
            "workflow_definition_code",
            "state_code",
            "assignee_username",
            "assigned_by_username",
            "status",
            "due_date",
            "completed_at",
            "created_at",
            "updated_at",
        )
