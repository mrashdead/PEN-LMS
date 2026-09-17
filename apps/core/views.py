from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, resolve_url
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from apps.core.utils import english_numbers
from apps.core.login_security import blocked, clear_failures, record_failure


SELF_PASSWORD_ROLES = {"manager", "workflow_admin", "supervisor", "employee"}


class DashboardLoginView(LoginView):
    """ورود با نام کاربری/رمز عبور؛ اعداد فارسی و انگلیسی هر دو پذیرفته می‌شوند."""

    template_name = "dashboard/login.html"
    redirect_authenticated_user = True
    next_page = "dashboard-home"

    def post(self, request, *args, **kwargs):
        username = english_numbers(request.POST.get("username", "")).strip()
        reason = blocked(request, username)
        if reason:
            self._login_blocked = True
            form = self.get_form()
            form.add_error(None, reason)
            return self.form_invalid(form)
        self._login_username = username
        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        data = kwargs.get("data")
        if data is not None:
            data = data.copy()
            data["username"] = english_numbers(data.get("username", "")).strip()
            kwargs["data"] = data
        return kwargs

    def form_invalid(self, form):
        username = getattr(self, "_login_username", "") or english_numbers(
            self.request.POST.get("username", "")
        ).strip()
        if not getattr(self, "_login_blocked", False) and username and self.request.POST.get("password"):
            record_failure(self.request, username)
        return super().form_invalid(form)

    def form_valid(self, form):
        username = getattr(self, "_login_username", "") or english_numbers(
            self.request.POST.get("username", "")
        ).strip()
        clear_failures(self.request, username)
        return super().form_valid(form)

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


class DashboardPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    """Self-service password change for staff accounts only."""

    template_name = "registration/password_change_form.html"
    success_url = reverse_lazy("password-change-done")

    def dispatch(self, request, *args, **kwargs):
        roles = set(request.user.role_codes()) if request.user.is_authenticated else set()
        if not (roles & SELF_PASSWORD_ROLES):
            raise PermissionDenied(
                "تغییر رمز عبور این نوع حساب فقط توسط مدیریت سامانه انجام می‌شود."
            )
        return super().dispatch(request, *args, **kwargs)


class DashboardHomeView(LoginRequiredMixin, TemplateView):
    """Admin/staff dashboard shell.

    A pure teacher (holds ``teacher`` and no management/employee role) is
    redirected to their dedicated portal instead — the stat cards here count
    persons/instances/tasks a teacher must not see even in aggregate, so the
    generic dashboard is not part of the teacher surface (task spec §1).
    """

    template_name = "dashboard/home.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_superuser:
            from apps.core.pages import _TEACHER_BLOCKED_ROLES

            roles = (
                set(request.user.role_codes())
                if hasattr(request.user, "role_codes") else set()
            )
            if "teacher" in roles and not (roles & _TEACHER_BLOCKED_ROLES):
                return redirect("workspace-teacher")
            if roles & {"student", "guardian"}:
                return redirect("workspace-learner-portal")
        return super().dispatch(request, *args, **kwargs)
