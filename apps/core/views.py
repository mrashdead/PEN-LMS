from __future__ import annotations

import logging

from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetConfirmView,
)
from django.core.exceptions import PermissionDenied
from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.shortcuts import redirect, resolve_url
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.throttling import AnonRateThrottle, ScopedRateThrottle, UserRateThrottle
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView

from apps.core.utils import english_numbers
from apps.core.login_security import blocked, clear_failures, record_failure
from apps.core.authentication import ExpiringTokenAuthentication, revoke_token

logger = logging.getLogger(__name__)


class DashboardTokenObtainView(ObtainAuthToken):
    """Issue API tokens with the configured login throttle."""

    authentication_classes = []
    permission_classes = []
    throttle_classes = [AnonRateThrottle, ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        if getattr(user, "is_deleted", False):
            raise AuthenticationFailed("این حساب غیرفعال است.")
        token, _ = Token.objects.get_or_create(user=user)
        from apps.core.models import AuditEvent

        AuditEvent.record(
            kind=AuditEvent.Kind.LOGIN,
            summary="ورود موفق کاربر از طریق API.",
            actor=user,
            obj=user,
            request=request,
            metadata={"method": request.method, "path": request.path, "auth_method": "api_token"},
        )
        return Response({"token": token.key})


class DashboardTokenRevokeView(APIView):
    """Revoke the authenticated API token so it can no longer be reused."""

    authentication_classes = [ExpiringTokenAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def post(self, request, *args, **kwargs):
        revoke_token(request.user)
        from apps.core.models import AuditEvent

        AuditEvent.record(
            kind=AuditEvent.Kind.FIELD_CHANGE,
            summary="کاربر توکن API حساب خود را باطل کرد.",
            actor=request.user,
            obj=request.user,
            request=request,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


def healthz(request):
    """Process liveness check. Deliberately does not depend on the database."""
    return JsonResponse({"status": "ok"})


def readyz(request):
    """Readiness check that verifies the primary database is reachable."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        logger.exception("readiness check failed: database unavailable")
        return JsonResponse({"status": "not_ready", "database": "unavailable"}, status=503)
    return JsonResponse({"status": "ready", "database": "ok"})


def dashboard_entry(request):
    """Send visitors to the login page and authenticated users to their home."""
    return redirect("dashboard-home" if request.user.is_authenticated else "dashboard-login")


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
            # دانش‌آموزان و معلمان معمولاً کد ملی را به‌عنوان رمز اولیه هم
            # وارد می‌کنند؛ رقم‌های فارسی/عربی رمز را هم مانند نام کاربری
            # به شکل انگلیسی ذخیره‌شده تبدیل کنیم.
            data["password"] = english_numbers(data.get("password", ""))
            kwargs["data"] = data
        return kwargs

    def form_invalid(self, form):
        username = getattr(self, "_login_username", "") or english_numbers(
            self.request.POST.get("username", "")
        ).strip()
        if not getattr(self, "_login_blocked", False) and username and self.request.POST.get("password"):
            record_failure(self.request, username)
        if username:
            from apps.core.models import AuditEvent

            AuditEvent.record(
                kind=AuditEvent.Kind.ACCESS_DENIED,
                summary="تلاش برای ورود به داشبورد ناموفق یا مسدود شد.",
                metadata={"username": username, "path": self.request.path},
                request=self.request,
            )
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

    def form_valid(self, form):
        response = super().form_valid(form)
        revoke_token(self.request.user)
        from apps.core.models import AuditEvent

        AuditEvent.record(
            kind=AuditEvent.Kind.FIELD_CHANGE,
            summary="کاربر رمز عبور حساب خود را تغییر داد.",
            actor=self.request.user,
            obj=self.request.user,
            request=self.request,
        )
        return response


class DashboardPasswordResetConfirmView(PasswordResetConfirmView):
    """Revoke API tokens when a user completes password recovery."""

    def form_valid(self, form):
        response = super().form_valid(form)
        revoke_token(form.user)
        from apps.core.models import AuditEvent

        AuditEvent.record(
            kind=AuditEvent.Kind.FIELD_CHANGE,
            summary="کاربر رمز عبور خود را از طریق بازیابی تغییر داد.",
            actor=form.user,
            obj=form.user,
            request=self.request,
        )
        return response


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
