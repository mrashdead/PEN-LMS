from __future__ import annotations

from django.db import models
from django.utils import timezone
from rest_framework import generics

from apps.core.group_permissions import StrictDjangoModelPermissions
from apps.core.permissions import IsActiveUser
from apps.tasks.models import WorkflowTask
from apps.tasks.serializers import (
    WorkflowTaskDetailSerializer,
    WorkflowTaskListSerializer,
)


class WorkflowTaskListView(generics.ListAPIView):
    """GET /api/tasks/ — current user's inbox only.

    Filters: ?status=pending  ?workflow=<code>  ?overdue=true|false
             ?instance=<uuid>   (tasks of one workflow instance)
    Ordering: ?ordering=due_date|-due_date|created_at (safe allowlist).
    """

    permission_classes = (IsActiveUser, StrictDjangoModelPermissions)
    serializer_class = WorkflowTaskListSerializer
    # Allowlist — never pass client input straight to .order_by().
    ORDERING_ALLOWED = {"due_date", "-due_date", "created_at", "-created_at"}

    def get_queryset(self):
        user = self.request.user
        qs = WorkflowTask.objects.filter(assignee=user).select_related(
            "instance", "instance__workflow_definition", "state"
        )
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        instance_param = self.request.query_params.get("instance")
        if instance_param:
            qs = qs.filter(instance_id=instance_param)
        wf_param = self.request.query_params.get("workflow")
        if wf_param:
            qs = qs.filter(instance__workflow_definition__code=wf_param)
        overdue = self.request.query_params.get("overdue")
        if overdue is not None:
            now = timezone.now()
            is_overdue = overdue.lower() in ("1", "true")
            overdue_qs = models.Q(
                status=WorkflowTask.Status.PENDING,
                due_date__isnull=False,
                due_date__lt=now,
            )
            qs = qs.filter(overdue_qs) if is_overdue else qs.exclude(overdue_qs)
        ordering = self.request.query_params.get("ordering")
        if ordering in self.ORDERING_ALLOWED:
            qs = qs.order_by(ordering)
        else:
            qs = qs.order_by("-created_at")
        return qs


class WorkflowTaskDetailView(generics.RetrieveAPIView):
    """GET /api/tasks/{id}/ — current user's task only."""

    permission_classes = (IsActiveUser, StrictDjangoModelPermissions)
    serializer_class = WorkflowTaskDetailSerializer

    def get_queryset(self):
        user = self.request.user
        return WorkflowTask.objects.filter(assignee=user).select_related(
            "instance", "instance__workflow_definition", "state", "assignee", "assigned_by"
        )
