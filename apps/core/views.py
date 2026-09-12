from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, resolve_url
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from apps.core.utils import english_numbers


class DashboardLoginView(LoginView):
    """ورود با نام کاربری/رمز عبور؛ اعداد فارسی و انگلیسی هر دو پذیرفته می‌شوند."""

    template_name = "dashboard/login.html"
    redirect_authenticated_user = True
    next_page = "dashboard-home"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        data = kwargs.get("data")
        if data is not None:
            data = data.copy()
            data["username"] = english_numbers(data.get("username", "")).strip()
            kwargs["data"] = data
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.GET.get("logged_out") == "1":
            messages.success(
                self.request,
                "با موفقیت از سامانه خارج شدید. برای ورود دوباره اطلاعات خود را وارد کنید.",
            )
        return ctx


class DashboardLogoutView(LogoutView):
    """فقط POST؛ پاک‌سازی کامل session و انتقال امن به صفحه login."""

    template_name = "dashboard/logout.html"
    next_page = reverse_lazy("dashboard-login")

    def post(self, request, *args, **kwargs):
        auth_logout(request)
        url = resolve_url(self.next_page)
        return redirect(f"{url}?logged_out=1")


class DashboardHomeView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"
