from __future__ import annotations

from django.contrib import admin

from apps.tasks.models import WorkflowTask


@admin.register(WorkflowTask)
class WorkflowTaskAdmin(admin.ModelAdmin):
    list_display = ("instance", "state", "assignee", "status", "due_date", "completed_at", "created_at")
    list_filter = ("status",)
    search_fields = ("instance__title", "assignee__username")
    autocomplete_fields = ("instance", "state", "assignee", "assigned_by")
    readonly_fields = ("created_at", "updated_at")
