"""Authentication helpers for Pen API."""
from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed


class ExpiringTokenAuthentication(TokenAuthentication):
    """
    DRF's built-in token authentication with optional expiry.

    This keeps authentication dependency-free. Set TOKEN_EXPIRY_DAYS=0 to
    disable expiry. Expired tokens are rejected and deleted.
    """

    keyword = "Token"

    def authenticate_credentials(self, key: str):
        user, token = super().authenticate_credentials(key)
        expiry_days = getattr(settings, "TOKEN_EXPIRY_DAYS", 0)
        if expiry_days and token.created + timedelta(days=expiry_days) <= timezone.now():
            token.delete()
            raise AuthenticationFailed("توکن منقضی شده است.")
        return user, token


def issue_token(user) -> Token:
    """Return the user's stable API token, creating it when needed."""
    token, _ = Token.objects.get_or_create(user=user)
    return token
