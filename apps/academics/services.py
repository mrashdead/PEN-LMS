"""
Enrollment service for academics (B4): capacity enforced under a row lock.

Previously ``ClassGroup.capacity`` was display-only and the enrollment API
created rows with a bare serializer.save(), so two concurrent requests could
both pass any check and over-enroll. Here the class-group row is locked for
the duration of the transaction and the active enrollment count is recomputed
FROM the locked rows, so the count can never exceed a non-zero capacity.
"""
from __future__ import annotations

import logging
from typing import Optional

from django.db import transaction

from apps.academics.models import ClassEnrollment, ClassGroup

logger = logging.getLogger(__name__)


class EnrollmentError(Exception):
    """Base error — maps to HTTP 400 at the API edge."""


class CapacityExceededError(EnrollmentError):
    """ظرفیت کلاس تکمیل است."""


class AlreadyEnrolledError(EnrollmentError):
    """دانش‌آموز از قبل در این کلاس ثبت‌نام دارد."""


class EnrollmentService:

    @transaction.atomic
    def enroll(
        self,
        *,
        class_group_id,
        student_id,
        enrollment_date=None,
        actor: Optional[object] = None,
    ) -> ClassEnrollment:
        """
        Lock the class group, count LIVE active enrollments, and create (or
        reactivate) the student's enrollment only when a seat is free.

        Capacity semantics preserved from the model: capacity == 0 → unlimited.
        """
        group: ClassGroup = (
            ClassGroup.objects.select_for_update().filter(pk=class_group_id).first()
        )
        if group is None:
            raise EnrollmentError("کلاس مورد نظر یافت نشد.")

        existing = ClassEnrollment.all_objects.filter(
            class_group=group, student_id=student_id
        ).first()
        if existing is not None and not existing.is_deleted and existing.is_active:
            raise AlreadyEnrolledError("این دانش‌آموز از قبل در کلاس ثبت‌نام دارد.")

        live_count = ClassEnrollment.objects.filter(
            class_group=group, is_active=True
        ).count()
        if group.capacity and live_count >= group.capacity:
            raise CapacityExceededError(
                f"ظرفیت کلاس تکمیل است ({live_count}/{group.capacity})."
            )

        if existing is not None:
            # Soft-deleted twin → revive it instead of creating a duplicate
            # (the live-only unique constraint also guarantees no clash).
            existing.is_deleted = False
            existing.deleted_at = None
            existing.is_active = True
            if enrollment_date is not None:
                existing.enrollment_date = enrollment_date
            existing.save(
                update_fields=["is_deleted", "deleted_at", "is_active",
                               "enrollment_date", "updated_at"]
            )
            enrollment = existing
        else:
            kwargs = {"class_group": group, "student_id": student_id}
            if enrollment_date is not None:
                kwargs["enrollment_date"] = enrollment_date
            enrollment = ClassEnrollment.objects.create(**kwargs)

        logger.info(
            "student %s enrolled in class %s (by %s)",
            student_id, group.pk, getattr(actor, "pk", actor),
        )
        if actor is not None and getattr(actor, "is_authenticated", False):
            from apps.core.models import AuditEvent
            AuditEvent.record(
                kind=AuditEvent.Kind.FIELD_CHANGE, summary="ثبت‌نام دانش‌آموز در کلاس",
                actor=actor, obj=enrollment,
                metadata={"action": "create" if existing is None else "update", "resource": "class-enrollments"},
            )
        return enrollment

    @transaction.atomic
    def unenroll(self, *, enrollment_id, actor: Optional[object] = None) -> None:
        """Soft-delete an enrollment, freeing the seat under the same lock."""
        enrollment = (
            ClassEnrollment.objects.select_for_update().filter(pk=enrollment_id).first()
        )
        if enrollment is None:
            raise EnrollmentError("ثبت‌نام مورد نظر یافت نشد.")
        enrollment.is_active = False
        enrollment.save(update_fields=["is_active", "updated_at"])
        enrollment.delete()  # soft delete → seat freed for re-enrollment (B5/B4)
        logger.info("enrollment %s removed (by %s)", enrollment_id, getattr(actor, "pk", actor))


enrollment_service = EnrollmentService()
