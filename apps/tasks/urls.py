from __future__ import annotations

from django.urls import path

from apps.tasks.views import WorkflowTaskDetailView, WorkflowTaskListView

urlpatterns = [
    path("", WorkflowTaskListView.as_view(), name="task-list"),
    path("<uuid:pk>/", WorkflowTaskDetailView.as_view(), name="task-detail"),
]
