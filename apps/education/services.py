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

import datetime as dt
import logging
from typing import Iterable, Optional

from django.db import IntegrityError, models, transaction
from django.db.models import Q

from apps.core.utils import persian_date, persian_numbers
from apps.education.models import (
    AttendanceRecord,
    ClassSession,
    CourseOffering,
    EnrollmentWaitlist,
    GradeRecord,
    OfferingEnrollment,
    SessionScheduleRevision,
)

logger = logging.getLogger(__name__)


class EducationServiceError(Exception):
    """Base error for education services (maps to HTTP 400 at the API edge)."""


class CapacityExceededError(EducationServiceError):
    """ظرفیت برگزاری تکمیل است."""


class ScheduleConflictError(EducationServiceError):
    """تداخل زمانی مدرس/مکان/برگزاری برای این جلسه وجود دارد."""


def _waitlist_student_name(entry) -> str:
    return entry.student.display_name if entry.student_id else "دانش‌آموز"


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
def place_on_waitlist(*, offering: CourseOffering, student, actor=None) -> EnrollmentWaitlist:
    """Place a student in the FIFO queue, idempotently."""
    locked = CourseOffering.objects.select_for_update().get(pk=offering.pk)
    if locked.status not in (CourseOffering.Status.DRAFT, CourseOffering.Status.OPEN):
        raise EducationServiceError("ثبت‌نام یا صف انتظار این برگزاری فعال نیست.")
    existing = EnrollmentWaitlist.objects.filter(
        offering=locked, student=student, is_deleted=False,
        status__in=[EnrollmentWaitlist.Status.WAITING, EnrollmentWaitlist.Status.OFFERED],
    ).first()
    if existing:
        return existing
    return EnrollmentWaitlist.objects.create(offering=locked, student=student)


@transaction.atomic
def promote_next_waitlist(*, offering: CourseOffering, actor=None) -> EnrollmentWaitlist | None:
    """Offer the first waiting student whenever a seat becomes available."""
    locked = CourseOffering.objects.select_for_update().get(pk=offering.pk)
    if not locked.capacity or locked.enrolled_count >= locked.capacity:
        return None
    entry = (
        EnrollmentWaitlist.objects.select_for_update()
        .select_related("student", "student__user")
        .filter(
            offering=locked, status=EnrollmentWaitlist.Status.WAITING,
            is_deleted=False,
        )
        .order_by("requested_at", "created_at")
        .first()
    )
    if entry is None:
        return None
    entry.status = EnrollmentWaitlist.Status.OFFERED
    entry.offered_at = dt.datetime.now(dt.timezone.utc)
    entry.save(update_fields=["status", "offered_at", "updated_at"])
    # Email is best-effort and outside the enrollment transaction. The queue
    # row remains the source of truth when an account has no email.
    recipient = getattr(getattr(entry.student, "user", None), "email", "") or entry.student.email
    if recipient:
        from django.conf import settings
        from django.core.mail import send_mail

        def _notify():
            send_mail(
                subject="یک جای خالی در دورهٔ موردنظر شما ایجاد شد",
                message=(
                    f"سلام {entry.student.display_name}،\n\n"
                    f"در برگزاری «{locked.title or locked.course.title}» یک جای خالی ایجاد شده است. "
                    "لطفاً برای تکمیل ثبت‌نام با آموزشگاه تماس بگیرید."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=True,
            )
        transaction.on_commit(_notify)
    logger.info("waitlist offer %s created for %s (by %s)", entry.pk, _waitlist_student_name(entry), actor)
    return entry


@transaction.atomic
def withdraw_student(*, offering: CourseOffering, actor=None) -> CourseOffering:
    """Decrement the counter symmetrically (never below zero)."""
    locked = CourseOffering.objects.select_for_update().get(pk=offering.pk)
    locked.enrolled_count = max(locked.enrolled_count - 1, 0)
    locked.save(update_fields=["enrolled_count", "updated_at"])
    promote_next_waitlist(offering=locked, actor=actor)
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
    class_code: str = "",
    title: str = "",
    topic: str = "",
    actor=None,
    check_conflicts: bool = True,
) -> ClassSession:
    """
    Create a real session, preventing teacher/room/duplicate class-slot
    double-booking.

    ``class_code`` groups the sessions of one «تشکیل کلاس» (one lesson of the
    offering). Session numbering and the offering-overlap probe are per class
    code, so two classes of the same offering never block each other; room
    and teacher collisions remain global. Empty class_code keeps the legacy
    offering-wide semantics.

    Lock protocol: lock the offering row first (serializes concurrent session
    creation for the same offering), then probe the three conflict dimensions
    with indexed range queries — O(log R + c), not O(E²).
    """
    CourseOffering.objects.select_for_update().get(pk=offering.pk)
    class_code = (class_code or "").strip()

    if session_number is None:
        last = (
            offering.sessions.filter(is_deleted=False, class_code=class_code)
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
            session_date, start_time, end_time,
            offering=offering, class_code=class_code,
        ).exists():
            raise ScheduleConflictError("این کلاس در این بازه جلسه‌ی هم‌پوشان دارد.")

    try:
        session = ClassSession.objects.create(
            offering=offering,
            lesson=lesson,
            class_code=class_code,
            session_number=session_number,
            title=title,
            topic=topic,
            session_date=session_date,
            start_time=start_time,
            end_time=end_time,
            teacher=teacher,
            location=location,
        )
    except IntegrityError as exc:
        # (offering, class_code, session_number) live-unique raced → friendly 400.
        raise EducationServiceError("شماره جلسه تکراری است.") from exc
    logger.info("session %s created for offering %s class %r (by %s)",
                session.pk, offering.pk, class_code, actor)
    return session


@transaction.atomic
def update_session(
    *,
    session: ClassSession,
    actor=None,
    check_conflicts: bool = True,
    **fields,
) -> ClassSession:
    """
    Manually adjust ONE generated session — move its date (a closure day),
    retune its hours, or shift it to another room — without touching the rest
    of the class. Conflict-checked exactly like ``create_session``, minus the
    row itself. Past/held sessions may still be edited (the engine never
    rewrites history automatically); cancelling is done via status.
    """
    allowed = {"session_date", "start_time", "end_time", "teacher", "location",
               "lesson", "title", "topic", "status", "class_code"}
    unknown = set(fields) - allowed
    if unknown:
        raise EducationServiceError(f"فیلد نامعتبر برای ویرایش جلسه: {', '.join(sorted(unknown))}")

    locked = ClassSession.objects.select_for_update().get(pk=session.pk)
    date = fields.get("session_date", locked.session_date)
    start_t = fields.get("start_time", locked.start_time)
    end_t = fields.get("end_time", locked.end_time)
    if end_t <= start_t:
        raise EducationServiceError("ساعت پایان باید بعد از شروع باشد.")
    teacher = fields.get("teacher", locked.teacher)
    location = fields.get("location", locked.location)

    if check_conflicts:
        # the class dimension follows the (possibly new) class code
        class_dim = (fields.get("class_code")
                     if "class_code" in fields else locked.class_code) or ""
        others = Q(offering_id=locked.offering_id, class_code=class_dim)
        if teacher is not None:
            others |= Q(teacher=teacher)
        if location is not None:
            others |= Q(location=location)
        clash = (
            _overlapping(date, start_t, end_t).filter(others)
            .exclude(pk=locked.pk)
        )
        if clash.exists():
            raise ScheduleConflictError(
                "این بازه با جلسهٔ دیگری (اتاق/مدرس/کلاس) تداخل دارد."
            )

    before = {
        "session_date": locked.session_date.isoformat(),
        "start_time": locked.start_time.strftime("%H:%M"),
        "end_time": locked.end_time.strftime("%H:%M"),
        "teacher": str(locked.teacher_id) if locked.teacher_id else None,
        "location": str(locked.location_id) if locked.location_id else None,
        "class_code": locked.class_code or "",
    }
    tracked_changed = any(
        name in fields and fields[name] != getattr(locked, name)
        for name in ("session_date", "start_time", "end_time", "teacher", "location", "class_code")
    )
    for name, value in fields.items():
        setattr(locked, name, value)
    update_fields = ["updated_at"] + [
        name for name in allowed if name in fields
    ]
    locked.save(update_fields=update_fields)
    if tracked_changed:
        after = {
            "session_date": locked.session_date.isoformat(),
            "start_time": locked.start_time.strftime("%H:%M"),
            "end_time": locked.end_time.strftime("%H:%M"),
            "teacher": str(locked.teacher_id) if locked.teacher_id else None,
            "location": str(locked.location_id) if locked.location_id else None,
            "class_code": locked.class_code or "",
        }
        version = (
            SessionScheduleRevision.objects.filter(session=locked, is_deleted=False)
            .order_by("-version").values_list("version", flat=True).first() or 0
        ) + 1
        SessionScheduleRevision.objects.create(
            session=locked, version=version, changed_by=actor,
            before=before, after=after,
            reason=(fields.get("reason") or "").strip() if isinstance(fields.get("reason"), str) else "",
        )
    logger.info("session %s adjusted (fields=%s) by %s",
                locked.pk, sorted(fields), actor)
    return locked


# ─────────────────────────────────────────────────────────────────────────────
# Auto session generation (offering schedule → real sessions)
# ─────────────────────────────────────────────────────────────────────────────

# weekday() Mon=0..Sun=6 → our day keys (Iranian week starts Saturday).
_DAY_KEYS = {"sat": 5, "sun": 6, "mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4}


def _parse_hhmm(text: str) -> dt.time:
    parts = (text or "").strip().split(":")
    return dt.time(int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)


def holiday_dates(*, start: dt.date, end: dt.date, location=None) -> set[dt.date]:
    """
    Non-working dates in [start, end] from the single source of truth,
    ``AcademicHoliday`` — official/institute date ranges plus recurring
    weekly rules (جمعه، و پنجشنبه در مؤسسات دخترانه).

    Whole-day holidays only: a row flagged ``all_day=False`` (a morning
    ceremony) is NOT skipped, because the table carries no clock data and
    silently eating whole sessions is worse than keeping them — those days are
    handled by cancelling individual sessions. Location-scoped rows apply only
    when the same ``location`` is being scheduled.
    """
    from apps.education.models import AcademicHoliday

    loc_q = (
        models.Q(location__isnull=True) | models.Q(location=location)
        if location is not None
        else models.Q(location__isnull=True)
    )
    holidays = AcademicHoliday.objects.filter(
        is_active=True, is_deleted=False, all_day=True,
    ).filter(loc_q)

    out: set[dt.date] = set()
    for hol in holidays:
        if hol.scope == AcademicHoliday.Scope.WEEKLY:
            if hol.weekday is None:
                continue
            cursor = start + dt.timedelta(days=(hol.weekday - start.weekday()) % 7)
            while cursor <= end:
                out.add(cursor)
                cursor += dt.timedelta(days=7)
        else:
            lo = max(hol.date_from, start)
            hi = min(hol.date_to or hol.date_from, end)
            if lo <= hi:
                for offset in range((hi - lo).days + 1):
                    out.add(lo + dt.timedelta(days=offset))
    return out


def is_holiday(day: dt.date, *, location=None) -> bool:
    """Single-date convenience check for manual paths (reports, UI badges)."""
    return day in holiday_dates(start=day, end=day, location=location)


def generate_sessions(
    *,
    offering: CourseOffering,
    actor=None,
    count: Optional[int] = None,
    weeks: Optional[int] = None,
    max_sessions: int = 60,
    skip_holidays: Optional[bool] = None,
    regenerate: bool = False,
    strict: bool = False,
    class_code: str = "",
    lesson=None,
    teacher=None,
    location=None,
    schedule: Optional[dict] = None,
    start_date=None,
) -> dict:
    """
    Materialize ClassSession rows from the offering's recurrence rule
    (``schedule`` {days:[sat..fri], start, end} + ``start_date``).

    Class-formation inputs (the «تشکیل کلاس» form) arrive as overrides —
    ``class_code``/``lesson``/``teacher``/``location``/``schedule``/
    ``start_date`` default to the offering's PROPOSED values, so the old
    generate-sessions endpoint is byte-for-byte unchanged when they are
    omitted.

    Two modes, matching the class-formation form and the legacy hours model:

      count mode (the requested semantics) — ``count`` (or
        ``offering.total_sessions``) > 0: produce EXACTLY that many sessions,
        numbered 1..N contiguously per (offering, class_code) over the next
        valid slots. Holidays are jumped without consuming a number; a slot
        already taken by another class is pushed to the same rule's next
        occurrence and logged in ``pushed``. If N slots cannot be found
        within the scan horizon the whole transaction rolls back and
        ``ScheduleConflictError`` names the blocked dates — the caller never
        receives a half-written term.

      hours mode (legacy default, unchanged semantics) — spread the course's
        total teaching hours across weekly slots until exhausted; conflicts
        are collected in ``skipped`` and a partial schedule still lands.

    ``regenerate=True`` first soft-deletes this offering's FUTURE scheduled
    sessions so re-running the wizard does not collide with its own output
    (past/held sessions are never touched). Returns created/total/pushed/
    skipped/holidays_skipped/until.
    """
    sched = (schedule if schedule is not None else offering.schedule) or {}
    first_date = start_date or offering.start_date
    teacher = teacher if teacher is not None else offering.instructor
    location = location if location is not None else offering.location
    class_code = (class_code or "").strip()
    days = [d for d in (sched.get("days") or []) if d in _DAY_KEYS]
    if not days or not sched.get("start") or not sched.get("end"):
        raise EducationServiceError("برای تولید خودکار، روزها و ساعت شروع/پایان را در «زمان برگزاری» تنظیم کنید.")
    if not first_date:
        raise EducationServiceError("ابتدا تاریخ شروع برگزاری را مشخص کنید.")

    start_t = _parse_hhmm(sched["start"])
    end_t = _parse_hhmm(sched["end"])
    if end_t <= start_t:
        raise EducationServiceError("ساعت پایان باید بعد از شروع باشد.")
    slot_minutes = (dt.datetime.combine(dt.date.today(), end_t)
                    - dt.datetime.combine(dt.date.today(), start_t)).seconds // 60
    if slot_minutes <= 0:
        raise EducationServiceError("بازهٔ زمانی جلسه نامعتبر است.")

    if count is None:
        count = offering.total_sessions or 0
    if skip_holidays is None:
        skip_holidays = offering.auto_skip_holidays
    day_offsets = sorted(_DAY_KEYS[d] for d in days)

    if count and count > 0:
        return _generate_by_count(
            offering=offering, actor=actor, count=count, day_offsets=day_offsets,
            start_t=start_t, end_t=end_t, skip_holidays=skip_holidays,
            regenerate=regenerate, strict=strict,
            class_code=class_code, lesson=lesson, teacher=teacher,
            location=location, start_date=first_date,
        )

    # ── hours mode (legacy) ────────────────────────────────────────────
    # total teaching hours to distribute = sum of the course's lessons' hours
    total_minutes = sum((l.duration_hours or 0) * 60 for l in offering.course.lessons.all())
    if total_minutes <= 0:
        total_minutes = slot_minutes  # at least one session

    cursor = first_date
    # advance to the first scheduled weekday on/after start_date
    while cursor.weekday() not in day_offsets:
        cursor += dt.timedelta(days=1)

    holidays = (
        holiday_dates(start=cursor, end=cursor + dt.timedelta(days=400),
                      location=location)
        if skip_holidays else set()
    )

    created, skipped = 0, []
    remaining = total_minutes
    guard = 0
    last_date = cursor
    while remaining > 0 and created < max_sessions:
        guard += 1
        if guard > 400:  # hard stop for pathological inputs
            break
        if cursor.weekday() in day_offsets:
            if skip_holidays and cursor in holidays:
                skipped.append({"date": cursor.isoformat(), "reason": "تعطیلات"})
            else:
                try:
                    create_session(
                        offering=offering, session_date=cursor,
                        start_time=start_t, end_time=end_t,
                        teacher=teacher, location=location,
                        class_code=class_code, lesson=lesson,
                        title="", actor=actor,
                    )
                    created += 1
                    remaining -= slot_minutes
                    last_date = cursor
                except ScheduleConflictError as exc:
                    skipped.append({"date": cursor.isoformat(), "reason": str(exc)})
                except EducationServiceError as exc:
                    skipped.append({"date": cursor.isoformat(), "reason": str(exc)})
        cursor += dt.timedelta(days=1)
        if weeks and (cursor - first_date).days > weeks * 7:
            break

    return {
        "created": created,
        "skipped": skipped,
        "planned_hours": round(total_minutes / 60, 2),
        "until": last_date.isoformat(),
    }


@transaction.atomic
def _generate_by_count(
    *, offering, actor, count, day_offsets, start_t, end_t,
    skip_holidays, regenerate, strict,
    class_code="", lesson=None, teacher=None, location=None, start_date=None,
) -> dict:
    """
    count-mode engine (doc of ``generate_sessions``). Runs in ONE transaction:
    either exactly ``count`` sessions land (numbered 1..N per class code over
    the next valid slots) or nothing does and the error names every blocked
    date.
    """
    from apps.education.models import ClassSession

    if count > 200:
        raise EducationServiceError("تعداد جلسات نمی‌تواند از ۲۰۰ بیشتر باشد.")

    if regenerate:
        # Drop this class's own FUTURE scheduled sessions so a re-run of the
        # class-formation wizard is idempotent. Held/cancelled history and
        # OTHER classes of the same offering stay untouched.
        today = dt.date.today()
        stale_qs = ClassSession.objects.filter(
            offering=offering, class_code=class_code, is_deleted=False,
            status=ClassSession.Status.SCHEDULED,
            session_date__gte=today,
        )
        for s in stale_qs:
            s.soft_delete()

    # continuation numbering: a second run after a partial term must not
    # restart at 1 (the (offering, class_code, session_number) alive-unique
    # forbids it).
    last_no = (
        ClassSession.objects.filter(
            offering=offering, class_code=class_code, is_deleted=False,
        )
        .order_by("-session_number").values_list("session_number", flat=True).first()
    ) or 0

    if class_code and last_no and not regenerate:
        # Re-forming an already-formed class without regenerate would double
        # the term's sessions under continuation numbering — refuse instead.
        raise EducationServiceError(
            f"کلاس {class_code} قبلاً {persian_numbers(last_no)} جلسه دارد؛ "
            "برای بازسازی، گزینهٔ «بازتولید» را فعال کنید."
        )

    # Holidays need a horizon before we can jump them — 1.5y of scan is plenty
    # for N≤200 twice-a-week terms and keeps the query set-sized.
    horizon_start = start_date or offering.start_date
    horizon_end = horizon_start + dt.timedelta(days=700)
    holidays = (
        holiday_dates(start=horizon_start, end=horizon_end, location=location)
        if skip_holidays else set()
    )

    created, pushed, skipped = 0, [], []
    cursor = horizon_start
    while cursor.weekday() not in day_offsets and cursor <= horizon_end:
        cursor += dt.timedelta(days=1)

    guard_days = 0
    while created < count:
        guard_days += 1
        if cursor > horizon_end or guard_days > 900:
            raise EducationServiceError(
                f"در افق {horizon_end.isoformat()} به تعداد {persian_numbers(count)} "
                "جلسهٔ آزاد نرسیدیم؛ روزها/ساعت را بررسی کنید."
            )
        if cursor.weekday() not in day_offsets:
            cursor += dt.timedelta(days=1)
            continue
        if skip_holidays and cursor in holidays:
            skipped.append({"date": cursor.isoformat(), "reason": "تعطیلات"})
            cursor += dt.timedelta(days=1)
            continue

        occupied = False
        if _slot_busy(offering=offering, day=cursor, start_t=start_t, end_t=end_t,
                      class_code=class_code, teacher=teacher, location=location):
            occupied = True
        if occupied:
            if strict:
                raise ScheduleConflictError(
                    f"تداخل در {persian_date(cursor)} — "
                    "اتاق/مدرس/کلاس در این بازه رزرو است."
                )
            # push forward to the same rule's next occurrence (one week later)
            pushed.append({"from": cursor.isoformat()})
            cursor += dt.timedelta(days=7)
            guard_days += 6
            continue

        try:
            last_no += 1
            create_session(
                offering=offering, session_date=cursor,
                start_time=start_t, end_time=end_t,
                session_number=last_no,
                teacher=teacher, location=location,
                class_code=class_code, lesson=lesson,
                title="", actor=actor,
            )
            created += 1
        except ScheduleConflictError as exc:
            # raced after our probe — roll the whole run (atomic) and report.
            raise ScheduleConflictError(str(exc)) from exc
        cursor += dt.timedelta(days=1)

    # keep the offering's end_date honest (form usually leaves it empty).
    # total_sessions is the offering-WIDE hint: only the legacy (no class
    # code) path may rewrite it — a single class must not clobber it.
    update_fields = []
    if not class_code and offering.total_sessions != count:
        offering.total_sessions = count
        update_fields.append("total_sessions")
    if offering.end_date is None or (offering.end_date and offering.end_date < cursor):
        offering.end_date = min(cursor - dt.timedelta(days=1), horizon_end)
        update_fields.append("end_date")
    if update_fields:
        offering.save(update_fields=update_fields + ["updated_at"])

    return {
        "created": created,
        "total": last_no,
        "pushed": pushed,
        "skipped": skipped,
        "holidays_skipped": len(skipped),
        "until": (cursor - dt.timedelta(days=1)).isoformat(),
    }


def _slot_busy(*, offering, day, start_t, end_t, class_code="", teacher=None, location=None) -> bool:
    """
    Does the slot collide with ANY other live session (class/teacher/room)?

    Built on ``_overlapping`` — the authority's own window semantics (live,
    non-cancelled, half-open overlap) — so the probe can never drift from what
    create_session enforces. Mirrors create_session's guard that a NULL
    teacher/location must not match "all sessions with NULL teacher" via an
    implicit ``= None``. This is a pre-flight optimisation for count-mode
    push-forward; create_session still re-checks under the offering row lock.

    ``class_code`` narrows the offering dimension to the SAME class (sessions
    of sibling classes never block each other — rooms and teachers do).
    """
    dims = Q(offering=offering, class_code=class_code or "")
    if teacher is not None:
        dims |= Q(teacher=teacher)
    if location is not None:
        dims |= Q(location=location)
    return _overlapping(day, start_t, end_t).filter(dims).exists()



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

    from django.core.exceptions import ValidationError

    from apps.core.utils import english_numbers
    from apps.persons.models import Person

    valid_statuses = set(dict(AttendanceRecord.Status.choices))
    created = updated = 0
    seen_ids: list = []
    for row in rows:
        student = row["student"]
        student_id = english_numbers(str(getattr(student, "pk", student))).strip()
        try:
            exists = Person.objects.filter(pk=student_id, is_deleted=False).exists()
        except (ValueError, ValidationError):
            exists = False  # malformed uuid → same friendly error below
        if not exists:
            raise EducationServiceError(
                f"دانش‌آموز {student_id} یافت نشد؛ لطفاً برگه را دوباره بارگذاری کنید."
            )
        status = row.get("status") or AttendanceRecord.Status.PRESENT
        if status not in valid_statuses:
            raise EducationServiceError(
                f"وضعیت نامعتبر حضور: {status} — "
                "مقادیر مجاز: حاضر/غایب/تأخیر/موجه."
            )
        seen_ids.append(student_id)
        _obj, was_created = AttendanceRecord.objects.update_or_create(
            session=session,
            student_id=student_id,
            is_deleted=False,
            defaults={
                "status": status,
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


# ─────────────────────────────────────────────────────────────────────────────
# Teacher portal — roster (students of a class) + descriptive report cards
# ─────────────────────────────────────────────────────────────────────────────

def roster_students(*, offering=None, class_group=None) -> list[dict]:
    """
    Active students of a class, for auto-populating the attendance/report form.

    Union of BOTH enrollment worlds (teacher-portal spec §2.3 — «دانش‌آموزان
    ثبت‌نام‌شده و معتبر آن دوره» is exactly this union):

      * ``academics.ClassEnrollment`` of the given class_group, plus the class
        groups that carry this offering's sessions (the class-formation-form
        bridge — attendance submissions key on (class_group, date, number));
      * ``education.OfferingEnrollment`` — the financial enrollment of the
        offering itself (the course-run world).

    The previous heuristic (most-recent live ClassGroup of the instructor)
    could silently return another class's roster; it is gone. Only active,
    live students come back — [{id, name, student_code}], never more PII.
    """
    from apps.academics.models import ClassEnrollment
    from apps.persons.models import Person

    if offering is None and class_group is None:
        raise EducationServiceError("کلاس یا برگزاری مشخص نیست.")

    student_ids: set = set()
    if class_group is not None:
        student_ids |= set(
            ClassEnrollment.objects.filter(
                class_group=class_group, is_active=True, is_deleted=False
            ).values_list("student_id", flat=True)
        )
    if offering is not None:
        student_ids |= set(
            OfferingEnrollment.objects.filter(
                offering=offering, is_active=True, is_deleted=False
            ).values_list("student_id", flat=True)
        )
        bridged_group_ids = ClassSession.objects.filter(
            offering=offering, is_deleted=False, class_group__isnull=False
        ).values_list("class_group_id", flat=True).distinct()
        if bridged_group_ids:
            student_ids |= set(
                ClassEnrollment.objects.filter(
                    class_group_id__in=bridged_group_ids,
                    is_active=True, is_deleted=False,
                ).values_list("student_id", flat=True)
            )
    if not student_ids:
        return []
    rows = (
        Person.objects.filter(pk__in=student_ids, is_deleted=False)
        .order_by("first_name", "last_name")
    )
    return [
        {
            "id": str(p.pk),
            "name": (p.first_name + " " + p.last_name).strip(),
            "student_code": p.student_code or "",
        }
        for p in rows
    ]


@transaction.atomic
def record_session_attendance(
    *,
    offering: CourseOffering,
    session_date,
    start_time,
    end_time,
    rows: Iterable[dict],
    actor,
    session_id=None,
    session_number: Optional[int] = None,
    lesson=None,
    title: str = "",
    replace: bool = True,
    class_code: str = "",
) -> dict:
    """
    Teacher-portal attendance write — ONE atomic transaction for the whole
    session sheet (task spec §2.5).

    The teacher picks their class, enters the session metadata (Jalali date,
    session number, start/end) and marks each auto-loaded student. This finds
    or creates the real ``ClassSession`` and upserts every ``AttendanceRecord``
    through :func:`bulk_attendance`, all-or-nothing: any row error rolls back
    the session AND every attendance line together.

    Uniqueness (task spec §2.5 — «جلوگیری از ثبت دابلیت برای یک شماره جلسه یا
    یک تاریخ»): for a NEW sheet (no session_id), BOTH dimensions are hard
    rejects —
      * an existing live session with the same (offering, session_number) →
        «شماره جلسه تکراری است» (the DB partial-unique is the final arbiter);
      * an existing live session on the same date → named in the error so the
        teacher edits THAT session instead of stacking a second sheet.
    For an EDIT (session_id given) the date guard excludes the edited session
    itself and a number swap is checked against the constraint via
    IntegrityError. The offering row is locked first (``select_for_update``)
    so two submits for the same class serialize instead of racing.

    ``session_id`` edits an existing session (its number/window are corrected);
    otherwise the sheet creates a session — numbered explicitly, or as
    next-available when omitted. Returns {session_id, session_number,
    created, updated, total}.
    """
    if offering is None:
        raise EducationServiceError("کلاس/برگزاری مشخص نیست.")
    if not rows:
        raise EducationServiceError("فهرست دانش‌آموزان خالی است.")
    if end_time <= start_time:
        raise EducationServiceError("ساعت پایان باید بعد از ساعت شروع باشد.")

    CourseOffering.objects.select_for_update().get(pk=offering.pk)
    class_code = (class_code or "").strip()

    def _live(**f):
        # scoped to THIS class_code: the teacher portal writes class_code=""
        # sessions, which must not collide with a formation-class's numbered
        # 1..N on the same offering (uniqueness is per (offering, class_code,
        # session_number) and, for the date guard, per (offering, class_code)).
        return ClassSession.objects.filter(
            is_deleted=False, offering=offering, class_code=class_code, **f
        )

    session = None
    if session_id:
        # pk is unique — lookup is offering-scoped only; the session's OWN
        # class_code then drives the guards (a formation-class session opened
        # from the portal is edited within its 1..N numbering, not "").
        session = ClassSession.objects.filter(
            is_deleted=False, offering=offering, pk=session_id
        ).first()
        if session is None:
            raise EducationServiceError("جلسه‌ی انتخابی در این کلاس یافت نشد.")
        class_code = session.class_code or ""

    if session is None:
        # New sheet — reject collisions on BOTH number and date (task §2.5).
        # This is a per-CLASS guard, not a room/teacher double-booking check:
        # the sheet records what genuinely happened in THIS class, so it must
        # not be blocked by the teacher's other classes at the same window
        # (that concern belongs to the timetable engine's create_session).
        if session_number is not None and _live(session_number=session_number).exists():
            raise EducationServiceError(
                f"شماره جلسه تکراری است؛ جلسه‌ی شماره {persian_numbers(session_number)} برای این کلاس "
                "از قبل ثبت شده است؛ برای اصلاح همان جلسه را باز کنید."
            )
        clash = _live(session_date=session_date).first()
        if clash is not None:
            raise EducationServiceError(
                f"برای تاریخ {persian_date(session_date)} از قبل جلسه‌ی شماره "
                f"{persian_numbers(clash.session_number)} ثبت شده است؛ یا همان "
                "جلسه را ویرایش کنید یا تاریخ دیگری انتخاب کنید."
            )
        if session_number is None:
            last = (
                _live().order_by("-session_number")
                .values_list("session_number", flat=True).first()
            )
            session_number = (last or 0) + 1
        try:
            session = ClassSession.objects.create(
                offering=offering,
                class_code=class_code,
                lesson=lesson,
                session_number=session_number,
                title=title,
                session_date=session_date,
                start_time=start_time,
                end_time=end_time,
                teacher=offering.instructor,
                location=offering.location,
                status=ClassSession.Status.HELD,
            )
        except IntegrityError as exc:
            raise EducationServiceError("شماره جلسه تکراری است.") from exc
    else:
        if session.status == ClassSession.Status.CANCELLED:
            raise EducationServiceError("این جلسه لغو شده است.")
        other_on_date = _live(session_date=session_date).exclude(pk=session.pk)
        if other_on_date.exists():
            clash = other_on_date.first()
            raise EducationServiceError(
                f"تاریخ {persian_date(session_date)} به جلسه‌ی شماره "
                f"{persian_numbers(clash.session_number)} اختصاص دارد."
            )
        changed: list[str] = []
        if session.session_date != session_date:
            session.session_date = session_date
            changed.append("session_date")
        if session.start_time != start_time:
            session.start_time = start_time
            changed.append("start_time")
        if session.end_time != end_time:
            session.end_time = end_time
            changed.append("end_time")
        if session_number is not None and session.session_number != session_number:
            session.session_number = session_number
            changed.append("session_number")
        if lesson is not None and session.lesson_id != getattr(lesson, "pk", lesson):
            session.lesson = lesson
            changed.append("lesson")
        if title and session.title != title:
            session.title = title
            changed.append("title")
        if session.status != ClassSession.Status.HELD:
            session.status = ClassSession.Status.HELD
            changed.append("status")
        if changed:
            try:
                session.save(update_fields=changed + ["updated_at"])
            except IntegrityError as exc:
                raise EducationServiceError("شماره جلسه تکراری است.") from exc

    counts = bulk_attendance(
        session=session, rows=rows, recorded_by=actor, replace=replace
    )
    return {
        "session_id": str(session.pk),
        "session_number": session.session_number,
        **counts,
    }


def teacher_report_cards(offering: CourseOffering) -> list[dict]:
    """Existing descriptive report cards for one offering, keyed by student id.

    Lets the teacher report-card page pre-fill rows it already saved (so
    reopening a class shows prior decisions rather than blanks). Returns
    [{student, result, teacher_note}].
    """
    rows = GradeRecord.objects.filter(
        offering=offering, session__isnull=True, is_deleted=False
    ).select_related("student")
    return [
        {
            "student": str(g.student_id),
            "result": g.result,
            "teacher_note": g.teacher_note,
        }
        for g in rows
    ]


@transaction.atomic
def save_report_cards(
    *,
    offering: CourseOffering,
    rows: Iterable[dict],
    actor,
    lesson=None,
) -> dict:
    """
    Bulk upsert descriptive report cards for one offering (final evaluation).

    rows: [{"student": pk, "result": passed|failed, "teacher_note": str}]
    Enforces the model rule (failed ⇒ note required) and the live-unique
    (student, offering | session null) constraint via update_or_create, so a
    re-post corrects instead of duplicating. Returns {created, updated}.
    """
    from apps.persons.models import Person

    if offering is None:
        raise EducationServiceError("برگزاری مشخص نیست.")
    created = updated = 0
    seen = set()
    for row in rows:
        student_id = row.get("student")
        result = (row.get("result") or "").strip().lower()
        note = (row.get("teacher_note") or "").strip()
        if not student_id or result not in dict(GradeRecord.Result.choices):
            raise EducationServiceError("هر ردیف باید دانش‌آموز و نتیجهٔ معتبر داشته باشد.")
        if result == GradeRecord.Result.FAILED and not note:
            raise EducationServiceError("برای نتیجهٔ مردود، یادداشت توصیفی الزامی است.")
        if not Person.objects.filter(pk=student_id, is_deleted=False).exists():
            raise EducationServiceError(f"دانش‌آموز نامعتبر: {student_id}")
        if str(student_id) in seen:
            raise EducationServiceError("دانش‌آموز تکراری در فهرست کارنامه.")
        seen.add(str(student_id))
        _obj, was_created = GradeRecord.objects.update_or_create(
            student_id=student_id,
            offering=offering,
            session__isnull=True,
            is_deleted=False,
            defaults={
                "result": result,
                "teacher_note": note,
                "lesson": lesson,
                "evaluated_by": actor,
            },
        )
        created += int(was_created)
        updated += int(not was_created)
    logger.info(
        "report cards for offering %s: %s created / %s updated (by %s)",
        offering.pk, created, updated, actor,
    )
    return {"created": created, "updated": updated}


def _resolve_learner_person(user, student_id=None):
    """
    The student Person whose data a learner-portal caller may read.

    A student gets their OWN person (student_id optional — must match). A
    guardian (والدین) gets one of their ACTIVE wards (student_id required and
    must be in their ward list). Anything else → None (the view 403s). Row
    visibility comes from the StudentGuardian link / own-person identity, never
    from the role code alone (§13 scoping convention).
    """
    from apps.persons.models import Person

    person = getattr(user, "person", None)
    if person is None:
        return None
    roles = set(user.role_codes() if hasattr(user, "role_codes") else set())
    own_id = str(person.pk)
    if "student" in roles and (student_id in (None, "", own_id)):
        return person
    if "guardian" in roles and student_id:
        from apps.academics.scoping import ward_student_ids_for

        if str(student_id) in {str(x) for x in ward_student_ids_for(user)}:
            return Person.objects.filter(pk=student_id, is_deleted=False).first()
    return None


def learner_students(user) -> list[dict]:
    """
    The student(s) whose data this learner-portal user may open.

    Student → just themselves (one row). Guardian → each ACTIVE ward. Powers
    the portal's child switcher so a parent with two students can toggle.
    """
    from apps.academics.scoping import ward_student_ids_for
    from apps.persons.models import Person

    roles = set(user.role_codes() if hasattr(user, "role_codes") else set())
    person = getattr(user, "person", None)
    out: list[dict] = []
    if "student" in roles and person is not None:
        out.append({
            "id": str(person.pk),
            "name": (person.first_name + " " + person.last_name).strip(),
            "student_code": person.student_code or "",
            "relation": "self",
        })
    if "guardian" in roles:
        wards = ward_student_ids_for(user)
        if wards:
            rows = (
                Person.objects.filter(pk__in=wards, is_deleted=False)
                .order_by("first_name", "last_name")
            )
            out.extend({
                "id": str(p.pk),
                "name": (p.first_name + " " + p.last_name).strip(),
                "student_code": p.student_code or "",
                "relation": "ward",
            } for p in rows)
    # de-dupe by id (a person who is both a student and someone's ward)
    seen: set = set()
    uniq = []
    for row in out:
        if row["id"] in seen:
            continue
        seen.add(row["id"])
        uniq.append(row)
    return uniq


def learner_attendance_summary(user, student=None) -> dict:
    """
    Attendance stats + session list for a learner's OWN (or ward's) record.

    ``student`` is a Person already resolved by the caller (see
    ``_resolve_learner_person``); when omitted it falls back to the user's own
    person. Returns {totals:{present,absent,late,excused}, all, rate,
    on_time_rate, sessions:[…]}. Scoped strictly to that one student — never
    another's rows.
    Dates are surfaced as Jalali (۱۴۰۴/…) per the portal spec; ISO kept for
    client-side sorting.
    """
    from apps.core.utils import persian_date

    person = student if student is not None else getattr(user, "person", None)
    empty = {"totals": {}, "all": 0, "rate": 0, "on_time_rate": 0, "sessions": []}
    if person is None:
        return empty
    records = (
        AttendanceRecord.objects.filter(
            student=person, is_deleted=False, session__is_deleted=False
        )
        .select_related("session")
        .order_by("-session__session_date", "-session__start_time")
    )
    totals: dict[str, int] = {}
    sessions = []
    for r in records:
        totals[r.status] = totals.get(r.status, 0) + 1
        sessions.append({
            "date": r.session.session_date.isoformat(),
            "date_jalali": persian_date(r.session.session_date),
            "session_number": r.session.session_number,
            "start": r.session.start_time.strftime("%H:%M"),
            "end": r.session.end_time.strftime("%H:%M"),
            "status": r.status,
            "status_display": dict(AttendanceRecord.Status.choices).get(r.status, r.status),
            "note": r.note,
            "offering": (
                (r.session.offering.title or r.session.offering.course.title)
                if r.session.offering_id and r.session.offering
                else ""
            ),
        })
    all_count = sum(totals.values())
    present = totals.get(AttendanceRecord.Status.PRESENT, 0)
    late = totals.get(AttendanceRecord.Status.LATE, 0)
    on_time_rate = round(present * 100 / all_count) if all_count else 0
    rate = round((present + late) * 100 / all_count) if all_count else 0
    return {
        "totals": {
            "present": totals.get("present", 0),
            "absent": totals.get("absent", 0),
            "late": totals.get("late", 0),
            "excused": totals.get("excused", 0),
        },
        "all": all_count,
        "rate": rate,
        "on_time_rate": on_time_rate,
        "sessions": sessions,
    }


def learner_report_cards(user, student=None) -> list[dict]:
    """Final descriptive report cards for the learner's own (or ward's) record."""
    person = student if student is not None else getattr(user, "person", None)
    if person is None:
        return []
    rows = (
        GradeRecord.objects.filter(
            student=person, is_deleted=False, session__isnull=True
        )
        .select_related("offering", "offering__course", "lesson")
        .order_by("-created_at")
    )
    return [
        {
            "id": str(g.pk),
            "offering": (g.offering.title or (g.offering.course.title if g.offering_id and g.offering.course else "")),
            "lesson": g.lesson.title if g.lesson else "",
            "result": g.result,
            "result_display": dict(GradeRecord.Result.choices).get(g.result, g.result),
            "teacher_note": g.teacher_note,
            "date": g.created_at.date().isoformat(),
        }
        for g in rows
    ]


def teacher_classes(user) -> list[dict]:
    """
    Offerings assigned to this teacher (instructor == their Person) with the
    sessions each one already has. Powers the teacher dashboard and the class
    pickers on the attendance / report-card pages.

    ``sessions`` now spans BOTH directions — past (so the attendance page can
    list and edit recorded sheets) and upcoming — newest-first is wrong for a
    class picker, so rows are chronological and capped; ``stats`` carries the
    per-class rollups (total / held / recorded / not-held / upcoming / next)
    the dashboard cards show. roster_size comes from ONE grouped count, not
    per-class queries.
    """
    from django.db.models import Count

    person = getattr(user, "person", None)
    if person is None:
        return []
    offerings = list(
        CourseOffering.objects.filter(
            instructor=person, is_deleted=False, is_active=True
        )
        .select_related("course", "location")
        .order_by("-start_date", "-created_at")
    )
    if not offerings:
        return []
    today = dt.date.today()
    offering_ids = [o.pk for o in offerings]

    sessions_qs = (
        ClassSession.objects.filter(
            offering_id__in=offering_ids, is_deleted=False
        )
        .exclude(status=ClassSession.Status.CANCELLED)
        .annotate(recorded=Count("attendances", filter=Q(attendances__is_deleted=False)))
        .order_by("session_date", "start_time")
    )
    sessions_by_offering: dict = {}
    for s in sessions_qs:
        sessions_by_offering.setdefault(str(s.offering_id), []).append(s)

    roster_sizes = {
        str(r["offering_id"]): r["n"]
        for r in OfferingEnrollment.objects.filter(
            offering_id__in=offering_ids, is_active=True, is_deleted=False
        ).values("offering_id").annotate(n=Count("id"))
    }

    out = []
    for o in offerings:
        rows = sessions_by_offering.get(str(o.pk), [])
        past = [s for s in rows if s.session_date < today]
        upcoming = [s for s in rows if s.session_date >= today][:6]
        # chronological window around "now": last 6 past + next 6 upcoming
        visible = past[-6:] + upcoming
        out.append({
            "id": str(o.pk),
            "title": o.title or (o.course.title if o.course_id else ""),
            "course": o.course.title if o.course_id else "",
            "location": o.location.name if o.location_id else "",
            "schedule": o.schedule or {},
            "capacity": o.capacity,
            "enrolled_count": o.enrolled_count,
            "roster_size": roster_sizes.get(str(o.pk), 0),
            "start_date": o.start_date.isoformat() if o.start_date else "",
            "status": o.status,
            "stats": {
                "total": len(rows),
                "held": sum(1 for s in rows if s.status == ClassSession.Status.HELD),
                "recorded": sum(1 for s in rows if s.recorded > 0),
                "not_recorded": sum(1 for s in rows if s.recorded == 0),
                "upcoming": len(upcoming),
                "next": upcoming[0].session_date.isoformat() if upcoming else "",
            },
            "sessions": [
                {
                    "id": str(s.pk),
                    "number": s.session_number,
                    "topic": s.topic or "",
                    "date": s.session_date.isoformat(),
                    "date_jalali": persian_date(s.session_date),
                    "start": s.start_time.strftime("%H:%M"),
                    "end": s.end_time.strftime("%H:%M"),
                    "status": s.status,
                    "recorded": s.recorded,
                    "past": s.session_date < today,
                }
                for s in visible
            ],
        })
    return out
