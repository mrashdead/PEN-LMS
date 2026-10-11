from __future__ import annotations

from django.core.cache import cache
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from apps.accounts.forms import AdminPasswordResetForm
from apps.core.models import AuditEvent
from apps.forms.tests.factories import UserFactory


class AuthenticationSecurityTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = UserFactory(username="auth-security-user")
        self.client = APIClient()

    def tearDown(self):
        cache.clear()

    def test_token_issue_endpoint_enforces_login_rate_limit(self):
        for _ in range(5):
            response = self.client.post(
                "/api/auth/token/",
                {"username": self.user.username, "password": "pass-12345"},
                format="json",
            )
            self.assertEqual(response.status_code, 200)

        response = self.client.post(
            "/api/auth/token/",
            {"username": self.user.username, "password": "pass-12345"},
            format="json",
        )
        self.assertEqual(response.status_code, 429)

    def test_failed_dashboard_login_is_recorded_as_access_denied(self):
        response = self.client.post(
            "/dashboard/login/",
            {"username": self.user.username, "password": "incorrect-password"},
        )

        self.assertEqual(response.status_code, 200)
        event = AuditEvent.objects.get(kind=AuditEvent.Kind.ACCESS_DENIED)
        self.assertEqual(event.metadata["username"], self.user.username)

    def test_successful_dashboard_login_is_recorded(self):
        response = self.client.post(
            "/dashboard/login/",
            {"username": self.user.username, "password": "pass-12345"},
        )

        self.assertEqual(response.status_code, 302)
        event = AuditEvent.objects.get(kind=AuditEvent.Kind.LOGIN, actor=self.user)
        self.assertEqual(event.metadata["path"], "/dashboard/login/")

    def test_successful_dashboard_logout_is_recorded(self):
        self.client.force_login(self.user)

        response = self.client.post("/dashboard/logout/")

        self.assertEqual(response.status_code, 302)
        event = AuditEvent.objects.get(kind=AuditEvent.Kind.LOGOUT, actor=self.user)
        self.assertEqual(event.metadata["path"], "/dashboard/logout/")

    def test_successful_api_token_login_is_recorded(self):
        response = self.client.post(
            "/api/auth/token/",
            {"username": self.user.username, "password": "pass-12345"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        event = AuditEvent.objects.get(kind=AuditEvent.Kind.LOGIN, actor=self.user)
        self.assertEqual(event.metadata["auth_method"], "api_token")

    def test_soft_deleted_user_cannot_obtain_an_api_token(self):
        self.user.is_deleted = True
        self.user.save(update_fields=["is_deleted", "updated_at"])

        response = self.client.post(
            "/api/auth/token/",
            {"username": self.user.username, "password": "pass-12345"},
            format="json",
        )

        self.assertEqual(response.status_code, 401)
        self.assertTrue(
            AuditEvent.objects.filter(kind=AuditEvent.Kind.ACCESS_DENIED).exists()
        )

    def test_admin_password_reset_revokes_existing_api_token(self):
        old_token = Token.objects.get(user=self.user)
        form = AdminPasswordResetForm(
            data={
                "target_user": str(self.user.pk),
                "new_password1": "N3w-Long-Enough-Password!42",
                "new_password2": "N3w-Long-Enough-Password!42",
            },
            user_queryset=type(self.user).objects.filter(pk=self.user.pk),
        )

        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        self.assertFalse(Token.objects.filter(pk=old_token.pk).exists())
        self.assertTrue(self.user.check_password("N3w-Long-Enough-Password!42"))

    def test_authenticated_api_client_can_revoke_its_token(self):
        token = Token.objects.get(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        response = self.client.post("/api/auth/token/revoke/")

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Token.objects.filter(pk=token.pk).exists())
        response = self.client.post("/api/auth/token/revoke/")
        self.assertEqual(response.status_code, 401)
