# apps/accounts/managers.py
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from django.contrib.auth.base_user import BaseUserManager
from django.db import models
from django.utils import timezone

if TYPE_CHECKING:
    from apps.accounts.models import User


class UserManager(BaseUserManager["User"]):
    """Thread-safe-ish creation; always use on DB alias explicitly in services."""

    use_in_migrations = True

    def _create_user(
        self,
        username: str,
        email: Optional[str],
        password: Optional[str],
        **extra_fields: Any,
    ) -> User:
        if not username:
            raise ValueError("username is required")
        email = self.normalize_email(email) if email else None
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(
        self,
        username: str,
        email: Optional[str] = None,
        password: Optional[str] = None,
        **extra_fields: Any,
    ) -> User:
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", True)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(
        self,
        username: str,
        email: Optional[str] = None,
        password: Optional[str] = None,
        **extra_fields: Any,
    ) -> User:
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(username, email, password, **extra_fields)

    def active(self) -> models.QuerySet[User]:
        return self.get_queryset().filter(is_active=True, is_deleted=False)


class RoleQuerySet(models.QuerySet):
    def active(self) -> RoleQuerySet:
        return self.filter(is_active=True, is_deleted=False)

    def by_codes(self, codes: list[str]) -> RoleQuerySet:
        return self.active().filter(code__in=codes)
