"""
Education domain services — the transactional core for B4:

  * enroll_student  — capacity enforced under select_for_update (§13:
    «ظرفیت و رزرو قفل شود»; previously capacity was display-only).
  * bulk_attendance — one AttendanceRecord per (session, student); the DB
    unique constraint is the final arbiter, the service surfaces friendly
    errors and idempotently upserts a re-posted roster.
  * create_session  — teacher / room / offering double-booking prevention
    using the transaction + logical-lock variant sanctioned by the report
    (§5, §7) instead of O(E²) app-level pairwise scans.
"""
from __future__ import annotations

import logging
from typing import Iterable, Optional

from django.db import IntegrityError, models, transaction
from django.db.models import Q

from apps.education.models import AttendanceRecord, ClassSession, CourseOffering

logger = logging.getLogger(__name__)


class EducationServiceError(Exception):
    """Base error for education services (maps to HTTP 400 at the API edge)."""


class CapacityExceededError(EducationServiceError):
    """ظرفیت برگزاری تکمیل است."""


class ScheduleConflictError(EducationServiceError):
    """تداخل زمانی مدرس/مکان/برگزاری برای این جلسه وجود دارد."""


# ─────────────────────────────────────────────────────────────────────────────
# Enrollment + capacity
# ─────────────────────────────────────────────────────────────────────────────

@transaction.atomic
def enroll_student(*, offering: CourseOffering, student, actor=None) -> CourseOffering:
    """
    Increment ``offering.enrolled_count`` under a row lock, refusing to pass a
    finite capacity. Raises CapacityExceededError (→ 400) instead of a silent
    over-enrollment (B4). Creating the academics.ClassEnrollment membership
    row stays the caller's responsibility.
    """
    locked = CourseOffering.objects.select_for_update().get(pk=offering.pk)
    if locked.status not in (CourseOffering.Status.DRAFT, CourseOffering.Status.OPEN):
        raise EducationServiceError("ثبت‌نام در این برگزاری مجاز نیست.")
    if locked.capacity and locked.enrolled_count >= locked.capacity:
        raise CapacityExceededError(
            f"ظرفیت این برگزاری تکمیل است ({locked.enrolled_count}/{locked.capacity})."
        )
    locked.enrolled_count += 1
    locked.save(update_fields=["enrolled_count", "updated_at"])
    logger.info("offering %s enrolled_count -> %s (by %s)",
                locked.pk, locked.enrolled_count, actor)
    return locked


@transaction.atomic
def withdraw_student(*, offering: CourseOffering, actor=None) -> CourseOffering:
    """Decrement the counter symmetrically (never below zero)."""
    locked = CourseOffering.objects.select_for_update().get(pk=offering.pk)
    locked.enrolled_count = max(locked.enrolled_count - 1, 0)
    locked.save(update_fields=["enrolled_count", "updated_at"])
    return locked


# ─────────────────────────────────────────────────────────────────────────────
# Sessions + conflict detection
# ─────────────────────────────────────────────────────────────────────────────

def _overlapping(date, start, end, **extra_filters) -> models.QuerySet:
    """
    Live, non-cancelled sessions on ``date`` whose [start,end) window overlaps
    the target window: (other.start < end) AND (other.end > start).
    """
    window = Q(start_time__lt=end) & Q(end_time__gt=start)
    return (
        ClassSession.objects.filter(is_deleted=False)
        .exclude(status=ClassSession.Status.CANCELLED)
        .filter(Q(session_date=date) & window)
        .filter(**extra_filters)
    )


@transaction.atomic
def create_session(
    *,
    offering: CourseOffering,
    session_date,
    start_time,
    end_time,
    session_number: Optional[int] = None,
    lesson=None,
    teacher=None,
    location=None,
    title: str = "",
    actor=None,
    check_conflicts: bool = True,
) -> ClassSession:
    """
    Create a real session, preventing teacher/room/offering double-booking.

    Lock protocol: lock the offering row first (serializes concurrent session
    creation for the same offering), then probe the three conflict dimensions
    with indexed range queries — O(log R + c), not O(E²).
    """
    CourseOffering.objects.select_for_update().get(pk=offering.pk)

    if session_number is None:
        last = (
            offering.sessions.filter(is_deleted=False)
            .order_by("-session_number").values_list("session_number", flat=True).first()
        )
        session_number = (last or 0) + 1

    if check_conflicts:
        if teacher is not None and _overlapping(
            session_date, start_time, end_time, teacher=teacher
        ).exists():
            raise ScheduleConflictError("مدرس در این بازه جلسه‌ی دیگری دارد.")
        if location is not None and _overlapping(
            session_date, start_time, end_time, location=location
        ).exists():
            raise ScheduleConflictError("این فضا در این بازه رزرو شده است.")
        if _overlapping(
            session_date, start_time, end_time, offering=offering
        ).exists():
            raise ScheduleConflictError("برگزاری در این بازه جلسه‌ی هم‌پوشان دارد.")

    try:
        session = ClassSession.objects.create(
            offering=offering,
            lesson=lesson,
            session_number=session_number,
            title=title,
            session_date=session_date,
            start_time=start_time,
            end_time=end_time,
            teacher=teacher,
            location=location,
        )
    except IntegrityError as exc:
        # (offering, session_number) live-unique raced → friendly 400.
        raise EducationServiceError("شماره جلسه تکراری است.") from exc
    logger.info("session %s created for offering %s (by %s)",
                session.pk, offering.pk, actor)
    return session


# ─────────────────────────────────────────────────────────────────────────────
# Attendance
# ─────────────────────────────────────────────────────────────────────────────

@transaction.atomic
def bulk_attendance(
    *,
    session: ClassSession,
    rows: Iterable[dict],
    recorded_by=None,
    replace: bool = False,
) -> dict:
    """
    Bulk attendance for one real session (idempotent on re-post).

    rows: [{"student": Person | pk, "status": present|absent|late|excused,
            "note": str?}, ...]

    The partial unique constraint (session, student | alive) is the source of
    truth: re-posting the same roster UPDATES existing rows instead of
    500-ing, so a double-click or a corrected sheet never duplicates a
    student's attendance (fixes B4's cross-submission double-record).
    ``replace=True`` soft-deletes rows for students missing from the payload.
    """
    session = ClassSession.objects.select_for_update().get(pk=session.pk)
    if session.status == ClassSession.Status.CANCELLED:
        raise EducationServiceError("برای جلسه‌ی لغوشده نمی‌توان حضور ثبت کرد.")

    created = updated = 0
    seen_ids: list = []
    for row in rows:
        student = row["student"]
        student_id = getattr(student, "pk", student)
        seen_ids.append(student_id)
        _obj, was_created = AttendanceRecord.objects.update_or_create(
            session=session,
            student_id=student_id,
            is_deleted=False,
            defaults={
                "status": row.get("status", AttendanceRecord.Status.PRESENT),
                "note": row.get("note", "") or "",
                "recorded_by": recorded_by,
                "deleted_at": None,
            },
        )
        created += int(was_created)
        updated += int(not was_created)

    if replace:
        AttendanceRecord.objects.filter(
            session=session, is_deleted=False
        ).exclude(student_id__in=seen_ids).delete()  # queryset soft-delete

    logger.info(
        "attendance for session %s: %d created, %d updated (by %s)",
        session.pk, created, updated, recorded_by,
    )
    return {"created": created, "updated": updated, "total": created + updated}


# ─────────────────────────────────────────────────────────────────────────────
# Form → table projection (B4)
# ─────────────────────────────────────────────────────────────────────────────

@transaction.atomic
def project_attendance_submission(
    *,
    class_group_id,
    session_date,
    session_number: int,
    session_start,
    session_end,
    rows: Iterable[dict],
    actor=None,
) -> dict:
    """
    Project a submitted attendance FORM (JSON payload) into the typed tables:
    find-or-create the real ClassSession for (class_group, date, number) —
    the live-only unique constraint guarantees a single session per tuple —
    then upsert one AttendanceRecord per student through bulk_attendance().

    A second submission for the same (group, date, number) therefore UPDATES
    the same session/records instead of silently duplicating them (which the
    pure-JSON world allowed). Missing optional times are tolerated; a wrong
    time on a re-post updates the session window.

    rows: same contract as bulk_attendance ({"student": pk|Person, "status", "note"}).
    Returns {"session_id", **bulk_attendance counters}.
    """
    from apps.academics.models import ClassGroup

    if not ClassGroup.objects.filter(pk=class_group_id, is_deleted=False).exists():
        raise EducationServiceError("کلاس انتخاب‌شده یافت نشد.")
    if not rows:
        raise EducationServiceError("ردیف حضور خالی است.")

    # Serialize concurrent projections for the same tuple; the unique
    # constraint is the final arbiter (transaction + logical lock variant
    # sanctioned by report §5).
    session = (
        ClassSession.objects.select_for_update()
        .filter(
            class_group_id=class_group_id,
            session_date=session_date,
            session_number=session_number,
            is_deleted=False,
        )
        .first()
    )
    if session is None:
        try:
            session = ClassSession.objects.create(
                class_group_id=class_group_id,
                session_number=session_number,
                session_date=session_date,
                start_time=session_start,
                end_time=session_end,
                status=ClassSession.Status.HELD,
            )
        except IntegrityError as exc:
            raise EducationServiceError(
                "جلسه‌ی هم‌کلاس/هم‌تاریخ/هم‌شماره به‌تازگی ثبت شده؛ دوباره تلاش کنید."
            ) from exc
    elif session_start and session_end:
        # Keep the canonical window current with the latest authoritative sheet.
        session.start_time = session_start
        session.end_time = session_end
        session.status = ClassSession.Status.HELD
        session.save(update_fields=["start_time", "end_time", "status", "updated_at"])

    result = bulk_attendance(session=session, rows=rows, recorded_by=actor)
    return {"session_id": str(session.pk), **result}
