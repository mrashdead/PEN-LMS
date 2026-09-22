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

from django.contrib.auth import get_user_model
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsActiveUser
from apps.org import acl_services, services
from apps.forms.permissions import ELEVATED_ROLES

User = get_user_model()


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


# ── Permission management (roles + groups + effective model perms) ────────────

class PermissionDirectoryView(_StaffGate, APIView):
    """GET /api/org/perm/directory/?search= → users to pick (elevated only)."""

    permission_classes = (IsActiveUser,)

    def get(self, request):
        denied = self._deny(request, elevated_only=True)
        if denied:
            return denied
        return Response({"results": services.user_directory(request.query_params.get("search", ""))})


class PermissionOptionsView(_StaffGate, APIView):
    """GET /api/org/perm/options/ → all roles + groups for the editor."""

    permission_classes = (IsActiveUser,)

    def get(self, request):
        denied = self._deny(request, elevated_only=True)
        if denied:
            return denied
        return Response({"roles": services.all_roles(), "groups": services.all_groups()})


class PermissionUserView(_StaffGate, APIView):
    """GET /api/org/perm/user/<uuid>/ → full permission view for one user."""

    permission_classes = (IsActiveUser,)

    def get(self, request, pk):
        denied = self._deny(request, elevated_only=True)
        if denied:
            return denied
        data = services.user_permissions(pk)
        if data is None:
            return Response({"detail": "یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        return Response(data)


class PermissionRolesView(_StaffGate, APIView):
    """POST /api/org/perm/user/<uuid>/roles/ → replace roles (hierarchy-checked)."""

    permission_classes = (IsActiveUser,)

    def post(self, request, pk):
        denied = self._deny(request, elevated_only=True)
        if denied:
            return denied
        codes = (request.data or {}).get("roles") or []
        if isinstance(codes, str):
            codes = [codes]
        try:
            result = services.set_user_roles(user_id=pk, role_codes=codes, actor=request.user)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result)


class PermissionGroupsView(_StaffGate, APIView):
    """POST /api/org/perm/user/<uuid>/groups/ → replace Django groups."""

    permission_classes = (IsActiveUser,)

    def post(self, request, pk):
        denied = self._deny(request, elevated_only=True)
        if denied:
            return denied
        names = (request.data or {}).get("groups") or []
        if isinstance(names, str):
            names = [names]
        try:
            result = services.set_user_groups(user_id=pk, group_names=names, actor=request.user)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result)


# ── Person ACL (manual explicit grants) ────────────────────────────────────────

class AclCatalogView(_StaffGate, APIView):
    """
    GET /api/org/acl/catalog/
    → full catalog: pages + forms (dynamic from DB) + models + verb labels.
    No user context needed; same catalog for everyone.
    """

    permission_classes = (IsActiveUser,)

    def get(self, request):
        denied = self._deny(request, elevated_only=True)
        if denied:
            return denied
        return Response(acl_services.catalog())


class AclDirectoryView(_StaffGate, APIView):
    """GET /api/org/acl/directory/?search= → staff users for the person picker."""

    permission_classes = (IsActiveUser,)

    def get(self, request):
        denied = self._deny(request, elevated_only=True)
        if denied:
            return denied
        q = request.query_params.get("search", "")
        return Response({"results": acl_services.user_directory(q)})


class AclUserView(_StaffGate, APIView):
    """
    GET /api/org/acl/user/<uuid>/
    → all explicit ACL entries for one user + effective-access summary per resource.
    """

    permission_classes = (IsActiveUser,)

    def get(self, request, pk):
        denied = self._deny(request, elevated_only=True)
        if denied:
            return denied
        user = User.objects.filter(pk=pk, is_deleted=False).first()
        if user is None:
            return Response({"detail": "کاربر یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        return Response(acl_services.user_acl_full(user))


class AclGrantView(_StaffGate, APIView):
    """
    PUT /api/org/acl/user/<uuid>/grant/
    Body: {resource_type, resource_key, verbs: []}
    Set the explicit verb list for one (type, key). Atomic + row-locked.
    """

    permission_classes = (IsActiveUser,)

    def put(self, request, pk):
        denied = self._deny(request, elevated_only=True)
        if denied:
            return denied
        user = User.objects.filter(pk=pk, is_deleted=False).first()
        if user is None:
            return Response({"detail": "کاربر یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        payload = request.data or {}
        try:
            resource_type, resource_key, verbs = acl_services.validate_grant_payload(payload)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        try:
            entry = acl_services.grant_verbs(
                user=user,
                resource_type=resource_type,
                resource_key=resource_key,
                verbs=verbs,
                actor=request.user,
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        if entry is None:
            # empty verbs = revoked
            return Response({"ok": True, "entry": None, "message": "ACL entry removed."})
        return Response({
            "ok": True,
            "entry": acl_services.entry_serialize(entry),
        })


class AclRevokeView(_StaffGate, APIView):
    """
    POST /api/org/acl/user/<uuid>/revoke/
    Body: {resource_type, resource_key}
    Soft-delete the ACL entry for one (type, key).
    """

    permission_classes = (IsActiveUser,)

    def post(self, request, pk):
        denied = self._deny(request, elevated_only=True)
        if denied:
            return denied
        user = User.objects.filter(pk=pk, is_deleted=False).first()
        if user is None:
            return Response({"detail": "کاربر یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        payload = request.data or {}
        resource_type = str(payload.get("resource_type", "")).strip()
        resource_key = str(payload.get("resource_key", "")).strip()
        if not resource_type or not resource_key:
            return Response(
                {"error": "resource_type و resource_key الزامی‌اند."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ok = acl_services.revoke(
            user=user,
            resource_type=resource_type,
            resource_key=resource_key,
            actor=request.user,
        )
        return Response({"ok": ok})


class AclBulkView(_StaffGate, APIView):
    """
    POST /api/org/acl/user/<uuid>/bulk/
    Body: {entries: [{resource_type, resource_key, verbs}]}
    Save the entire ACL grid for one user in one transaction.
    Entries with empty verbs are revoked.
    """

    permission_classes = (IsActiveUser,)

    def post(self, request, pk):
        denied = self._deny(request, elevated_only=True)
        if denied:
            return denied
        user = User.objects.filter(pk=pk, is_deleted=False).first()
        if user is None:
            return Response({"detail": "کاربر یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        entries = (request.data or {}).get("entries") or []
        if not isinstance(entries, list):
            return Response(
                {"error": "entries باید لیست باشد."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        errors = []
        results = []
        for i, entry in enumerate(entries):
            try:
                resource_type, resource_key, verbs = acl_services.validate_grant_payload(entry)
            except ValueError as exc:
                errors.append({"index": i, "error": str(exc)})
                continue
            try:
                obj = acl_services.grant_verbs(
                    user=user,
                    resource_type=resource_type,
                    resource_key=resource_key,
                    verbs=verbs,
                    actor=request.user,
                )
                if obj is not None:
                    results.append(acl_services.entry_serialize(obj))
            except Exception as exc:
                errors.append({"index": i, "error": str(exc)})
        return Response({"ok": True, "saved": results, "errors": errors})
