"""
Workflow URL Configuration — مسیرهای API گردش کار

تمامی مسیرها با /api/workflow/ شروع می‌شوند (تعریف شده در pen/urls.py).
"""
from __future__ import annotations

from django.urls import path

from apps.workflow.views import (
    ActionLogListView,
    ApprovalListView,
    ApproveInstanceView,
    AvailableTransitionsView,
    CancelInstanceView,
    CompleteInstanceView,
    DelegateTaskView,
    ExecuteTransitionView,
    InstanceDetailView,
    InstanceListCreateView,
    LinkEntityView,
    RejectInstanceView,
    ReturnInstanceView,
    SendCopyView,
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

    # ── Semantic actions (B6) — named service paths over the engine ──
    path(
        "instances/<uuid:instance_id>/approve/",
        ApproveInstanceView.as_view(),
        name="workflow-instance-approve",
    ),
    path(
        "instances/<uuid:instance_id>/reject/",
        RejectInstanceView.as_view(),
        name="workflow-instance-reject",
    ),
    path(
        "instances/<uuid:instance_id>/return/",
        ReturnInstanceView.as_view(),
        name="workflow-instance-return",
    ),
    path(
        "instances/<uuid:instance_id>/complete/",
        CompleteInstanceView.as_view(),
        name="workflow-instance-complete",
    ),
    path(
        "instances/<uuid:instance_id>/copies/",
        SendCopyView.as_view(),
        name="workflow-instance-copies",
    ),
    path(
        "instances/<uuid:instance_id>/delegate/",
        DelegateTaskView.as_view(),
        name="workflow-instance-delegate",
    ),
    path(
        "instances/<uuid:instance_id>/approvals/",
        ApprovalListView.as_view(),
        name="workflow-instance-approvals",
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
