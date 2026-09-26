"""Page and API share the same configurable permission boundary."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.views.generic import TemplateView
from rest_framework.pagination import CursorPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.reports.permissions import CanAccessCapacityReport, can_access_capacity_report
from apps.reports.selectors.enrollment_capacity import (
    CapacityFilters, report_options, report_query, report_rows, report_summary, row_data,
)
from apps.reports.selectors.reports import ReportFilterError


class CapacityPagination(CursorPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100
    ordering = ("-created_at", "-pk")


class EnrollmentCapacityView(APIView):
    permission_classes = (CanAccessCapacityReport,)

    def get(self, request):
        try:
            filters = CapacityFilters.parse(request.query_params)
            qs, registrations, foreign_key, date_field = report_query(request.user, filters)
            pager = CapacityPagination()
            rows = pager.paginate_queryset(report_rows(qs, filters.source), request, view=self)
            payload = {"results": [row_data(row, filters.source) for row in rows],
                       "next": pager.get_next_link(), "previous": pager.get_previous_link()}
            # Moving between pages does not rerun the overview aggregates.
            if not request.query_params.get("cursor"):
                payload["overview"] = report_summary(qs, registrations, foreign_key, date_field, filters)
            return Response(payload)
        except ReportFilterError as exc:
            return Response({"detail": str(exc)}, status=400)


class EnrollmentCapacityOptionsView(APIView):
    permission_classes = (CanAccessCapacityReport,)

    def get(self, request):
        try:
            return Response(report_options(request.user, request.query_params))
        except ReportFilterError as exc:
            return Response({"detail": str(exc)}, status=400)


class EnrollmentCapacityPage(LoginRequiredMixin, TemplateView):
    template_name = "enrollment_capacity.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not can_access_capacity_report(request.user):
            raise PermissionDenied("دسترسی به گزارش ثبت‌نام و ظرفیت کلاس‌ها مجاز نیست.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["capacity_endpoints"] = {
            "report": reverse("reports-enrollment-capacity"),
            "options": reverse("reports-enrollment-capacity-options"),
        }
        return context
