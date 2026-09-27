"""Thin HTTP adapters for the reports read model."""
from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.reports.permissions import (
    CanAccessReports,
    can_access_reports,
    can_view_financial_reports,
)
from apps.reports.selectors.reports import (
    ReportFilterError,
    ReportFilters,
    dashboard_data,
    filter_options,
)


class ReportsDashboardView(APIView):
    """GET /api/reports/dashboard/ — one filtered dashboard read model."""

    permission_classes = (IsAuthenticated, CanAccessReports)

    def get(self, request):
        try:
            filters = ReportFilters.from_query(request.query_params)
            return Response(dashboard_data(request.user, filters))
        except ReportFilterError as exc:
            return Response({"detail": str(exc)}, status=400)


class ReportsFilterOptionsView(APIView):
    """GET /api/reports/filters/ — safe, non-PII filter option lists."""

    permission_classes = (IsAuthenticated, CanAccessReports)

    def get(self, request):
        return Response(filter_options())


class ReportsPageAccessMixin(LoginRequiredMixin):
    """Presentation gate mirroring the API's report permission."""

    login_url = "dashboard-login"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (
            not request.user.is_active
            or getattr(request.user, "is_deleted", False)
            or not can_access_reports(request.user)
        ):
            raise PermissionDenied("فقط مدیریت یا سرپرست مجاز به مشاهدهٔ مرکز گزارش‌هاست.")
        return super().dispatch(request, *args, **kwargs)


class ReportsPage(ReportsPageAccessMixin, TemplateView):
    """Reports & Analytics Dashboard page."""

    template_name = "reports.html"

    report_page = "overview"

    def dispatch(self, request, *args, **kwargs):
        self.report_page = kwargs.get("section", "overview")
        if self.report_page not in {
            "overview", "financial", "enrollments", "people", "classes",
            "workflow", "communications",
        }:
            from django.http import Http404
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["report_options"] = filter_options()
        context["report_page"] = self.report_page
        pages = [
            ("overview", "نمای کلی", "گزارش‌های کلیدی و دسترسی سریع"),
            ("financial", "مالی", "درآمد و وضعیت وصول"),
            ("enrollments", "ثبت‌نام و دوره‌ها", "وضعیت دوره‌ها و برگزاری‌ها"),
            ("people", "افراد و مدرسان", "ترکیب افراد و بار تدریس"),
            ("classes", "کلاس و حضور", "جلسات، فضاها و حضور و غیاب"),
            ("workflow", "درخواست‌ها", "زمان پاسخ و درخواست‌های در جریان"),
            ("communications", "ارتباطات", "پیام‌ها و اعلان‌ها"),
        ]
        context["report_pages"] = [
            {"key": key, "title": title, "description": description,
             "url": "/workspace/reports/" if key == "overview" else f"/workspace/reports/{key}/",
             "active": key == self.report_page}
            for key, title, description in pages
            if key != "financial" or can_view_financial_reports(self.request.user)
        ]
        context["report_page_title"] = next(
            (page[1] for page in pages if page[0] == self.report_page), "گزارش‌ها"
        )
        context["can_view_financial_reports"] = can_view_financial_reports(self.request.user)
        from apps.reports.permissions import can_access_capacity_report
        context["can_capacity_report"] = can_access_capacity_report(self.request.user)
        context["report_endpoints"] = {
            "dashboard": "/api/reports/dashboard/",
            "filters": "/api/reports/filters/",
            "export": "/api/reports/export/",
            "workflow_requests": "/api/workflow/reports/",
        }
        return context
