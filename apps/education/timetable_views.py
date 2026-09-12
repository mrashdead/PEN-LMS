"""
Daily timetable endpoint — the read model the UI grid consumes.

GET /api/education/timetable/?date=YYYY-MM-DD

Response:
  {
    "date": "YYYY-MM-DD",
    "hours": ["08:00", "09:00", …],          # grid columns (1h each)
    "locations": [{id, name, building}, …],  # grid rows, ordered
    "blocks": [{                              # placements (colspan computed client-side too)
       "session_id", "location_id", "start", "end",
       "lesson_title", "lesson_code", "offering_title",
       "teacher_name", "status", "class_group"
    }, …]
  }

Read-only; visibility mirrors education_sessions_visible_to (teachers see
their own sessions, managers everything). Data is derived in ONE pass with
select_related — no N+1.
"""
from __future__ import annotations

import datetime

from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsActiveUser
from apps.academics.scoping import education_sessions_visible_to
from apps.education.models import Location


class TimetableView(APIView):
    permission_classes = (IsActiveUser,)

    DEFAULT_START = 8   # 08:00
    DEFAULT_END = 21    # last hour slot start

    def get(self, request):
        # ── date param (ISO; jalali strings are rejected by strptime → 400) ──
        raw = (request.query_params.get("date") or "").strip()
        try:
            day = datetime.date.fromisoformat(raw) if raw else timezone.localdate()
        except ValueError:
            return Response(
                {"date": "قالب تاریخ نامعتبر است (YYYY-MM-DD)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sessions = (
            education_sessions_visible_to(request.user)
            .filter(session_date=day, is_deleted=False)
            .exclude(status="cancelled")
            .select_related("lesson", "teacher", "location", "offering", "offering__course")
        )

        # ── locations: rows of the grid ────────────────────────────────
        locations = list(
            Location.objects.filter(is_active=True, is_deleted=False)
            .order_by("name")
            .values("id", "name", "building")
        )
        location_ids = {str(l["id"]) for l in locations}

        # ── grid window: explicit params, else data-driven bounds ──────
        try:
            start_h = int(request.query_params.get("start_hour", self.DEFAULT_START))
            end_h = int(request.query_params.get("end_hour", self.DEFAULT_END))
        except (TypeError, ValueError):
            start_h, end_h = self.DEFAULT_START, self.DEFAULT_END
        start_h = max(0, min(start_h, 23))
        end_h = max(start_h + 1, min(end_h, 24))

        # widen the window to include every session found that day
        for s in sessions:
            start_h = min(start_h, s.start_time.hour)
            end_h = max(end_h, min(s.end_time.hour + (1 if s.end_time.minute else 0), 24))

        hours = [f"{h:02d}:00" for h in range(start_h, end_h)]

        # ── blocks ─────────────────────────────────────────────────────
        blocks = []
        for s in sessions:
            loc_id = str(s.location_id) if s.location_id else None
            blocks.append({
                "session_id": str(s.pk),
                "location_id": loc_id,
                "start": s.start_time.strftime("%H:%M"),
                "end": s.end_time.strftime("%H:%M"),
                "lesson_title": s.lesson.title if s.lesson else (s.title or ""),
                "lesson_code": s.lesson.code if s.lesson else "",
                "offering_title": (
                    s.offering.title or s.offering.course.title
                    if s.offering and s.offering.course else (s.offering.title if s.offering else "")
                ),
                "teacher_name": (
                    f"{s.teacher.first_name} {s.teacher.last_name}".strip()
                    if s.teacher else ""
                ),
                "status": s.status,
                "class_group": str(s.class_group_id) if s.class_group_id else "",
            })
        blocks.sort(key=lambda b: (b["location_id"] or "", b["start"]))

        return Response({
            "date": day.isoformat(),
            "hours": hours,
            "locations": locations,
            "blocks": blocks,
        })
