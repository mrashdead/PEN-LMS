"""Dashboard workspace page routes (session auth) — mounted under /workspace/."""
from __future__ import annotations

from django.urls import path

from apps.core.pages import (
    EnrollmentEntityPage,
    EnrollmentPage,
    EnrollmentRecordPage,
    LearnerPortalPage,
    MessagesPage,
    OrgChartPage,
    OrgDelegationsPage,
    OrgPermissionsPage,
    OrgResponsibilitiesPage,
    PermissionManagePage,
    PasswordManagementPage,
    ProfilePage,
    RequestsPage,
    ResourcePage,
    TeacherAttendancePage,
    TeacherDashboardPage,
    TeacherReportCardPage,
    TimetablePage,
    WorkQueuePage,
)
from apps.persons.page_views import PersonCreatePageView, PersonsPage
from apps.reports.views.reports import ReportsPage
from apps.reports.views.enrollment_capacity import EnrollmentCapacityPage

urlpatterns = [
    path("profile/", ProfilePage.as_view(), name="workspace-profile"),
    path("password-management/", PasswordManagementPage.as_view(), name="workspace-password-management"),
    path("work/", WorkQueuePage.as_view(), name="workspace-work"),
    path("requests/", RequestsPage.as_view(), name="workspace-requests"),
    path("enrollments/", EnrollmentPage.as_view(), name="workspace-enrollments"),
    path("enrollments/records/<str:source>/<uuid:pk>/", EnrollmentRecordPage.as_view(), name="workspace-enrollment-record"),
    path("enrollments/<str:kind>/<uuid:pk>/", EnrollmentEntityPage.as_view(), name="workspace-enrollment-entity"),
    path("org/chart/", OrgChartPage.as_view(), name="workspace-org-chart"),
    path("org/permissions/", OrgPermissionsPage.as_view(), name="workspace-org-permissions"),
    path("org/responsibilities/", OrgResponsibilitiesPage.as_view(), name="workspace-org-responsibilities"),
    path("org/delegations/", OrgDelegationsPage.as_view(), name="workspace-org-delegations"),
    path("org/permissions/manage/", PermissionManagePage.as_view(), name="workspace-perm-manage"),
    path("persons/create/", PersonCreatePageView.as_view(), name="workspace-person-create"),
    path("persons/", PersonsPage.as_view(), name="workspace-persons"),
    path("departments/", ResourcePage.as_view(), {"resource": "departments"}, name="workspace-departments"),
    path("lessons/", ResourcePage.as_view(), {"resource": "lessons"}, name="workspace-lessons"),
    path("courses/", ResourcePage.as_view(), {"resource": "courses"}, name="workspace-courses"),
    path("offerings/", ResourcePage.as_view(), {"resource": "offerings"}, name="workspace-offerings"),
    path("sessions/", ResourcePage.as_view(), {"resource": "sessions"}, name="workspace-sessions"),
    path("locations/", ResourcePage.as_view(), {"resource": "locations"}, name="workspace-locations"),
    path("timetable/", TimetablePage.as_view(), name="workspace-timetable"),
    path("messages/", MessagesPage.as_view(), name="workspace-messages"),
    path("reports/", ReportsPage.as_view(), name="workspace-reports"),
    path("reports/enrollment-capacity/", EnrollmentCapacityPage.as_view(), name="workspace-enrollment-capacity"),
    # Teacher portal
    path("teacher/", TeacherDashboardPage.as_view(), name="workspace-teacher"),
    path("teacher/attendance/", TeacherAttendancePage.as_view(), name="workspace-teacher-attendance"),
    path("teacher/report-cards/", TeacherReportCardPage.as_view(), name="workspace-teacher-report-cards"),
    # Learner (student/parent) portal
    path("portal/", LearnerPortalPage.as_view(), name="workspace-learner-portal"),
]
