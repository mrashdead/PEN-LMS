"""
Education URL configuration — mounted under /api/education/ in pen/urls.py.
"""
from __future__ import annotations

from django.urls import path

from apps.education.timetable_views import TimetableView
from apps.education.views import (
    AttendanceReportView,
    CapacityReportView,
    CourseDetailView,
    CourseListCreateView,
    DepartmentListCreateView,
    LessonDetailView,
    LessonListCreateView,
    LocationListCreateView,
    OfferingDetailView,
    OfferingEnrollView,
    OfferingListCreateView,
    SessionAttendanceListView,
    SessionBulkAttendanceView,
    SessionDetailView,
    SessionListCreateView,
)

urlpatterns = [
    path("departments/", DepartmentListCreateView.as_view(), name="edu-department-list"),
    path("locations/", LocationListCreateView.as_view(), name="edu-location-list"),
    path("lessons/", LessonListCreateView.as_view(), name="edu-lesson-list"),
    path("lessons/<uuid:pk>/", LessonDetailView.as_view(), name="edu-lesson-detail"),
    path("courses/", CourseListCreateView.as_view(), name="edu-course-list"),
    path("courses/<uuid:pk>/", CourseDetailView.as_view(), name="edu-course-detail"),
    path("offerings/", OfferingListCreateView.as_view(), name="edu-offering-list"),
    path("offerings/<uuid:pk>/", OfferingDetailView.as_view(), name="edu-offering-detail"),
    path("offerings/<uuid:pk>/enroll/", OfferingEnrollView.as_view(), name="edu-offering-enroll"),
    path("sessions/", SessionListCreateView.as_view(), name="edu-session-list"),
    path("sessions/<uuid:pk>/", SessionDetailView.as_view(), name="edu-session-detail"),
    path("sessions/<uuid:pk>/attendance/",
         SessionBulkAttendanceView.as_view(), name="edu-session-attendance-post"),
    path("sessions/<uuid:pk>/roster/",
         SessionAttendanceListView.as_view(), name="edu-session-roster"),
    # Reports (§13-7)
    path("reports/attendance/", AttendanceReportView.as_view(), name="edu-report-attendance"),
    path("reports/capacity/", CapacityReportView.as_view(), name="edu-report-capacity"),

    # Daily timetable (read model for the UI grid)
    path("timetable/", TimetableView.as_view(), name="edu-timetable"),
]
