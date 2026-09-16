"""
Role-based calendar endpoints (read-models live in apps/education/calendar.py).

    GET /api/education/calendar/resources/?date=… | ?from=…&to=…
        staff/manager room-occupancy master view.
    GET /api/education/calendar/me/?date=… | ?from=…&to=…
        perspective router: teacher schedule (+attendance links) and/or the
        learner's confirmed-enrollment calendar; staff fall back to scope.

APIView + no queryset → deliberately NO StrictDjangoModelPermissions (the
queryset-less-APIView pitfall would 403/500 everyone); authorization is the
role class plus the selectors' row-scoping.
"""
from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.academics.scoping import ELEVATED_ROLES
from apps.core.permissions import IsActiveUser
from apps.education.calendar import (
    _parse_range,
    my_schedule,
    resource_timeline,
)

STAFF_ROLES = ELEVATED_ROLES | {"employee", "teacher", "supervisor"}


class ResourceCalendarView(APIView):
    """Rooms-as-rows occupancy for the staff infrastructure console."""

    permission_classes = (IsActiveUser, IsAuthenticated)

    def get(self, request):
        roles = set(request.user.role_codes())
        if not (roles & STAFF_ROLES):
            return Response(
                {"error": "نمای منابع فقط برای کارکنان است."},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            start, end = _parse_range(request.query_params)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(resource_timeline(request.user, start=start, end=end))


class MyCalendarView(APIView):
    """The signed-in user's own calendar — perspective chosen by their roles."""

    permission_classes = (IsActiveUser, IsAuthenticated)

    def get(self, request):
        try:
            start, end = _parse_range(request.query_params)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(my_schedule(request.user, start=start, end=end))
