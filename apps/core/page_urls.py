"""Dashboard workspace page routes (session auth) — mounted under /workspace/."""
from __future__ import annotations

from django.urls import path

from apps.core.pages import (
    MessagesPage,
    OrgChartPage,
    OrgDelegationsPage,
    OrgPermissionsPage,
    OrgResponsibilitiesPage,
    RequestsPage,
    ReportsPage,
    ResourcePage,
    TimetablePage,
    WorkQueuePage,
)

urlpatterns = [
    path("work/", WorkQueuePage.as_view(), name="workspace-work"),
    path("requests/", RequestsPage.as_view(), name="workspace-requests"),
    path("org/chart/", OrgChartPage.as_view(), name="workspace-org-chart"),
    path("org/permissions/", OrgPermissionsPage.as_view(), name="workspace-org-permissions"),
    path("org/responsibilities/", OrgResponsibilitiesPage.as_view(), name="workspace-org-responsibilities"),
    path("org/delegations/", OrgDelegationsPage.as_view(), name="workspace-org-delegations"),
    path("persons/", ResourcePage.as_view(), {"resource": "persons"}, name="workspace-persons"),
    path("lessons/", ResourcePage.as_view(), {"resource": "lessons"}, name="workspace-lessons"),
    path("courses/", ResourcePage.as_view(), {"resource": "courses"}, name="workspace-courses"),
    path("offerings/", ResourcePage.as_view(), {"resource": "offerings"}, name="workspace-offerings"),
    path("sessions/", ResourcePage.as_view(), {"resource": "sessions"}, name="workspace-sessions"),
    path("locations/", ResourcePage.as_view(), {"resource": "locations"}, name="workspace-locations"),
    path("timetable/", TimetablePage.as_view(), name="workspace-timetable"),
    path("messages/", MessagesPage.as_view(), name="workspace-messages"),
    path("reports/", ReportsPage.as_view(), name="workspace-reports"),
]
