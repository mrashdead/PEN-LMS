# apps/core/models.py
from __future__ import annotations

import uuid
from typing import Any, Optional, Tuple, TypeVar

from django.db import models
from django.utils import timezone

T = TypeVar("T", bound=models.Model)


class TimeStampedModel(models.Model):
    """created_at / updated_at برای تمام موجودیت‌های دامنه."""

    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        editable=False,
    )
    updated_at = models.DateTimeField(auto_now=True)

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
