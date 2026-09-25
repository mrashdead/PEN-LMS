# apps/accounts/models.py
from __future__ import annotations

import uuid
from typing import Iterable, Optional

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q, UniqueConstraint
from django.utils import timezone

from apps.accounts.manager import RoleQuerySet, UserManager
from apps.core.models import SoftDeleteModel, TimeStampedModel



class Role(TimeStampedModel, SoftDeleteModel):
    """
    نقش سازمانی برای Workflow Engine.
    مثال واقعی مرخصی:
      - employee   → شروع Draft / Submit
      - manager    → Approve سطح ۱
      - hr         → Approve نهایی
      - admin      → تعریف فرآیند
    Transition و TaskAssignment با role.code کار می‌کنند (نه pk).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.SlugField(
        max_length=64,
        db_index=True,
        help_text="Immutable business key, e.g. manager, hr, employee "
                  "(یکتا در میان نقش‌های زنده)",
    )
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)
    # اولویت برای انتخاب assignee وقتی چند نقش مجازند
    priority = models.PositiveSmallIntegerField(default=100)

    objects = RoleQuerySet.as_manager()
    all_objects = models.Manager()

    class Meta:
        app_label = "accounts"
        db_table = "accounts_role"
        ordering = ("priority", "code")
        verbose_name = "Role"
        verbose_name_plural = "Roles"
        indexes = [
            models.Index(fields=["code", "is_active"]),
            models.Index(fields=["priority"]),
        ]
        constraints = [
            # کد نقش (business key) فقط در میان نقش‌های «زنده» یکتاست (B5) —
            # حذف نرم یک نقش نباید ساخت نقش هم‌کد را برای همیشه مسدود کند.
            models.UniqueConstraint(
                fields=["code"],
                condition=models.Q(is_deleted=False),
                name="uniq_accounts_role_code_alive",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.code} ({self.name})"

    def clean(self) -> None:
        self.code = (self.code or "").strip().lower()
        if not self.code:
            raise ValidationError({"code": "code is required"})

    def save(self, *args, **kwargs) -> None:
        self.code = (self.code or "").strip().lower()
        super().save(*args, **kwargs)


class User(AbstractUser, TimeStampedModel, SoftDeleteModel):
    """
    Custom user — AUTH_USER_MODEL.
    فیلدهای سازمانی برای Inbox و Routing واقعی.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # AbstractUser: username, email, first_name, last_name, is_staff, ...
    email = models.EmailField(blank=True, null=True, db_index=True)
    employee_code = models.CharField(
        max_length=32,
        blank=True,
        null=True,
        help_text="کد پرسنلی — مثال: EMP-10042 (یکتا در میان کاربران زنده)",
    )
    mobile = models.CharField(max_length=20, blank=True, default="")
    department = models.CharField(max_length=128, blank=True, default="", db_index=True)
    job_title = models.CharField(max_length=128, blank=True, default="")

    # مدیر مستقیم — برای routing مرخصی به manager
    manager = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subordinates",
        db_index=True,
    )

    roles = models.ManyToManyField(
        Role,
        through="UserRole",
        through_fields=("user", "role"),
        related_name="users",
        blank=True,
    )

    objects = UserManager()

    class Meta:
        app_label = "accounts"
        db_table = "accounts_user"
        verbose_name = "User"
        verbose_name_plural = "Users"
        indexes = [
            models.Index(fields=["username"]),
            models.Index(fields=["department", "is_active"]),
            models.Index(fields=["employee_code"]),
        ]
        constraints = [
            UniqueConstraint(
                fields=["email"],
                condition=Q(email__isnull=False) & ~Q(email=""),
                name="uniq_user_email_nonempty",
            ),
            UniqueConstraint(
                fields=["employee_code"],
                condition=Q(is_deleted=False, employee_code__isnull=False)
                & ~Q(employee_code=""),
                name="uniq_user_employee_code_alive",
            ),
        ]

    def __str__(self) -> str:
        return self.username

    # ---------- Role helpers (Engine استفاده می‌کند) ----------

    def role_codes(self) -> set[str]:
        now = timezone.now()
        return set(
            UserRole.objects.filter(user_id=self.pk, is_active=True)
            .filter(Q(valid_from__isnull=True) | Q(valid_from__lte=now))
            .filter(Q(valid_to__isnull=True) | Q(valid_to__gte=now))
            .filter(role__is_active=True, role__is_deleted=False)
            .values_list("role__code", flat=True)
        )

    def has_role(self, code: str) -> bool:
        return code.strip().lower() in self.role_codes()

    def has_any_role(self, codes: Iterable[str]) -> bool:
        wanted = {c.strip().lower() for c in codes}
        return bool(self.role_codes() & wanted)

    @transaction.atomic
    def assign_role(
        self,
        role: Role | str,
        *,
        assigned_by: Optional[User] = None,
        valid_from=None,
        valid_to=None,
    ) -> UserRole:
        """
        Idempotent assign — برای seed و admin.
        role: instance یا code
        """
        # role.code is unique only among live rows now (partial unique
        # index), so the lookup must exclude soft-deleted twins — a bare
        # .get(code=...) could otherwise raise MultipleObjectsReturned.
        if isinstance(role, str):
            role_obj = (
                Role.objects.select_for_update()
                .filter(code=role.strip().lower(), is_deleted=False)
                .first()
            )
            if role_obj is None:
                raise Role.DoesNotExist(f"role '{role}' not found")
        else:
            role_obj = Role.objects.select_for_update().get(pk=role.pk)

        obj, _created = UserRole.objects.select_for_update().get_or_create(
            user=self,
            role=role_obj,
            defaults={
                "is_active": True,
                "assigned_by": assigned_by,
                "valid_from": valid_from,
                "valid_to": valid_to,
            },
        )
        if not _created:
            obj.is_active = True
            obj.assigned_by = assigned_by or obj.assigned_by
            obj.valid_from = valid_from
            obj.valid_to = valid_to
            obj.save(
                update_fields=[
                    "is_active",
                    "assigned_by",
                    "valid_from",
                    "valid_to",
                    "updated_at",
                ]
            )
        return obj

    @transaction.atomic
    def revoke_role(self, role: Role | str) -> None:
        if isinstance(role, str):
            UserRole.objects.filter(
                user=self, role__code=role.strip().lower()
            ).update(is_active=False, updated_at=timezone.now())
        else:
            UserRole.objects.filter(user=self, role=role).update(
                is_active=False, updated_at=timezone.now()
            )


class UserRole(TimeStampedModel):
    """
    Through table — نقش موقت/تاریخ‌دار (مثال: سرپرست جایگزین ۲ هفته).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_roles",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="user_roles",
    )
    is_active = models.BooleanField(default=True, db_index=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_roles",
    )
    note = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        app_label = "accounts"
        db_table = "accounts_user_role"
        verbose_name = "User Role"
        verbose_name_plural = "User Roles"
        constraints = [
            UniqueConstraint(
                fields=["user", "role"],
                name="uniq_accounts_user_role",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["role", "is_active"]),
            models.Index(fields=["valid_from", "valid_to"]),
        ]

    def __str__(self) -> str:
        return f"{self.user_id} → {self.role_id}"

    def clean(self) -> None:
        if self.valid_from and self.valid_to and self.valid_from > self.valid_to:
            raise ValidationError("valid_from must be <= valid_to")

    @property
    def is_currently_valid(self) -> bool:
        if not self.is_active:
            return False
        now = timezone.now()
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_to and now > self.valid_to:
            return False
        return True
