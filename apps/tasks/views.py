from __future__ import annotations

from rest_framework import generics, permissions

from apps.tasks.models import WorkflowTask
from apps.tasks.serializers import (
    WorkflowTaskDetailSerializer,
    WorkflowTaskListSerializer,
)


class WorkflowTaskListView(generics.ListAPIView):
    """
    GET /api/tasks/ — list tasks for the current user (inbox)
    """

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = WorkflowTaskListSerializer

    def get_queryset(self):
        user = self.request.user
        qs = WorkflowTask.objects.filter(assignee=user).select_related(
            "instance", "instance__workflow_definition", "state"
        )

        # Optional filters
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)

        wf_param = self.request.query_params.get("workflow")
        if wf_param:
            qs = qs.filter(instance__workflow_definition__code=wf_param)

        return qs.order_by("-created_at")


class WorkflowTaskDetailView(generics.RetrieveAPIView):
    """
    GET /api/tasks/{id}/ — detail of a task
    """

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = WorkflowTaskDetailSerializer

    def get_queryset(self):
        user = self.request.user
        return WorkflowTask.objects.filter(assignee=user).select_related(
            "instance", "instance__workflow_definition", "state", "assignee", "assigned_by"
        )
