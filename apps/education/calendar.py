"""
Role-based calendar read-models — three perspectives over ONE dataset.

The requirement: staff, teachers and students/parents must not share one
"calendar blob". Each perspective answers a different question, and — crucially
— each is scoped by a DIFFERENT relation:

    resource_timeline(user, day)   "کدام اتاق، کی، با کدام کلاس/استاد؟"
        → every live session of the day, grouped BY LOCATION (rooms as rows).
        Staff/manager perspective for physical-infrastructure management.

    teacher_schedule(user, ...)    "کلاس‌های خودم + لینک حضوروغیاب هر جلسه"
        → sessions where teacher == user's Person, each carrying the URL of
        the attendance page for THAT session.

    student_schedule(user, ...)    "فقط کلاس‌هایی که قطعی ثبت‌نام کرده‌ام"
        → sessions whose class group / offering has an ACTIVE enrollment for
        the student (or for a guardian: each of their wards, labelled).

All three go through apps.academics.scoping where an underlying queryset
already exists, so a view can never forget the DataScope rule (that was the
B-round's whole point). These functions are pure read selectors — no writes,
no side effects — returning plain JSON-ready dicts.
"""
from __future__ import annotations

import datetime as dt
from typing import Optional

from django.db.models import Q

from apps.core.utils import jalali_date_str
from apps.academics.scoping import (
    _person_of,
    _roles_of,
    education_sessions_visible_to,
    ward_student_ids_for,
)

# ── shared helpers ───────────────────────────────────────────────────────────

def _parse_range(query_params) -> tuple[dt.date, dt.date]:
    """?from=YYYY-MM-DD&to=YYYY-MM-DD (default: today..+14d); ?date= → one day."""
    today = dt.date.today()
    single = (query_params.get("date") or "").strip()
    raw_from = (query_params.get("from") or "").strip()
    raw_to = (query_params.get("to") or "").strip()
    try:
        if single:
            start = end = dt.date.fromisoformat(single)
        else:
            start = dt.date.fromisoformat(raw_from) if raw_from else today
            end = dt.date.fromisoformat(raw_to) if raw_to else start + dt.timedelta(days=14)
    except ValueError as exc:
        raise ValueError("قالب تاریخ باید YYYY-MM-DD باشد.") from exc
    if end < start:
        start, end = end, start
    if (end - start).days > 92:
        raise ValueError("بازه‌ی تقویم نمی‌تواند بیش از ۹۲ روز باشد.")
    return start, end


def _session_row(s, *, attendance_url_base: str = "", extra: Optional[dict] = None) -> dict:
    """One session → the JSON shape all three calendars share (plus extras).

    Dates ship BOTH formats (the repo convention is full Jalali UX, but the
    resource grid's JS sorts on the ISO key): ``date`` = ISO gregorian for
    ordering/filtering, ``date_jalali`` = ۱۴۰۵/۰۷/۱۱ for display.
    """
    from apps.core.utils import jalali_date_str

    row = {
        "id": str(s.pk),
        "number": s.session_number,
        "date": s.session_date.isoformat(),
        "date_jalali": jalali_date_str(s.session_date),
        "start": s.start_time.strftime("%H:%M"),
        "end": s.end_time.strftime("%H:%M"),
        "status": s.status,
        "title": s.title or (
            s.lesson.title if s.lesson_id
            else (s.offering.title or (s.offering.course.title if s.offering and s.offering.course_id else ""))
            if s.offering_id
            else (s.class_group.name if s.class_group_id else "")
        ),
        "topic": s.topic or "",
        "teacher": s.teacher.display_name if s.teacher_id else "",
        "location": s.location.name if s.location_id else "",
        "location_id": str(s.location_id) if s.location_id else None,
        "schedule_version": s.schedule_revisions.filter(is_deleted=False).count() + 1,
        "schedule_updated_at": (
            (s.schedule_revisions.filter(is_deleted=False).order_by("-version").first() or s).updated_at.isoformat()
            if getattr(s, "updated_at", None) else ""
        ),
        "materials": [
            {
                "id": str(m.pk), "title": m.title, "kind": m.kind,
                "url": m.public_url,
            }
            for m in s.materials.filter(is_deleted=False, is_visible=True).order_by("sort_order", "created_at")
        ],
    }
    if attendance_url_base:
        # deep link the teacher's calendar into the per-session attendance form
        row["attendance_url"] = f"{attendance_url_base}?session={s.pk}"
    if extra:
        row.update(extra)
    return row


def _live_sessions(start: dt.date, end: dt.date):
    from apps.education.models import ClassSession

    return (
        ClassSession.objects.filter(
            session_date__gte=start, session_date__lte=end, is_deleted=False,
        )
        .exclude(status="cancelled")
        .select_related("lesson", "teacher", "location", "offering",
                        "offering__course", "class_group")
        .order_by("session_date", "start_time", "location__name")
    )


# ── 1) staff: resource / room master calendar ───────────────────────────────

def resource_timeline(user, *, start: dt.date, end: dt.date) -> dict:
    """
    Rooms-as-rows occupancy view (employee/manager infrastructure console).

    Only managers/HR/workflow_admin/employees reach this selector — the view
    checks the role first. Every live session in range appears under its
    location; sessions without a location land in a synthetic «بدون فضا» row
    so an unassigned room is VISIBLE as a problem instead of vanishing.

    Also returns ``holidays`` in range (from the same AcademicHoliday source
    the generator uses) so the grid can grey out closed days.
    """
    from apps.education.services import holiday_dates

    sessions = list(_live_sessions(start, end))

    locations: dict[str, dict] = {}
    per_day_utilization: dict[str, int] = {}
    for s in sessions:
        key = str(s.location_id) if s.location_id else "__none__"
        loc = locations.setdefault(key, {
            "id": None if key == "__none__" else key,
            "name": s.location.name if s.location_id else "بدون فضا",
            "building": s.location.building if s.location_id else "",
            "capacity": s.location.capacity if s.location_id else 0,
            "sessions": [],
        })
        loc["sessions"].append(_session_row(s, extra={"teacher_id": str(s.teacher_id) if s.teacher_id else None}))
        per_day_utilization[s.session_date.isoformat()] = per_day_utilization.get(s.session_date.isoformat(), 0) + 1

    # Institute-wide closures only (location=None): room-specific maintenance
    # days are already visible as empty rows on that room's timeline.
    holidays = sorted(d.isoformat() for d in holiday_dates(start=start, end=end))

    return {
        "range": {"from": start.isoformat(), "to": end.isoformat()},
        "locations": list(locations.values()),
        "per_day": per_day_utilization,
        "holidays": holidays,
        "unassigned": sum(
            1 for s in sessions if s.location_id is None
        ),
    }


# ── 2) teacher: own schedule with attendance links ──────────────────────────

def teacher_schedule(user, *, start: dt.date, end: dt.date) -> dict:
    """
    The teacher's own classes, each session carrying its attendance deep link.

    Strictly teacher==person — NOT education_sessions_visible_to (which also
    returns students' rows for a dual-persona user; a teacher-calendar mixing
    someone else's class would defeat the "no confusion" requirement).
    """
    person = _person_of(user)
    if person is None:
        return {"range": {"from": start.isoformat(), "to": end.isoformat()},
                "sessions": [], "by_offering": []}

    from apps.education.models import ClassSession

    sessions = (
        ClassSession.objects.filter(
            teacher=person, session_date__gte=start, session_date__lte=end,
            is_deleted=False,
        )
        .exclude(status="cancelled")
        .select_related("lesson", "location", "offering", "offering__course", "class_group")
        .order_by("session_date", "start_time")
    )
    rows = [_session_row(s, attendance_url_base="/workspace/teacher/attendance/") for s in sessions]

    # next session per offering — powers "کلاس بعدی من" cards + quick links
    by_offering: dict[str, dict] = {}
    for s in sessions:
        if s.offering_id is None:
            continue
        key = str(s.offering_id)
        if key not in by_offering:
            by_offering[key] = {
                "offering_id": key,
                "offering": s.offering.title or (
                    s.offering.course.title if s.offering.course_id else ""
                ),
                "next": _session_row(s, attendance_url_base="/workspace/teacher/attendance/"),
            }
    return {
        "range": {"from": start.isoformat(), "to": end.isoformat()},
        "sessions": rows,
        "by_offering": list(by_offering.values()),
    }


# ── 3) student / guardian: only confirmed enrollments ───────────────────────

def student_schedule(user, *, start: dt.date, end: dt.date) -> dict:
    """
    Lean learner calendar. Rule: a session appears ONLY if the student's
    enrollment is active (class-group world: ClassEnrollment; course-run
    world: OfferingEnrollment). A guardian sees the same rows per ward, each
    tagged with the ward's name — never a merged soup.

    Dual-persona users (someone who teaches AND was a student) get the union,
    which is exactly what "their enrollments" means for them; the teacher
    calendar stays separate.
    """
    person = _person_of(user)
    roles = _roles_of(user)
    if person is None:
        # Without a Person row there is no enrollment identity to scope by —
        # a student/guardian role code alone must never surface rows.
        return {"range": {"from": start.isoformat(), "to": end.isoformat()}, "days": []}

    # targets: person → label mapping (self for students, wards for guardians)
    targets: list[tuple[object, str]] = []
    if "student" in roles:
        targets.append((person, ""))
    labelled = False  # ward rows must carry the parent's child-name context
    if "guardian" in roles:
        from apps.persons.models import Person

        wards = Person.objects.filter(
            pk__in=ward_student_ids_for(user), is_deleted=False
        )
        for w in wards:
            targets.append((w, w.display_name))
            labelled = True
    if not targets:
        return {"range": {"from": start.isoformat(), "to": end.isoformat()}, "days": []}

    from apps.education.models import ClassSession

    cond = Q()
    for student, _label in targets:
        cond |= Q(
            class_group__enrollments__student=student,
            class_group__enrollments__is_active=True,
            class_group__enrollments__is_deleted=False,
        )
        cond |= Q(
            offering__enrollments__student=student,
            offering__enrollments__is_active=True,
            offering__enrollments__is_deleted=False,
        )
    sessions = (
        ClassSession.objects.filter(cond, session_date__gte=start,
                                    session_date__lte=end, is_deleted=False)
        .exclude(status="cancelled")
        .select_related("lesson", "teacher", "location", "offering",
                        "offering__course", "class_group")
        .distinct()
        .order_by("session_date", "start_time")
    )

    # Which ward justifies each row — so a parent of two students can tell
    # whose class this is. Only guardians pay for the extra per-row probes.
    days: dict[str, list] = {}
    for s in sessions:
        label = ""
        if labelled:
            for student, lab in targets:
                if not lab:
                    continue
                if (s.offering_id and _enrolled_offering(student, s.offering_id)) or (
                    s.class_group_id and _enrolled_group(student, s.class_group_id)
                ):
                    label = lab
                    break
        days.setdefault(s.session_date.isoformat(), []).append(
            _session_row(s, extra={"ward": label})
        )
    return {
        "range": {"from": start.isoformat(), "to": end.isoformat()},
        "days": [
            {
                "date": d,
                "date_jalali": jalali_date_str(dt.date.fromisoformat(d)),
                "sessions": rows,
            }
            for d, rows in sorted(days.items())
        ],
    }


def _enrolled_offering(student, offering_id) -> bool:
    from apps.education.models import OfferingEnrollment

    return OfferingEnrollment.objects.filter(
        student=student, offering_id=offering_id,
        is_active=True, is_deleted=False,
    ).exists()


def _enrolled_group(student, group_id) -> bool:
    from apps.academics.models import ClassEnrollment

    return ClassEnrollment.objects.filter(
        student=student, class_group_id=group_id,
        is_active=True, is_deleted=False,
    ).exists()


# ── perspective router (used by /calendar/me/) ──────────────────────────────

def my_schedule(user, *, start: dt.date, end: dt.date) -> dict:
    """
    One endpoint, correct perspective per role — the view layer picks by
    presence of the role code, and a dual-role user gets BOTH sections
    (teacher block + learner block) since they genuinely live two schedules.
    """
    roles = _roles_of(user)
    out: dict = {"range": {"from": start.isoformat(), "to": end.isoformat()},
                 "perspectives": []}
    if "teacher" in roles:
        out["perspectives"].append("teacher")
        out["teacher"] = teacher_schedule(user, start=start, end=end)
    if roles & {"student", "guardian"}:
        out["perspectives"].append("learner")
        out["learner"] = student_schedule(user, start=start, end=end)
    if not out["perspectives"]:
        # staff/manager without teaching: fall back to the full visible scope,
        # read-only (TimetableView is their richer console anyway).
        sessions = [
            _session_row(s)
            for s in education_sessions_visible_to(user).filter(
                session_date__gte=start, session_date__lte=end,
            ).exclude(
                status="cancelled"
            ).order_by("session_date", "start_time")
        ]
        out["perspectives"].append("staff")
        out["sessions"] = sessions
    return out
