"""Organizational URL configuration — mounted under /api/org/ in pen/urls.py."""
from __future__ import annotations

from django.urls import path

from apps.org.views import (
    AccessSimulatorView,
    DelegationListCreateView,
    DelegationRevokeView,
    OrgChartView,
    OrgProfileView,
    PermissionMatrixView,
    ResponsibilitiesView,
    UnitPerformanceView,
)

urlpatterns = [
    path("chart/", OrgChartView.as_view(), name="org-chart"),
    path("profile/<uuid:pk>/", OrgProfileView.as_view(), name="org-profile"),
    path("permissions/matrix/", PermissionMatrixView.as_view(), name="org-matrix"),
    path("permissions/simulate/", AccessSimulatorView.as_view(), name="org-simulate"),
    path("responsibilities/", ResponsibilitiesView.as_view(), name="org-responsibilities"),
    path("performance/units/", UnitPerformanceView.as_view(), name="org-performance"),
    path("delegations/", DelegationListCreateView.as_view(), name="org-delegations"),
    path("delegations/<uuid:pk>/revoke/", DelegationRevokeView.as_view(), name="org-delegation-revoke"),
]
