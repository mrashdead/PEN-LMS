"""
Staff operations service layer — business logic for timesheet, leave and
work reports. Views are thin HTTP adapters; every rule lives here.

Concurrency invariants:
  * clock-in/out and review run inside ``transaction.atomic`` with
    ``select_for_update`` on the target row, so two concurrent reviews cannot
    both flip the same record, and a double-submit of the same day cannot
    create two live rows (the partial unique index is the backstop).
"""
from __future__ import annotations

import datetime as dt
import logging
from decimal import Decimal
from typing import Optional

from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.db.models import Q, Sum
from django.utils import timezone

from apps.staff.models import (
    APPROVER_ROLES,
    LeaveRequest,
    LeaveType,
    ReviewHistory,
    ReviewStatus,
    TimesheetEntry,
    WorkReport,
)
from apps.staff.models import _log_transition  # noqa: F401 — shared audit write path

logger = logging.getLogger(__name__)


class StaffServiceError(Exception):
    """Base error for the staff service (maps to HTTP 400 at the API edge)."""


class AlreadyClockedInError(StaffServiceError):
    """کاربر برای این روز قبلاً ورود زده است."""


class NotClockedInError(StaffServiceError):
    """ورودی برای خروج ثبت نشده است."""


class InvalidReviewError(StaffServiceError):
    """انتقال وضعیت مجاز نیست (وضعیت فعلی یا نقش مجاز نیست)."""


class LeaveOverlapError(StaffServiceError):
    """این بازه با یک مرخصی تأییدشده‌ی دیگر هم‌پوشانی دارد."""


# ─────────────────────────────────────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────────────────────────────────────

def _is_approver(user) -> bool:
    if user is None or not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    return bool(set(user.role_codes()) & set(APPROVER_ROLES))


def _person_of(user):
    return getattr(user, "person", None)


# ─────────────────────────────────────────────────────────────────────────────
# ۱) ساعت کاری
# ─────────────────────────────────────────────────────────────────────────────

@transaction.atomic
def clock_in(*, user, work_date: Optional[dt.date] = None, kind: str = TimesheetEntry.Kind.REGULAR,
             note: str = "") -> TimesheetEntry:
    """
    ثبت ورود برای یک روز کاری. اگر ردیفِ زنده‌ی همان روز وجود داشته باشد
    (مثلاً پس از بازگشتِ عمدی)، همان ردیف برمی‌گردد — عملیات idempotent است.
    """
    if user is None or not getattr(user, "is_authenticated", False):
        raise StaffServiceError("کاربر معتبر نیست.")
    day = work_date or timezone.localdate()
    if day > timezone.localdate():
        raise StaffServiceError("تاریخ کاری نمی‌تواند در آینده باشد.")

    existing = (
        TimesheetEntry.objects.select_for_update()
        .filter(user=user, work_date=day, kind=kind, is_deleted=False)
        .first()
    )
    if existing is not None:
        if existing.check_out is not None:
            raise AlreadyClockedInError(
                "برای این روز ورود و خروج قبلاً ثبت شده است."
            )
        return existing

    try:
        return TimesheetEntry.objects.create(
            user=user,
            person=_person_of(user),
            work_date=day,
            kind=kind,
            check_in=timezone.now(),
            note=(note or "").strip(),
            status=ReviewStatus.PENDING,
        )
    except IntegrityError as exc:
        # Lost the race for the same (user, date, kind) — re-read and return.
        existing = TimesheetEntry.objects.filter(
            user=user, work_date=day, kind=kind, is_deleted=False,
        ).first()
        if existing is not None:
            return existing
        raise StaffServiceError(str(exc)) from exc


@transaction.atomic
def clock_out(*, user, work_date: Optional[dt.date] = None,
              kind: str = TimesheetEntry.Kind.REGULAR) -> TimesheetEntry:
    """ثبت خروج — ردیفِ بازِ همان روز را می‌بندد."""
    day = work_date or timezone.localdate()
    entry = (
        TimesheetEntry.objects.select_for_update()
        .filter(user=user, work_date=day, kind=kind, is_deleted=False)
        .order_by("-check_in").first()
    )
    if entry is None:
        raise NotClockedInError("برای این روز ورودی ثبت نشده است.")
    if entry.check_out is not None:
        return entry
    entry.check_out = timezone.now()
    entry.save(update_fields=["check_out", "updated_at"])
    return entry


def timesheet_status(*, user, day: Optional[dt.date] = None) -> dict:
    """
    وضعیت ساعت کاری یک کاربر در یک روز — برای نمایش داشبورد.
    همه‌ی ردیف‌های آن روز در یک کوئری خوانده می‌شوند.
    """
    day = day or timezone.localdate()
    rows = list(
        TimesheetEntry.objects.filter(
            user=user, work_date=day, is_deleted=False,
        ).order_by("kind")
    )
    return {
        "date": day.isoformat(),
        "open_entry_id": str(rows[-1].pk) if rows and rows[-1].is_open else None,
        "rows": [
            {
                "id": str(r.pk),
                "kind": r.kind,
                "kind_display": r.get_kind_display(),
                "check_in": r.check_in.isoformat() if r.check_in else None,
                "check_out": r.check_out.isoformat() if r.check_out else None,
                "duration_minutes": r.duration_minutes,
                "status": r.status,
                "status_display": r.get_status_display(),
                "note": r.note,
            }
            for r in rows
        ],
        "total_minutes": sum(r.duration_minutes or 0 for r in rows),
    }


def timesheets_visible_to(user, *, for_review: bool = False):
    """
    DataScope for timesheets — mirrors apps.academics.scoping:

      elevated/approver → all rows;
      other staff       → own rows only.
    ``for_review=True`` narrows to approvers (used by review endpoints).
    """
    qs = TimesheetEntry.objects.select_related("user", "person", "reviewed_by")
    if user is None or not getattr(user, "is_authenticated", False):
        return qs.none()
    if _is_approver(user):
        return qs
    return qs.filter(user=user)


@transaction.atomic
def review_timesheet(*, entry_id, actor, decision: str, comment: str = "",
                     rejection_reason: str = "",
                     override_minutes: Optional[int] = None) -> TimesheetEntry:
    """
    تأیید یا رد یک ردیف ساعت کاری توسط مسئول مجاز.

    تصمیم فقط روی رکوردهای pending ممکن است؛ تاریخچه append-only نوشته
    می‌شود و در صورت رد، دلیل اجباری است.
    """
    if decision not in {ReviewStatus.APPROVED, ReviewStatus.REJECTED}:
        raise InvalidReviewError("تصمیم باید approve یا reject باشد.")
    if not _is_approver(actor):
        raise InvalidReviewError("شما مجاز به بررسی ساعت کاری نیستید.")

    entry = (
        TimesheetEntry.objects.select_for_update()
        .filter(pk=entry_id, is_deleted=False).first()
    )
    if entry is None:
        raise StaffServiceError("رکورد ساعت کاری یافت نشد.")
    if entry.status != ReviewStatus.PENDING:
        raise InvalidReviewError(
            f"این رکورد قبلاً بررسی شده است ({entry.get_status_display()})."
        )
    if decision == ReviewStatus.REJECTED and not (rejection_reason or "").strip():
        raise InvalidReviewError("برای رد ساعت کاری، ذکر دلیل الزامی است.")

    previous = entry.status
    if override_minutes is not None and decision == ReviewStatus.APPROVED:
        if override_minutes < 0 or override_minutes > 24 * 60:
            raise InvalidReviewError("مدت زمان اصلاحی نامعتبر است.")
        entry.override_minutes = override_minutes

    entry.status = decision
    entry.reviewed_by = actor
    entry.reviewed_at = timezone.now()
    entry.rejection_reason = (rejection_reason or "").strip() if decision == ReviewStatus.REJECTED else ""
    entry.save(update_fields=[
        "status", "reviewed_by", "reviewed_at", "rejection_reason",
        "override_minutes", "updated_at",
    ])

    _log_transition(
        record_type=ReviewHistory.RecordType.TIMESHEET,
        record_id=entry.pk, from_status=previous, to_status=decision,
        actor=actor, comment=comment, rejection_reason=rejection_reason,
        metadata={"work_date": entry.work_date.isoformat()},
    )
    return entry


# ─────────────────────────────────────────────────────────────────────────────
# ۲) مرخصی
# ─────────────────────────────────────────────────────────────────────────────

def _leave_duration(*, start: dt.date, end: dt.date, unit: str) -> Decimal:
    """Compute duration in ``unit`` — calendar days, half-day collapse, hours."""
    days = (end - start).days + 1
    if unit == LeaveRequest.Unit.HALF_DAY:
        return Decimal("0.5")
    if unit == LeaveRequest.Unit.HOUR:
        # Hour-based leave spans at most one business day in this model; the
        # UI asks for hours explicitly, but the stored field stays numeric so
        # reports sum cleanly.
        return Decimal(max(days, 0))
    return Decimal(max(days, 0))


@transaction.atomic
def create_leave_request(*, user, leave_type, start_date, end_date,
                         unit: str = LeaveRequest.Unit.DAY,
                         description: str = "", attachment=None) -> LeaveRequest:
    """
    ثبت درخواست مرخصی — هم‌پوشانی با مرخصی‌های تأییدشده/در انتظار بررسی
    نمی‌شود (قانون کسب‌وکار: یک کاربر در یک روز فقط یک مرخصی دارد).
    """
    if user is None or not getattr(user, "is_authenticated", False):
        raise StaffServiceError("کاربر معتبر نیست.")
    if not leave_type or not getattr(leave_type, "pk", None):
        raise StaffServiceError("نوع مرخصی الزامی است.")
    if not start_date or not end_date:
        raise StaffServiceError("تاریخ شروع و پایان الزامی است.")
    if end_date < start_date:
        raise StaffServiceError("تاریخ پایان باید بعد از شروع باشد.")
    if start_date < timezone.localdate():
        raise StaffServiceError("تاریخ شروع مرخصی نمی‌تواند در گذشته باشد.")
    if unit == LeaveRequest.Unit.HALF_DAY and start_date != end_date:
        raise StaffServiceError("مرخصی نیم‌روز فقط برای یک روز مجاز است.")

    # Overlap guard against live, non-rejected requests of the same user.
    clash = LeaveRequest.objects.filter(
        user=user,
        status__in=[ReviewStatus.PENDING, ReviewStatus.APPROVED],
        is_deleted=False,
    ).filter(start_date__lte=end_date, end_date__gte=start_date).first()
    if clash is not None:
        raise LeaveOverlapError(
            "در این بازه قبلاً درخواست مرخصی ثبت شده است "
            f"({clash.start_date} تا {clash.end_date})."
        )

    duration = _leave_duration(start=start_date, end=end_date, unit=unit)
    request = LeaveRequest(
        user=user,
        person=_person_of(user),
        leave_type=leave_type,
        start_date=start_date,
        end_date=end_date,
        unit=unit,
        duration=duration,
        description=(description or "").strip(),
        status=ReviewStatus.PENDING,
    )
    if attachment:
        request.attachment = attachment
    try:
        request.full_clean()
    except ValidationError as exc:
        raise StaffServiceError(str(exc)) from exc
    request.save()
    return request


def leave_requests_visible_to(user, *, for_review: bool = False):
    """
    DataScope for leave requests — approvers see all (or the pending queue),
    everyone else sees only their own requests.
    """
    qs = LeaveRequest.objects.select_related(
        "user", "person", "leave_type", "reviewed_by", "workflow_instance",
    )
    if user is None or not getattr(user, "is_authenticated", False):
        return qs.none()
    if _is_approver(user):
        return qs
    return qs.filter(user=user)


@transaction.atomic
def review_leave_request(*, request_id, actor, decision: str,
                         comment: str = "", rejection_reason: str = "") -> LeaveRequest:
    """تأیید یا رد درخواست مرخصی — فقط رکوردهای pending، با تاریخچه append-only."""
    if decision not in {ReviewStatus.APPROVED, ReviewStatus.REJECTED}:
        raise InvalidReviewError("تصمیم باید approve یا reject باشد.")
    if not _is_approver(actor):
        raise InvalidReviewError("شما مجاز به بررسی درخواست مرخصی نیستید.")

    request = (
        LeaveRequest.objects.select_for_update()
        .filter(pk=request_id, is_deleted=False).first()
    )
    if request is None:
        raise StaffServiceError("درخواست مرخصی یافت نشد.")
    if request.status != ReviewStatus.PENDING:
        raise InvalidReviewError(
            f"این درخواست قبلاً بررسی شده است ({request.get_status_display()})."
        )
    if decision == ReviewStatus.REJECTED and not (rejection_reason or "").strip():
        raise InvalidReviewError("برای رد مرخصی، ذکر دلیل الزامی است.")

    previous = request.status
    request.status = decision
    request.reviewed_by = actor
    request.reviewed_at = timezone.now()
    request.rejection_reason = (rejection_reason or "").strip() if decision == ReviewStatus.REJECTED else ""
    request.save(update_fields=[
        "status", "reviewed_by", "reviewed_at", "rejection_reason", "updated_at",
    ])

    _log_transition(
        record_type=ReviewHistory.RecordType.LEAVE,
        record_id=request.pk, from_status=previous, to_status=decision,
        actor=actor, comment=comment, rejection_reason=rejection_reason,
        metadata={
            "leave_type": request.leave_type_id and str(request.leave_type_id),
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat(),
        },
    )
    return request


@transaction.atomic
def cancel_leave_request(*, request_id, actor) -> LeaveRequest:
    """کاربر می‌تواند درخواست pending خود را لغو کند (نه تأییدشده را)."""
    request = (
        LeaveRequest.objects.select_for_update()
        .filter(pk=request_id, is_deleted=False).first()
    )
    if request is None:
        raise StaffServiceError("درخواست مرخصی یافت نشد.")
    if request.user_id != actor.pk and not _is_approver(actor):
        raise InvalidReviewError("شما فقط می‌توانید درخواست خودتان را لغو کنید.")
    if request.status != ReviewStatus.PENDING:
        raise InvalidReviewError("فقط درخواست‌های در انتظار بررسی قابل لغو هستند.")

    previous = request.status
    request.status = ReviewStatus.CANCELLED
    request.save(update_fields=["status", "updated_at"])
    _log_transition(
        record_type=ReviewHistory.RecordType.LEAVE,
        record_id=request.pk, from_status=previous, to_status=ReviewStatus.CANCELLED,
        actor=actor, comment="لغو توسط کاربر",
    )
    return request


# ─────────────────────────────────────────────────────────────────────────────
# ۳) گزارش کاری
# ─────────────────────────────────────────────────────────────────────────────

@transaction.atomic
def create_work_report(*, user, report_date, title, description: str = "",
                       spent_minutes: int = 0,
                       timesheet_id=None) -> WorkReport:
    if user is None or not getattr(user, "is_authenticated", False):
        raise StaffServiceError("کاربر معتبر نیست.")
    if not (title or "").strip():
        raise StaffServiceError("عنوان فعالیت الزامی است.")
    if report_date is None:
        report_date = timezone.localdate()
    if report_date > timezone.localdate():
        raise StaffServiceError("تاریخ گزارش نمی‌تواند در آینده باشد.")
    if spent_minutes < 0 or spent_minutes > 24 * 60:
        raise StaffServiceError("مدت زمان صرف‌شده نامعتبر است.")

    report = WorkReport(
        user=user,
        person=_person_of(user),
        report_date=report_date,
        title=title.strip(),
        description=(description or "").strip(),
        spent_minutes=int(spent_minutes or 0),
        status=ReviewStatus.PENDING,
    )
    if timesheet_id:
        ts = TimesheetEntry.objects.filter(
            pk=timesheet_id, user=user, is_deleted=False,
        ).first()
        if ts is not None:
            report.timesheet = ts
    report.save()
    return report


def work_reports_visible_to(user, *, for_review: bool = False):
    """DataScope for work reports — same shape as timesheets/leave."""
    qs = WorkReport.objects.select_related("user", "person", "reviewed_by", "timesheet")
    if user is None or not getattr(user, "is_authenticated", False):
        return qs.none()
    if _is_approver(user):
        return qs
    return qs.filter(user=user)


@transaction.atomic
def review_work_report(*, report_id, actor, decision: str, comment: str = "",
                       rejection_reason: str = "") -> WorkReport:
    if decision not in {ReviewStatus.APPROVED, ReviewStatus.REJECTED}:
        raise InvalidReviewError("تصمیم باید approve یا reject باشد.")
    if not _is_approver(actor):
        raise InvalidReviewError("شما مجاز به بررسی گزارش کاری نیستید.")

    report = (
        WorkReport.objects.select_for_update()
        .filter(pk=report_id, is_deleted=False).first()
    )
    if report is None:
        raise StaffServiceError("گزارش کاری یافت نشد.")
    if report.status != ReviewStatus.PENDING:
        raise InvalidReviewError(
            f"این گزارش قبلاً بررسی شده است ({report.get_status_display()})."
        )
    if decision == ReviewStatus.REJECTED and not (rejection_reason or "").strip():
        raise InvalidReviewError("برای رد گزارش کاری، ذکر دلیل الزامی است.")

    previous = report.status
    report.status = decision
    report.reviewed_by = actor
    report.reviewed_at = timezone.now()
    report.rejection_reason = (rejection_reason or "").strip() if decision == ReviewStatus.REJECTED else ""
    report.save(update_fields=[
        "status", "reviewed_by", "reviewed_at", "rejection_reason", "updated_at",
    ])

    _log_transition(
        record_type=ReviewHistory.RecordType.WORK_REPORT,
        record_id=report.pk, from_status=previous, to_status=decision,
        actor=actor, comment=comment, rejection_reason=rejection_reason,
        metadata={"report_date": report.report_date.isoformat()},
    )
    return report


def review_history_for(record_type: str, record_id) -> list[dict]:
    """Append-only trail for one record — newest first, bounded by table size."""
    rows = (
        ReviewHistory.objects.filter(record_type=record_type, record_id=record_id)
        .select_related("actor")
        .order_by("-created_at")
    )
    return [
        {
            "id": str(r.pk),
            "from_status": r.from_status,
            "to_status": r.to_status,
            "actor": str(getattr(r.actor, "username", r.actor_id)),
            "comment": r.comment,
            "rejection_reason": r.rejection_reason,
            "created_at": r.created_at.isoformat(),
            "created_at_jalali": r.created_at_jalali,
        }
        for r in rows
    ]


__all__ = [
    "AlreadyClockedInError",
    "InvalidReviewError",
    "LeaveOverlapError",
    "NotClockedInError",
    "StaffServiceError",
    "cancel_leave_request",
    "clock_in",
    "clock_out",
    "create_leave_request",
    "create_work_report",
    "leave_requests_visible_to",
    "review_history_for",
    "review_leave_request",
    "review_timesheet",
    "review_work_report",
    "timesheet_status",
    "timesheets_visible_to",
    "work_reports_visible_to",
]
