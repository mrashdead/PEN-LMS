"""
Call-log API — mounted under /api/calls/.

Thin HTTP layer over the calls service; row scope comes from
``calls_visible_to`` (elevated roles see everything, other operators see the
calls they received or are responsible for).
"""
from __future__ import annotations

from rest_framework import generics, status
from rest_framework.permissions import SAFE_METHODS
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsActiveUser
from apps.calls.models import CallSubject, InboundCall
from apps.calls.permissions import CanAccessCalls
from apps.calls.selectors import (
    CallFilters,
    CallReportError,
    calls_report,
)
from apps.calls.serializers import (
    CallCreateSerializer,
    CallSubjectSerializer,
    FollowUpSerializer,
    InboundCallSerializer,
)
from apps.calls.services import (
    CallServiceError,
    InvalidTransitionError,
    calls_visible_to,
    log_call,
    update_follow_up,
)


class CallListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/calls/  — لیست تماس‌ها (دامنه: calls_visible_to)
    POST /api/calls/  — ثبت تماس
    """

    permission_classes = (IsActiveUser, CanAccessCalls)
    queryset = InboundCall.objects.none()

    def get_serializer_class(self):
        return InboundCallSerializer if self.request.method == "GET" else CallCreateSerializer

    def get_queryset(self):
        qs = calls_visible_to(self.request.user)
        params = self.request.query_params
        if params.get("from"):
            from apps.calls.selectors import CallReportError, _parse_datetime
            try:
                qs = qs.filter(called_at__date__gte=_parse_datetime(params["from"]))
            except CallReportError as exc:
                raise ValidationError({"from": str(exc)}) from exc
        if params.get("to"):
            from apps.calls.selectors import CallReportError, _parse_datetime
            try:
                qs = qs.filter(called_at__date__lte=_parse_datetime(params["to"]))
            except CallReportError as exc:
                raise ValidationError({"to": str(exc)}) from exc
        result = (params.get("result") or "").strip().lower()
        if result:
            qs = qs.filter(result=result)
        follow_up = (params.get("follow_up_status") or "").strip().lower()
        if follow_up:
            qs = qs.filter(follow_up_status=follow_up)
        needs = (params.get("needs_follow_up") or "").strip().lower() in {"1", "true", "yes"}
        if needs:
            from apps.calls.models import FollowUpStatus

            qs = qs.filter(follow_up_status__in=[FollowUpStatus.PENDING, FollowUpStatus.IN_PROGRESS])
        receiver = (params.get("receiver") or "").strip()
        if receiver:
            qs = qs.filter(receiver_id=receiver)
        subject = (params.get("subject") or "").strip()
        if subject:
            qs = qs.filter(subject__icontains=subject)
        subject_ref = (params.get("subject_ref") or "").strip()
        if subject_ref:
            qs = qs.filter(subject_ref_id=subject_ref)
        search = (params.get("search") or "").strip()
        if search:
            from django.db.models import Q

            qs = qs.filter(
                Q(caller_name__icontains=search)
                | Q(caller_phone__icontains=search)
                | Q(subject__icontains=search)
                | Q(description__icontains=search)
            )
        return qs.order_by("-called_at", "-pk")

    def create(self, request, *args, **kwargs):
        serializer = CallCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            call = log_call(
                actor=request.user,
                caller_name=serializer.validated_data.get("caller_name", ""),
                caller_phone=serializer.validated_data["caller_phone"],
                called_at=serializer.validated_data.get("called_at"),
                subject=serializer.validated_data["subject"],
                description=serializer.validated_data.get("description", ""),
                result=serializer.validated_data.get("result"),
                direction=serializer.validated_data.get("direction"),
                department=serializer.validated_data.get("department", ""),
                department_ref=serializer.validated_data.get("department_ref"),
                person=serializer.validated_data.get("person"),
                assignee=serializer.validated_data.get("assignee"),
                next_follow_up_at=serializer.validated_data.get("next_follow_up_at"),
                subject_ref=serializer.validated_data.get("subject_ref"),
            )
        except CallServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            InboundCallSerializer(call, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class CallDetailView(generics.RetrieveAPIView):
    permission_classes = (IsActiveUser, CanAccessCalls)
    serializer_class = InboundCallSerializer

    def get_queryset(self):
        return calls_visible_to(self.request.user)


class CallFollowUpView(APIView):
    """POST /api/calls/<id>/follow-up/ — تغییر وضعیت پیگیری + تاریخچه."""

    permission_classes = (IsActiveUser, CanAccessCalls)

    def post(self, request, pk):
        serializer = FollowUpSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            call = update_follow_up(
                call_id=pk, actor=request.user,
                new_status=serializer.validated_data["new_status"],
                note=serializer.validated_data.get("note", ""),
                next_follow_up_at=serializer.validated_data.get("next_follow_up_at"),
                assignee=serializer.validated_data.get("assignee"),
            )
        except InvalidTransitionError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except CallServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(InboundCallSerializer(call, context={"request": request}).data)


class CallReportView(APIView):
    """GET /api/calls/reports/ — گزارش مدیریتی تماس‌ها."""

    permission_classes = (IsActiveUser, CanAccessCalls)

    def get(self, request):
        try:
            filters = CallFilters.from_query(request.query_params)
        except CallReportError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(calls_report(filters, user=request.user))


class CallSubjectListView(generics.ListAPIView):
    """GET /api/calls/subjects/ — کاتالوگ موضوع‌های تماس (منبع حقیقت picklist)."""

    permission_classes = (IsActiveUser, CanAccessCalls)
    serializer_class = CallSubjectSerializer
    pagination_class = None

    def get_queryset(self):
        return CallSubject.objects.filter(
            is_active=True, is_deleted=False,
        ).order_by("name")
