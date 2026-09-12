"""
Organizational API (read-models + delegation).

  GET  /api/org/chart/                 → clickable org tree + departments
  GET  /api/org/profile/<uuid>/         → one user's org profile
  GET  /api/org/permissions/matrix/     → group × resource × verb matrix
  POST /api/org/permissions/simulate/   → {user, resource, verb} → verdict+why
  GET  /api/org/responsibilities/       → who approves what (from Transitions)
  GET  /api/org/performance/units/      → per-department SLA/throughput
  GET  /api/org/delegations/            → list
  POST /api/org/delegations/            → create (elevated only)
  POST /api/org/delegations/{id}/revoke/→ revoke (elevated only)

Read endpoints: any authenticated staff (chart/profile/matrix are org
structure, not PII). Delegation writes + the simulator are elevated-role only
(the simulator reveals effective access, so it's gated like an admin tool).
"""
from __future__ import annotations

from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsActiveUser
from apps.org import services
from apps.forms.permissions import ELEVATED_ROLES


class _StaffGate:
    def _deny(self, request, elevated_only=False):
        roles = set(request.user.role_codes()) if hasattr(request.user, "role_codes") else set()
        allowed = (roles & ELEVATED_ROLES) if elevated_only else (roles & services.STAFF)
        if not allowed:
            return Response(
                {"detail": "دسترسی به اطلاعات سازمانی محدود است."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return None


class OrgChartView(_StaffGate, APIView):
    permission_classes = (IsActiveUser,)

    def get(self, request):
        denied = self._deny(request)
        if denied:
            return denied
        return Response({
            "chart": services.org_chart(),
            "departments": services.departments(),
        })


class OrgProfileView(_StaffGate, APIView):
    permission_classes = (IsActiveUser,)

    def get(self, request, pk):
        denied = self._deny(request)
        if denied:
            return denied
        profile = services.person_profile(pk)
        if profile is None:
            return Response({"detail": "یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        return Response(profile)


class PermissionMatrixView(_StaffGate, APIView):
    permission_classes = (IsActiveUser,)

    def get(self, request):
        denied = self._deny(request, elevated_only=True)
        if denied:
            return denied
        return Response(services.permission_matrix())


class AccessSimulatorView(_StaffGate, APIView):
    permission_classes = (IsActiveUser,)

    def post(self, request):
        denied = self._deny(request, elevated_only=True)
        if denied:
            return denied
        payload = request.data or {}
        user_id = payload.get("user")
        resource = payload.get("resource")
        verb = payload.get("verb")
        if not (user_id and resource and verb):
            return Response(
                {"error": "user، resource و verb الزامی هستند."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(services.simulate_access(user_id, resource, verb))


class ResponsibilitiesView(_StaffGate, APIView):
    permission_classes = (IsActiveUser,)

    def get(self, request):
        denied = self._deny(request)
        if denied:
            return denied
        return Response({"results": services.responsibilities()})


class UnitPerformanceView(_StaffGate, APIView):
    permission_classes = (IsActiveUser,)

    def get(self, request):
        denied = self._deny(request)
        if denied:
            return denied
        return Response({"results": services.unit_performance()})


class DelegationListCreateView(_StaffGate, APIView):
    permission_classes = (IsActiveUser,)

    def get(self, request):
        denied = self._deny(request)
        if denied:
            return denied
        return Response({"results": services.list_delegations()})

    def post(self, request):
        denied = self._deny(request, elevated_only=True)
        if denied:
            return denied
        payload = request.data or {}
        valid_from = parse_datetime(str(payload.get("valid_from") or ""))
        valid_to = parse_datetime(str(payload.get("valid_to") or ""))
        if not (payload.get("principal") and payload.get("delegate") and valid_from and valid_to):
            return Response(
                {"error": "principal، delegate، valid_from و valid_to (ISO) الزامی‌اند."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            d = services.create_delegation(
                principal_id=payload["principal"], delegate_id=payload["delegate"],
                department=payload.get("department", ""),
                workflow_code=payload.get("workflow_code", ""),
                reason=payload.get("reason", ""),
                valid_from=valid_from, valid_to=valid_to, actor=request.user,
            )
        except Exception as exc:  # ValidationError surfaces field messages
            msg = getattr(exc, "message_dict", None) or str(exc)
            return Response({"error": msg}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"id": str(d.pk)}, status=status.HTTP_201_CREATED)


class DelegationRevokeView(_StaffGate, APIView):
    permission_classes = (IsActiveUser,)

    def post(self, request, pk):
        denied = self._deny(request, elevated_only=True)
        if denied:
            return denied
        ok = services.revoke_delegation(delegation_id=pk, actor=request.user)
        if not ok:
            return Response({"detail": "جانشینی یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"ok": True})
