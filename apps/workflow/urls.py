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
    path("instances/", InstanceListCreateView.as_view(), name="workflow-instance-list"),
    path("instances/<uuid:instance_id>/", InstanceDetailView.as_view(), name="workflow-instance-detail"),
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
    path(
        "instances/<uuid:instance_id>/cancel/",
        CancelInstanceView.as_view(),
        name="workflow-instance-cancel",
    ),
    path(
        "instances/<uuid:instance_id>/logs/",
        ActionLogListView.as_view(),
        name="workflow-instance-logs",
    ),
    path(
        "instances/<uuid:instance_id>/link-entity/",
        LinkEntityView.as_view(),
        name="workflow-instance-link-entity",
    ),
]
