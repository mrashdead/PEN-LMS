# apps/core/models.py
from __future__ import annotations

import datetime
import logging
import uuid
from typing import TYPE_CHECKING, Any, Optional, Tuple, TypeVar

import jdatetime
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.utils import timezone

T = TypeVar("T", bound=models.Model)

logger = logging.getLogger(__name__)


class JalaliDateField(models.DateField):
    """
    فیلد تاریخ شمسی — در دیتابیس به صورت میلادی (Gregorian) ذخیره می‌شود
    اما از طریق property و form به صورت شمسی (Jalali) تبادل می‌کند.
    """

    description = "Jalali (Shamsi) date field"

    def from_db_value(self, value, expression, connection):
        if value is None:
            return None
        if isinstance(value, jdatetime.date):
            return value
        try:
            if isinstance(value, datetime.date):
                return jdatetime.date.fromgregorian(date=value)
            return value
        except (ValueError, TypeError):
            return value

    def to_python(self, value):
        if value is None:
            return value
        if isinstance(value, jdatetime.date):
            return value.togregorian()
        if isinstance(value, datetime.date):
            return value
        try:
            parsed = jdatetime.date.fromisoformat(str(value))
            return parsed.togregorian()
        except (ValueError, TypeError):
            pass
        try:
            return datetime.date.fromisoformat(str(value))
        except (ValueError, TypeError):
            raise ValidationError(
                "تاریخ نامعتبر. لطفاً تاریخ را به فرمت YYYY-MM-DD (شمسی یا میلادی) وارد کنید."
            )

    def get_prep_value(self, value):
        value = self.to_python(value)
        if isinstance(value, jdatetime.date):
            value = value.togregorian()
        return super().get_prep_value(value)

    def formfield(self, **kwargs):
        from django.forms import DateField as FormDateField

        defaults = {"form_class": FormDateField}
        defaults.update(kwargs)
        return super().formfield(**defaults)


class JalaliDateTimeField(models.DateTimeField):
    """
    فیلد تاریخ و زمان شمسی — در دیتابیس به صورت میلادی ذخیره می‌شود.
    """

    description = "Jalali (Shamsi) datetime field"

    def from_db_value(self, value, expression, connection):
        if value is None:
            return None
        if isinstance(value, jdatetime.datetime):
            return value
        try:
            if isinstance(value, datetime.datetime):
                if timezone.is_aware(value):
                    value = timezone.localtime(value)
                return jdatetime.datetime.fromgregorian(datetime=value)
            return value
        except (ValueError, TypeError):
            return value

    def to_python(self, value):
        if value is None:
            return value
        if isinstance(value, jdatetime.datetime):
            return value.togregorian()
        if isinstance(value, datetime.datetime):
            return value
        try:
            parsed = jdatetime.datetime.fromisoformat(str(value))
            return parsed.togregorian()
        except (ValueError, TypeError):
            pass
        try:
            return datetime.datetime.fromisoformat(str(value))
        except (ValueError, TypeError):
            raise ValidationError(
                "تاریخ و زمان نامعتبر. لطفاً به فرمت YYYY-MM-DD HH:MM:SS وارد کنید."
            )

    def get_prep_value(self, value):
        value = self.to_python(value)
        if isinstance(value, jdatetime.datetime):
            value = value.togregorian()
        return super().get_prep_value(value)

    def formfield(self, **kwargs):
        defaults = {"form_class": type(self).__class__}
        defaults.update(kwargs)
        return super().formfield(**defaults)


class TimeStampedModel(models.Model):
    """created_at / updated_at برای تمام موجودیت‌های دامنه."""

    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        editable=False,
    )
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def created_at_jalali(self) -> str:
        from apps.core.utils import persian_date
        return persian_date(self.created_at)

    @property
    def updated_at_jalali(self) -> str:
        from apps.core.utils import persian_date
        return persian_date(self.updated_at)

    class Meta:
        abstract = True


class UUIDPrimaryKeyModel(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    class Meta:
        abstract = True


class SoftDeleteQuerySet(models.QuerySet):
    def alive(self) -> SoftDeleteQuerySet:
        return self.filter(is_deleted=False)

    def dead(self) -> SoftDeleteQuerySet:
        return self.filter(is_deleted=True)

    def delete(self) -> Tuple[int, dict[str, int]]:
        """Soft-delete در سطح queryset (bulk)."""
        now = timezone.now()
        count = self.update(is_deleted=True, deleted_at=now)
        return count, {}


class SoftDeleteManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    def get_queryset(self) -> SoftDeleteQuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)


class SoftDeleteModel(models.Model):
    """
    حذف منطقی.
    توجه: روی User از UserManager سفارشی استفاده کنید؛
    این Manager برای Role و مدل‌های غیر-Auth مناسب است.
    """

    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def soft_delete(self) -> None:
        self.is_deleted = True
        self.deleted_at = timezone.now()
        update_fields = ["is_deleted", "deleted_at"]
        # اگر مدل TimeStamped هم باشد
        if hasattr(self, "updated_at"):
            update_fields.append("updated_at")
        self.save(update_fields=update_fields)

    def restore(self) -> None:
        self.is_deleted = False
        self.deleted_at = None
        update_fields = ["is_deleted", "deleted_at"]
        if hasattr(self, "updated_at"):
            update_fields.append("updated_at")
        self.save(update_fields=update_fields)

    def delete(
        self,
        using: Optional[str] = None,
        keep_parents: bool = False,
    ) -> Tuple[int, dict[str, int]]:
        """پیش‌فرض: soft delete (جلوگیری از hard delete تصادفی)."""
        self.soft_delete()
        return 1, {self._meta.label: 1}

    def hard_delete(
        self,
        using: Optional[str] = None,
        keep_parents: bool = False,
    ) -> Tuple[int, dict[str, int]]:
        return super().delete(using=using, keep_parents=keep_parents)


class DomainModel(UUIDPrimaryKeyModel, TimeStampedModel, SoftDeleteModel):
    """Base ترکیبی برای Entityهای دامنه (Role، Definition، ...)."""

    class Meta:
        abstract = True


class AuditEvent(UUIDPrimaryKeyModel, TimeStampedModel):
    """
    حسابرسی دیتابیسیِ رخدادهای امنیتی/حساس (معیار §13-4).

    تفاوت با ActionLog گردش‌کار: ActionLog تاریخچه‌ی *فرآیند* است؛ این جدول
    تاریخچه‌ی *دسترسی و تغییر* است — رد دسترسی (۴۰۳)، دانلود فایل، خواندن
    PII خام، تغییر فیلدهای حساس. Append-only: هیچ ویرایش/حذفی از طریق ORM
    ممکن نیست (delete در سطح queryset هم به hard-delete هشدار می‌دهد).
    """

    class Kind(models.TextChoices):
        ACCESS_DENIED = "access_denied", "رد دسترسی"
        DOWNLOAD = "download", "دانلود فایل"
        SENSITIVE_READ = "sensitive_read", "خواندن داده‌ی حساس"
        FIELD_CHANGE = "field_change", "تغییر فیلد حساس"

    kind = models.CharField(max_length=32, choices=Kind.choices, db_index=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="audit_events",
        help_text="کاربر انجام‌دهنده (None = ناشناس/بی‌احراز هویت)",
    )
    object = GenericForeignKey("content_type", "object_id")
    content_type = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL, null=True, blank=True,
    )
    object_id = models.CharField(max_length=64, blank=True, default="", db_index=True)
    summary = models.CharField(
        max_length=512,
        help_text="خلاصه‌ی انسانی رخداد (فارسی)",
    )
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        app_label = "core"
        db_table = "core_audit_event"
        verbose_name = "Audit Event (رخداد حسابرسی)"
        verbose_name_plural = "Audit Events (رخدادهای حسابرسی)"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["kind", "created_at"]),
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.kind} — {self.summary[:60]}"

    def delete(self, *args, **kwargs):  # pragma: no cover - guard rail
        raise ProtectedError("AuditEvent append-only است و حذف نمی‌شود.", [])

    @classmethod
    def record(
        cls,
        *,
        kind: str,
        summary: str,
        actor=None,
        obj: object | None = None,
        metadata: dict | None = None,
        request=None,
    ) -> "AuditEvent | None":
        """
        کمکی برای ثبت امن: هرگز خطای حسابرسی، عملیات اصلی را نمی‌شکند.
        IP از استاندارد پروژه (X-Forwarded-For / REMOTE_ADDR) خوانده می‌شود.
        """
        try:
            from apps.core.utils import get_client_ip

            ct = None
            object_id = ""
            if obj is not None:
                ct = ContentType.objects.get_for_model(obj, for_concrete_model=False)
                object_id = str(obj.pk)
            ip = None
            if request is not None:
                ip = get_client_ip(request) or None
            actor_id = getattr(actor, "pk", None)
            if actor_id and not getattr(actor, "is_authenticated", True):
                actor_id = None
            return cls.objects.create(
                kind=kind,
                actor_id=actor_id,
                content_type=ct,
                object_id=object_id,
                summary=(summary or "")[:512],
                metadata=metadata or {},
                ip_address=ip,
            )
        except Exception:  # noqa: BLE001 — audit must never break the write path
            logger.exception("AuditEvent.record failed: %s", summary)
            return None


class AuditDeniedMixin:
    """
    میکس permission برای ثبت AuditEvent روی ردهای has_permission (۴۰۳).
    در has_object_permission هم‌زمان هم رد و هم ثبت می‌کند.
    """

    denial_summary = "دسترسی رد شد."

    def has_permission(self, request, view) -> bool:
        allowed = super().has_permission(request, view)
        if not allowed:
            AuditEvent.record(
                kind=AuditEvent.Kind.ACCESS_DENIED,
                summary=self.denial_summary,
                actor=request.user if request.user.is_authenticated else None,
                request=request,
                metadata={"view": type(view).__name__, "method": request.method},
            )
        return allowed
