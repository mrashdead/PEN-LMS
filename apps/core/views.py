from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import TemplateView


class DashboardLoginView(LoginView):
    template_name = "dashboard/login.html"
    redirect_authenticated_user = True
    next_page = "dashboard-home"


class DashboardLogoutView(LogoutView):
    next_page = "dashboard-login"


class DashboardHomeView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/base.html"
