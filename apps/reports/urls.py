"""Reports API routes — mounted under /api/reports/."""
from django.urls import path

from apps.reports.views.export import ReportsExportView
from apps.reports.views.reports import ReportsDashboardView, ReportsFilterOptionsView
from apps.reports.views.enrollment_capacity import EnrollmentCapacityView, EnrollmentCapacityOptionsView


urlpatterns = [
    path("enrollment-capacity/", EnrollmentCapacityView.as_view(), name="reports-enrollment-capacity"),
    path("enrollment-capacity/options/", EnrollmentCapacityOptionsView.as_view(), name="reports-enrollment-capacity-options"),
    path("dashboard/", ReportsDashboardView.as_view(), name="reports-dashboard"),
    path("filters/", ReportsFilterOptionsView.as_view(), name="reports-filters"),
    path("export/", ReportsExportView.as_view(), name="reports-export"),
]
