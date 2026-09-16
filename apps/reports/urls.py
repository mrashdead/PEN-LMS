"""Reports API routes — mounted under /api/reports/."""
from django.urls import path

from apps.reports.views.export import ReportsExportView
from apps.reports.views.reports import ReportsDashboardView, ReportsFilterOptionsView


urlpatterns = [
    path("dashboard/", ReportsDashboardView.as_view(), name="reports-dashboard"),
    path("filters/", ReportsFilterOptionsView.as_view(), name="reports-filters"),
    path("export/", ReportsExportView.as_view(), name="reports-export"),
]
