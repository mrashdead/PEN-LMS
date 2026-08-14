from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.models import DomainModel


class WorkflowTask(DomainModel):
    """
    یک تسک عملیاتی که در یک Instance به یک کاربر مشخص ارجاع داده می‌شود.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        SKIPPED = "skipped", "Skipped"

    instance = models.ForeignKey(
        "workflow.Instance",
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    state = models.ForeignKey(
        "workflow.State",
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workflow_tasks",
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
    )
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    due_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "tasks"
        db_table = "tasks_workflow_task"
        verbose_name = "Workflow Task"
        verbose_name_plural = "Workflow Tasks"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["assignee", "status"]),
            models.Index(fields=["instance", "status"]),
            models.Index(fields=["state"]),
        ]

    def __str__(self) -> str:
        return f"Task {self.instance_id} → {self.assignee_id} [{self.status}]"
