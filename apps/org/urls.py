"""Organizational URL configuration — mounted under /api/org/ in pen/urls.py."""
from __future__ import annotations

from django.urls import path

from apps.org.views import (
    AccessSimulatorView,
    AclBulkView,
    AclCatalogView,
    AclDirectoryView,
    AclGrantView,
    AclRevokeView,
    AclUserView,
    DelegationListCreateView,
    DelegationRevokeView,
    OrgChartView,
    OrgProfileView,
    PermissionDirectoryView,
    PermissionGroupsView,
    PermissionMatrixView,
    PermissionOptionsView,
    PermissionRolesView,
    PermissionUserView,
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
    # Person ACL (manual explicit per-user grants)
    path("acl/catalog/", AclCatalogView.as_view(), name="org-acl-catalog"),
    path("acl/directory/", AclDirectoryView.as_view(), name="org-acl-directory"),
    path("acl/user/<uuid:pk>/", AclUserView.as_view(), name="org-acl-user"),
    path("acl/user/<uuid:pk>/grant/", AclGrantView.as_view(), name="org-acl-grant"),
    path("acl/user/<uuid:pk>/revoke/", AclRevokeView.as_view(), name="org-acl-revoke"),
    path("acl/user/<uuid:pk>/bulk/", AclBulkView.as_view(), name="org-acl-bulk"),
    # Permission management (roles + groups + effective model perms)
    path("perm/directory/", PermissionDirectoryView.as_view(), name="org-perm-directory"),
    path("perm/options/", PermissionOptionsView.as_view(), name="org-perm-options"),
    path("perm/user/<uuid:pk>/", PermissionUserView.as_view(), name="org-perm-user"),
    path("perm/user/<uuid:pk>/roles/", PermissionRolesView.as_view(), name="org-perm-roles"),
    path("perm/user/<uuid:pk>/groups/", PermissionGroupsView.as_view(), name="org-perm-groups"),
]
