"""
Class-formation layer — the service behind the two pivotal forms.

  Form 1 «برگزاری دوره» (CourseOffering, planning/proposed)
      course + unique code + capacity + proposed jalali start + the course's
      lessons (read-only mirror) + proposed location + proposed weekly
      schedule. Lives in ``CourseOffering``; CRUD via the existing offering
      API. This module only adds the read-model the second form needs.

  Form 2 «تشکیل کلاس» (final execution)
      pick an offering → the proposed place/hours/lessons/teacher auto-fill
      but stay editable (Override) → class code + one lesson + teacher +
      final room + final jalali start + final days/hours → engine produces
      exactly N ``ClassSession`` rows in ONE transaction.

The scheduling math itself lives in ``apps.education.services`` (the single
engine the whole app shares: holiday jumping, push-forward, row-lock
conflict protocol). This module is the thin application layer that maps the
form onto that engine, so the two never drift.

Session-count formula (task §3.الف):

    session_length = end_time - start_time            # e.g. 2h
    total_minutes  = lesson hours for THIS class      # 20h → 1200
    count          = ceil(total_minutes / session_length)   # 10
"""
from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass, field

from django.db import transaction

from apps.core.utils import persian_date, persian_numbers
from apps.education.models import ClassSession, CourseOffering, Lesson
from apps.education.services import (
    EducationServiceError,
    generate_sessions,
)

#: day keys (services._DAY_KEYS) → Persian labels, for the preview table.
DAY_LABELS = {
    "sat": "شنبه", "sun": "یکشنبه", "mon": "دوشنبه", "tue": "سه‌شنبه",
    "wed": "چهارشنبه", "thu": "پنجشنبه", "fri": "جمعه",
}


# ═════════════════════════════════════════════════════════════════════════
# Read model — what the class-formation form pre-fills from an offering
# ═════════════════════════════════════════════════════════════════════════

@dataclass
class LessonOption:
    id: str
    code: str
    title: str
    hours: int
    tuition: int

    def as_dict(self) -> dict:
        return {"id": self.id, "code": self.code, "title": self.title,
                "hours": self.hours, "tuition": self.tuition}


@dataclass
class FormationPrefill:
    """Suggested values for one class inside an offering (form 2 inputs)."""

    offering_id: str
    offering_code: str
    offering_title: str
    course_title: str
    status: str
    capacity: int
    enrolled_count: int
    lessons: list
    location_id: str | None
    location_name: str
    teacher_id: str | None
    teacher_name: str
    start_date: str | None          # jalali, form format
    schedule: dict
    total_hours: int
    suggested_class_code: str
    skip_holidays: bool = True
    duration_hours: int = 0         # selected lesson's own hours (set later)

    def as_dict(self) -> dict:
        return {
            "offering_id": self.offering_id,
            "offering_code": self.offering_code,
            "offering_title": self.offering_title,
            "course_title": self.course_title,
            "status": self.status,
            "capacity": self.capacity,
            "enrolled_count": self.enrolled_count,
            "lessons": [l.as_dict() for l in self.lessons],
            "location": self.location_id,
            "location_name": self.location_name,
            "teacher": self.teacher_id,
            "teacher_name": self.teacher_name,
            "start_date": self.start_date,
            "schedule": self.schedule,
            "total_hours": self.total_hours,
            "suggested_class_code": self.suggested_class_code,
            "skip_holidays": self.skip_holidays,
        }


def formation_prefill(offering: CourseOffering) -> FormationPrefill:
    """
    The offering's PROPOSED values, shaped for the class-formation form.

    Every field the brief lists as "auto-fill but editable" is here: place,
    days+hours, the offering's lesson list (already ordered), the offering's
    instructor and its start date. Nothing is written to the DB.
    """
    links = list(offering.lesson_links)
    lessons = [
        LessonOption(
            id=str(link.lesson_id),
            code=getattr(link.lesson, "code", "") or "",
            title=getattr(link.lesson, "title", "") or "",
            hours=int(link.hours or (link.lesson.duration_hours if link.lesson_id else 0) or 0),
            tuition=int(getattr(link.lesson, "tuition", 0) or 0),
        )
        for link in links if link.lesson_id
    ]
    location = getattr(offering, "location", None)
    teacher = getattr(offering, "instructor", None)
    total_hours = sum(l.hours for l in lessons)
    return FormationPrefill(
        offering_id=str(offering.pk),
        offering_code=offering.code or "",
        offering_title=offering.title or "",
        course_title=getattr(offering.course, "title", "") or "",
        status=offering.status,
        capacity=offering.capacity or 0,
        enrolled_count=offering.enrolled_count or 0,
        lessons=lessons,
        location_id=str(location.pk) if location else None,
        location_name=getattr(location, "name", "") or "",
        teacher_id=str(teacher.pk) if teacher else None,
        teacher_name=(
            f"{teacher.first_name} {teacher.last_name}".strip() if teacher else ""
        ),
        start_date=persian_date(offering.start_date) if offering.start_date else None,
        schedule=dict(offering.schedule or {}),
        total_hours=total_hours,
        suggested_class_code=suggest_class_code(offering),
        skip_holidays=bool(offering.auto_skip_holidays),
    )


def suggest_class_code(offering: CourseOffering) -> str:
    """
    Default کد کلاس for the next class of this offering: CLS-<course code>-NN.

    Scans existing class codes under the offering (soft-deleted included, so
    a retired class code is never recycled into a confusing duplicate).
    """
    course_code = (getattr(offering.course, "code", "") or "COURSE").upper()
    prefix = f"CLS-{course_code}-"
    used = set(
        ClassSession._base_manager
        .filter(offering=offering, class_code__startswith=prefix)
        .values_list("class_code", flat=True)
    )
    n = 1
    while f"{prefix}{n:02d}" in used:
        n += 1
    return f"{prefix}{n:02d}"


# ═════════════════════════════════════════════════════════════════════════
# The formula — duration ÷ session length
# ═════════════════════════════════════════════════════════════════════════

def slot_minutes(schedule: dict) -> int:
    """Minutes per session from {start:'HH:MM', end:'HH:MM'}; 0 when invalid."""
    from apps.education.services import _parse_hhmm

    if not schedule or not schedule.get("start") or not schedule.get("end"):
        return 0
    start = _parse_hhmm(schedule["start"])
    end = _parse_hhmm(schedule["end"])
    if end <= start:
        return 0
    return (
        dt.datetime.combine(dt.date.today(), end)
        - dt.datetime.combine(dt.date.today(), start)
    ).seconds // 60


def derive_session_count(*, total_hours: int, schedule: dict) -> int:
    """
    تعداد جلسات = مدت کل درس ÷ طول هر جلسه (rounded UP — a part-session still
    needs a meeting). 0 when either side is missing; capped at the engine's
    own 200-session ceiling.
    """
    minutes = slot_minutes(schedule)
    total = int(total_hours or 0) * 60
    if minutes <= 0 or total <= 0:
        return 0
    return min(200, max(1, math.ceil(total / minutes)))


# ═════════════════════════════════════════════════════════════════════════
# Command — «تشکیل کلاس»: validate, auto-fill/override, generate
# ═════════════════════════════════════════════════════════════════════════

@dataclass
class ClassFormationInput:
    """Everything the second form submits, already normalized."""

    offering: CourseOffering
    class_code: str
    lesson: Lesson
    teacher: object | None = None
    location: object | None = None
    start_date: dt.date | None = None
    schedule: dict = field(default_factory=dict)
    count: int = 0                 # 0 → derived from lesson hours ÷ slot
    skip_holidays: bool = True
    strict: bool = False
    regenerate: bool = False


def resolve_formation_input(
    *,
    offering: CourseOffering,
    class_code: str,
    lesson,
    teacher=None,
    location=None,
    start_date=None,
    schedule=None,
    count=None,
    skip_holidays=None,
    strict=False,
    regenerate=False,
) -> ClassFormationInput:
    """
    Normalize + validate the form payload, applying the offering's proposed
    values wherever the clerk left a field untouched (that is the Override
    contract: pre-fill happens client-side, defaults are enforced again here
    so a raw API call behaves identically).
    """
    if offering.status == CourseOffering.Status.CANCELLED:
        raise EducationServiceError("این برگزاری لغو شده است.")

    code = (class_code or "").strip()
    if not code:
        code = suggest_class_code(offering)

    # Lesson must belong to the offering's curriculum (form 2 field 3 is
    # filtered by it; the API re-checks).
    lesson_obj = _coerce_lesson(lesson)
    if lesson_obj is None:
        raise EducationServiceError("درس را انتخاب کنید.")
    allowed_ids = set(offering.lesson_links.values_list("lesson_id", flat=True))
    if lesson_obj.pk not in allowed_ids:
        raise EducationServiceError(
            "درس انتخابی در درس‌های این برگزاری تعریف نشده است."
        )

    teacher_obj = teacher if teacher is not None else offering.instructor
    location_obj = location if location is not None else offering.location
    first_date = start_date or offering.start_date
    if not first_date:
        raise EducationServiceError("تاریخ شروع قطعی کلاس را مشخص کنید.")

    sched = dict(schedule or offering.schedule or {})
    days = [d for d in (sched.get("days") or []) if d in DAY_LABELS]
    if not days:
        raise EducationServiceError("روزهای برگزاری هفته را مشخص کنید.")
    sched["days"] = days
    if not sched.get("start") or not sched.get("end"):
        raise EducationServiceError("ساعت شروع و پایان هر جلسه الزامی است.")
    # parse before comparing: string-compare would rank "9:00" after "10:00"
    from apps.education.services import _parse_hhmm
    if _parse_hhmm(str(sched["end"])) <= _parse_hhmm(str(sched["start"])):
        raise EducationServiceError("ساعت پایان باید بعد از شروع باشد.")

    # Hours for THIS lesson inside THIS course (CourseLesson override first).
    link = offering.lesson_links.filter(lesson_id=lesson_obj.pk).first()
    hours = int((link.hours if link and link.hours else lesson_obj.duration_hours) or 0)
    n = int(count or 0)
    if n <= 0:
        n = derive_session_count(total_hours=hours, schedule=sched)
    if n <= 0:
        raise EducationServiceError(
            "تعداد جلسات قابل محاسبه نیست؛ مدت درس یا طول جلسه را وارد کنید."
        )
    if n > 200:
        raise EducationServiceError("تعداد جلسات نمی‌تواند از ۲۰۰ بیشتر باشد.")

    skip = offering.auto_skip_holidays if skip_holidays is None else bool(skip_holidays)

    # Same class code already formed → refuse unless regenerate (the engine
    # would otherwise continue numbering into a duplicate term).
    existing = ClassSession.objects.filter(
        offering=offering, class_code=code, is_deleted=False
    ).count()
    if existing and not regenerate:
        raise EducationServiceError(
            f"کلاس {code} قبلاً {persian_numbers(existing)} جلسه دارد؛ "
            "برای بازسازی «بازتولید جلسات» را فعال کنید."
        )

    return ClassFormationInput(
        offering=offering, class_code=code, lesson=lesson_obj,
        teacher=teacher_obj, location=location_obj, start_date=first_date,
        schedule=sched, count=n, skip_holidays=skip,
        strict=bool(strict), regenerate=bool(regenerate),
    )


def _coerce_lesson(lesson):
    if lesson is None or isinstance(lesson, Lesson):
        return lesson
    try:
        return Lesson.objects.filter(pk=lesson, is_deleted=False).first()
    except Exception:  # bad uuid → ValidationError; treat as "not found"
        return None


class ClassSessionGeneratorService:
    """
    Application service for «تشکیل کلاس» (task §4.1: dedicated scheduling
    layer). One call = one atomic class formation:

        result = ClassSessionGeneratorService(form).run()

    The actual recurrence walk stays in ``services.generate_sessions`` so the
    old offering-level endpoint and this form share one conflict/holiday
    engine. Returns the engine summary plus the resolved class plan.
    """

    def __init__(self, data: ClassFormationInput):
        self.data = data

    @transaction.atomic
    def run(self, *, actor=None) -> dict:
        d = self.data
        result = generate_sessions(
            offering=d.offering,
            actor=actor,
            count=d.count,
            skip_holidays=d.skip_holidays,
            regenerate=d.regenerate,
            strict=d.strict,
            class_code=d.class_code,
            lesson=d.lesson,
            teacher=d.teacher,
            location=d.location,
            schedule=d.schedule,
            start_date=d.start_date,
        )
        result.update({
            "class_code": d.class_code,
            "lesson": {"id": str(d.lesson.pk), "title": d.lesson.title},
            "teacher_id": str(d.teacher.pk) if d.teacher else None,
            "location_id": str(d.location.pk) if d.location else None,
            "start_date": d.start_date.isoformat(),
            "schedule": d.schedule,
            "planned_sessions": d.count,
            "session_minutes": slot_minutes(d.schedule),
            "duration_hours": int(
                (d.lesson.duration_hours or 0)
            ),
        })
        return result


def form_class(*, actor=None, **kwargs) -> dict:
    """Functional entry: validate payload → atomic class formation."""
    offering = kwargs.pop("offering")
    if not isinstance(offering, CourseOffering):
        offering = CourseOffering.objects.filter(pk=offering).first()
    if offering is None:
        raise EducationServiceError("برگزاری دوره یافت نشد.")
    data = resolve_formation_input(offering=offering, **kwargs)
    return ClassSessionGeneratorService(data).run(actor=actor)


# ═════════════════════════════════════════════════════════════════════════
# Dry-run preview — the "پیش‌نمایش جلسات" table (no writes)
# ═════════════════════════════════════════════════════════════════════════

def preview_sessions(
    *,
    offering: CourseOffering,
    lesson,
    schedule: dict,
    start_date=None,
    count: int = 0,
    location=None,
    teacher=None,
    skip_holidays=None,
    window_days: int = 420,
) -> dict:
    """
    Walk the same rule the generator uses and return the planned session rows
    WITHOUT saving, so the form can show «۱۰ جلسه — شنبه ۱۴۰۴/۰۷/۰۱ ۱۶:۰۰ تا
    ۱۸:۰۰ …» before submit. Conflicts are flagged per row (the real run then
    either pushes them a week forward or, with strict=true, aborts).
    """
    from apps.education.services import _DAY_KEYS, _parse_hhmm, holiday_dates, _slot_busy

    data = resolve_formation_input(
        offering=offering, lesson=lesson, schedule=schedule,
        start_date=start_date, count=count, location=location,
        teacher=teacher, skip_holidays=skip_holidays,
        class_code=suggest_class_code(offering),
    )
    sched = data.schedule
    day_offsets = sorted(_DAY_KEYS[d] for d in sched["days"])
    start_t, end_t = _parse_hhmm(sched["start"]), _parse_hhmm(sched["end"])
    horizon_end = data.start_date + dt.timedelta(days=window_days)
    holidays = (
        holiday_dates(start=data.start_date, end=horizon_end, location=data.location)
        if data.skip_holidays else set()
    )

    sessions, jumped = [], []
    number, cursor, guard = 0, data.start_date, 0
    while number < data.count and cursor <= horizon_end and guard < window_days:
        guard += 1
        if cursor.weekday() not in day_offsets:
            cursor += dt.timedelta(days=1)
            continue
        if data.skip_holidays and cursor in holidays:
            jumped.append({"date": cursor.isoformat(), "jalali": persian_date(cursor),
                           "reason": "تعطیلات"})
            cursor += dt.timedelta(days=1)
            continue
        conflict = _slot_busy(
            offering=data.offering, day=cursor, start_t=start_t, end_t=end_t,
            class_code=data.class_code, teacher=data.teacher, location=data.location,
        )
        number += 1
        sessions.append({
            "number": number,
            "date": cursor.isoformat(),
            "jalali": persian_date(cursor),
            "start": sched["start"], "end": sched["end"],
            "location_id": str(data.location.pk) if data.location else None,
            "teacher_id": str(data.teacher.pk) if data.teacher else None,
            "conflict": conflict,
        })
        # same step the engine takes: conflict → +1 week, else → next day
        cursor += dt.timedelta(days=7 if conflict else 1)

    # duration shown = THIS lesson's hours inside THIS course's curriculum
    # (CourseLesson override first) — same source resolve_formation_input used.
    link = offering.lesson_links.filter(lesson_id=data.lesson.pk).first()
    duration = int((link.hours if link and link.hours else data.lesson.duration_hours) or 0)

    return {
        "count": data.count,
        "class_code": data.class_code,
        "lesson": {"id": str(data.lesson.pk), "title": data.lesson.title},
        "session_minutes": slot_minutes(sched),
        "duration_hours": duration,
        "days": sched["days"],
        "start": sched["start"], "end": sched["end"],
        "location_id": str(data.location.pk) if data.location else None,
        "teacher_id": str(data.teacher.pk) if data.teacher else None,
        "sessions": sessions,
        "jumped_holidays": jumped,
        "conflicts": sum(1 for s in sessions if s["conflict"]),
        "holidays": len(jumped),
        "complete": number == data.count,
    }
