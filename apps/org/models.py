"""
Organizational models.

Only ONE new persisted concept is needed for the org UX: ``Delegation``
(جانشینی) — a time-bound grant of a person's cartable to a substitute, fully
auditable. Everything else the org screens show (chart, effective
permissions, responsibilities, unit performance) is DERIVED read-only from
existing models (User.manager/department, Role/UserRole, Group permissions,
Workflow Transition.allowed_role_codes, WorkflowTask). Deriving instead of
duplicating keeps a single source of truth.
"""
from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.core.models import DomainModel


class Delegation(DomainModel):
    """
    جانشینی: «از تاریخ X تا Y، مهدی جانشین سارا در کارتابل واحد آموزش است».

    - scope: کدام کارتابل/واحد (department string) یا کدام فرآیند (workflow
      code) — حداقل یکی لازم است تا دامنه روشن باشد.
    - status: فعال بودن جانشینی زمان‌محور است (valid_from/valid_to) + flag.
    - audit: created_by + timestamps از DomainModel؛ لغو با is_active=False
      و تاریخ/کاربر لغو ثبت می‌شود (بدون حذف).
    """

    principal = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="delegations_given",
        help_text="کسی که کارش به دیگری سپرده می‌شود (صاحب اصلی کارتابل).",
    )
    delegate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="delegations_received",
        help_text="جانشین.",
    )
    department = models.CharField(
        max_length=128, blank=True, default="",
        help_text="واحد/دپارتمان مشمول (خالی = کل کارتابل).",
    )
    workflow_code = models.SlugField(
        max_length=64, blank=True, default="",
        help_text="اگر فقط یک فرآیند خاص مد نظر است (مثلاً leave-request).",
    )
    reason = models.CharField(max_length=255, blank=True, default="")
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    is_active = models.BooleanField(default=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="created_delegations",
    )
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="revoked_delegations",
    )

    class Meta:
        app_label = "org"
        db_table = "org_delegation"
        verbose_name = "Delegation (جانشینی)"
        verbose_name_plural = "Delegations (جانشینی‌ها)"
        ordering = ("-valid_from",)
        indexes = [
            models.Index(fields=["principal", "is_active"]),
            models.Index(fields=["delegate", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.delegate_id} ⇐ {self.principal_id} [{self.valid_from:%Y-%m-%d}..{self.valid_to:%Y-%m-%d}]"

    def clean(self) -> None:
        if self.delegate_id and self.principal_id and self.delegate_id == self.principal_id:
            raise ValidationError({"delegate": "جانشین نمی‌تواند خودِ صاحب کار باشد."})
        if self.valid_to and self.valid_from and self.valid_to <= self.valid_from:
            raise ValidationError({"valid_to": "پایان باید بعد از شروع باشد."})
        if not (self.department or self.workflow_code):
            raise ValidationError(
                {"department": "حداقل یک دامنه (واحد یا فرآیند) مشخص کنید."}
            )

    @property
    def is_live(self) -> bool:
        now = timezone.now()
        return bool(
            self.is_active
            and self.valid_from and self.valid_from <= now
            and self.valid_to and self.valid_to >= now
        )
