# apps/core/models.py
from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING, Any, Optional, Tuple, TypeVar

import jdatetime
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

T = TypeVar("T", bound=models.Model)


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
