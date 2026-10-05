"""
Server-rendered operator page for the playhouse (dashboard-style, session auth).

The page is thin: it renders the shell and seeds today's rows; live timer
ticking and form submission go through the playhouse API. Authorization stays
on the API side — the page just gates visibility for staff.
"""
from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.utils import timezone
from django.views.generic import TemplateView

from apps.core.utils import jalali_date_str
from apps.playhouse import selectors
from apps.playhouse.permissions import FINANCE_ROLES, OPERATOR_ROLES


class PlayhousePageMixin(LoginRequiredMixin):
    """Require a staff operator role (mirrors the API permission)."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        roles = set(request.user.role_codes()) if hasattr(request.user, "role_codes") else set()
        if not roles & OPERATOR_ROLES:
            raise Http404
        return super().dispatch(request, *args, **kwargs)


class PlayhouseDashboardPage(PlayhousePageMixin, TemplateView):
    """The operator front-desk: intake form + live session list with timers."""

    template_name = "playhouse/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sessions"] = selectors.sessions_today()
        context["today"] = timezone.localdate()
        # Keep ASCII digits in the input: jalalidatepicker parses the numeric
        # value itself, while the calendar labels remain Persian.
        context["today_jalali"] = jalali_date_str(context["today"])
        return context


class PlayhouseAttendancePage(PlayhousePageMixin, TemplateView):
    """Searchable daily register and recovery tools for incomplete visits."""
    template_name = "playhouse/attendance.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["today"] = timezone.localdate().isoformat()
        context["today_jalali"] = jalali_date_str(timezone.localdate())
        return context


class PlayhouseFinancePage(LoginRequiredMixin, TemplateView):
    """Finance-only view over paid playhouse invoices."""

    template_name = "playhouse/finance.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        roles = set(request.user.role_codes()) if hasattr(request.user, "role_codes") else set()
        if not request.user.is_active or not roles & FINANCE_ROLES:
            raise Http404
        return super().dispatch(request, *args, **kwargs)


class PlayhouseSettingsPage(LoginRequiredMixin, TemplateView):
    """Manager-only page: 15-minute price + working hours."""

    template_name = "playhouse/settings.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        roles = set(request.user.role_codes()) if hasattr(request.user, "role_codes") else set()
        if not request.user.is_active or not roles & FINANCE_ROLES:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        from apps.playhouse.models import PlayhouseConfig

        context = super().get_context_data(**kwargs)
        context["config"] = PlayhouseConfig.get_solo()
        return context
