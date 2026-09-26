"""Staff operations API routes — mounted under /api/staff/."""
from django.urls import path

from apps.staff.views import (
    LeaveRequestCancelView,
    LeaveRequestDetailView,
    LeaveRequestListCreateView,
    LeaveRequestReviewView,
    LeaveTypeListView,
    ReviewHistoryView,
    StaffClockView,
    StaffReportView,
    TimesheetDetailView,
    TimesheetListCreateView,
    TimesheetReviewView,
    WorkReportDetailView,
    WorkReportListCreateView,
    WorkReportReviewView,
)

urlpatterns = [
    # Clock in/out + today status
    path("timesheet/<str:action>/", StaffClockView.as_view(), name="staff-clock"),
    # Timesheets
    path("timesheets/", TimesheetListCreateView.as_view(), name="staff-timesheet-list"),
    path("timesheets/<uuid:pk>/", TimesheetDetailView.as_view(), name="staff-timesheet-detail"),
    path("timesheets/<uuid:pk>/review/", TimesheetReviewView.as_view(), name="staff-timesheet-review"),
    # Leave catalog + requests
    path("leave-types/", LeaveTypeListView.as_view(), name="staff-leave-type-list"),
    path("leave-requests/", LeaveRequestListCreateView.as_view(), name="staff-leave-list"),
    path("leave-requests/<uuid:pk>/", LeaveRequestDetailView.as_view(), name="staff-leave-detail"),
    path("leave-requests/<uuid:pk>/review/", LeaveRequestReviewView.as_view(), name="staff-leave-review"),
    path("leave-requests/<uuid:pk>/cancel/", LeaveRequestCancelView.as_view(), name="staff-leave-cancel"),
    # Work reports
    path("work-reports/", WorkReportListCreateView.as_view(), name="staff-work-report-list"),
    path("work-reports/<uuid:pk>/", WorkReportDetailView.as_view(), name="staff-work-report-detail"),
    path("work-reports/<uuid:pk>/review/", WorkReportReviewView.as_view(), name="staff-work-report-review"),
    # Append-only review history
    path("history/<str:record_type>/<uuid:record_id>/", ReviewHistoryView.as_view(), name="staff-review-history"),
    # Management dashboard
    path("reports/", StaffReportView.as_view(), name="staff-report-dashboard"),
]
