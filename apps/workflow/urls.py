"""
Workflow URL Configuration — مسیرهای API گردش کار

تمامی مسیرها با /api/workflow/ شروع می‌شوند (تعریف شده در pen/urls.py).
"""
from __future__ import annotations

from django.urls import path

from apps.workflow.views import (
    ActionLogListView,
    AvailableTransitionsView,
    CancelInstanceView,
    ExecuteTransitionView,
    InstanceDetailView,
    InstanceListCreateView,
    LinkEntityView,
)

urlpatterns = [
    # ── Instance ─────────────────────────────────────────────
    path("instances/", InstanceListCreateView.as_view(), name="workflow-instance-list"),
    path(
        "instances/<uuid:instance_id>/",
        InstanceDetailView.as_view(),
        name="workflow-instance-detail",
    ),

    # ── Transitions ──────────────────────────────────────────
    path(
        "instances/<uuid:instance_id>/available-transitions/",
        AvailableTransitionsView.as_view(),
        name="workflow-instance-transitions",
    ),
    path(
        "instances/<uuid:instance_id>/execute-transition/",
        ExecuteTransitionView.as_view(),
        name="workflow-instance-execute",
    ),

    # ── Cancel ───────────────────────────────────────────────
    path(
        "instances/<uuid:instance_id>/cancel/",
        CancelInstanceView.as_view(),
        name="workflow-instance-cancel",
    ),

    # ── Logs ─────────────────────────────────────────────────
    path(
        "instances/<uuid:instance_id>/logs/",
        ActionLogListView.as_view(),
        name="workflow-instance-logs",
    ),

    # ── Entity Link ──────────────────────────────────────────
    path(
        "instances/<uuid:instance_id>/link-entity/",
        LinkEntityView.as_view(),
        name="workflow-instance-link-entity",
    ),
]