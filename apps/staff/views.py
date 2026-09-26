"""
Staff operations API — mounted under /api/staff/.

Thin HTTP layer: validate with serializers, call the service, return
serialised results. No business logic here. Every review endpoint shares
one ReviewSerializer and one service decision function.
"""
from __future__ import annotations

from django.core.exceptions import PermissionDenied
from django.db.models import Q
from rest_framework import generics, status
from rest_framework.permissions import SAFE_METHODS
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsActiveUser
from apps.core.utils import english_numbers
from apps.staff.models import (
    LeaveRequest,
    LeaveType,
    ReviewHistory,
    ReviewStatus,
    TimesheetEntry,
    WorkReport,
)
from apps.staff.permissions import IsStaffReviewer, IsStaffUser, IsTimesheetOwnerOrReviewer
from apps.staff.selectors import (
    StaffFilters,
    StaffReportError,
    staff_dashboard,
)
from apps.staff.serializers import (
    ClockInSerializer,
    LeaveRequestCreateSerializer,
    LeaveRequestSerializer,
    LeaveTypeSerializer,
    ReviewSerializer,
    TimesheetEntrySerializer,
    WorkReportCreateSerializer,
    WorkReportSerializer,
)
from apps.staff.services import (
    AlreadyClockedInError,
    InvalidReviewError,
    LeaveOverlapError,
    NotClockedInError,
    StaffServiceError,
    cancel_leave_request,
    clock_in,
    clock_out,
    create_leave_request,
    create_work_report,
    leave_requests_visible_to,
    review_history_for,
    review_leave_request,
    review_timesheet,
    review_work_report,
    timesheet_status,
    timesheets_visible_to,
    work_reports_visible_to,
)


class StaffClockView(APIView):
    """
    POST /api/staff/timesheet/clock-in/   — ثبت ورود
    POST /api/staff/timesheet/clock-out/  — ثبت خروج
    GET  /api/staff/timesheet/status/     — وضعیت امروز
    """

    permission_classes = (IsActiveUser, IsStaffUser)

    def post(self, request, action):
        if action == "clock-in":
            serializer = ClockInSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            try:
                entry = clock_in(
                    user=request.user,
                    work_date=serializer.validated_data.get("work_date"),
                    kind=serializer.validated_data.get("kind", TimesheetEntry.Kind.REGULAR),
                    note=serializer.validated_data.get("note", ""),
                )
            except (AlreadyClockedInError, StaffServiceError) as exc:
                return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
            return Response(TimesheetEntrySerializer(entry, context={"request": request}).data)

        if action == "clock-out":
            serializer = ClockInSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            try:
                entry = clock_out(
                    user=request.user,
                    work_date=serializer.validated_data.get("work_date"),
                    kind=serializer.validated_data.get("kind", TimesheetEntry.Kind.REGULAR),
                )
            except (NotClockedInError, StaffServiceError) as exc:
                return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
            return Response(TimesheetEntrySerializer(entry, context={"request": request}).data)

        return Response({"error": "عملیات نامعتبر است."}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, action):
        if action != "status":
            return Response({"error": "عملیات نامعتبر است."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(timesheet_status(user=request.user))


class TimesheetListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/staff/timesheets/  — لیست ساعت‌های کاری (دامنه: services)
    POST /api/staff/timesheets/  — ثبت دستی ورود/خروج (سرویس، برای مدیر)
    """

    permission_classes = (IsActiveUser, IsStaffUser, IsTimesheetOwnerOrReviewer)
    serializer_class = TimesheetEntrySerializer

    def get_queryset(self):
        qs = timesheets_visible_to(self.request.user)
        params = self.request.query_params
        raw_from = params.get("from")
        raw_to = params.get("to")
        if raw_from:
            qs = qs.filter(work_date__gte=_to_date(raw_from))
        if raw_to:
            qs = qs.filter(work_date__lte=_to_date(raw_to))
        status_param = (params.get("status") or "").strip().lower()
        if status_param:
            qs = qs.filter(status=status_param)
        kind = (params.get("kind") or "").strip().lower()
        if kind:
            qs = qs.filter(kind=kind)
        search = (params.get("search") or "").strip()
        if search:
            qs = qs.filter(user__username__icontains=search)
        return qs.order_by("-work_date", "-check_in", "-pk")

    def create(self, request, *args, **kwargs):
        # Manual entry (manager correction) — check_in/check_out both given.
        if not IsStaffReviewer().has_permission(request, self):
            return Response(
                {"error": "ثبت دستی ساعت کاری فقط برای مدیر/سرپرست مجاز است."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = TimesheetEntrySerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            entry = TimesheetEntry.objects.create(
                user=request.user,
                person=getattr(request.user, "person", None),
                work_date=serializer.validated_data["work_date"],
                kind=serializer.validated_data.get("kind", TimesheetEntry.Kind.REGULAR),
                check_in=serializer.validated_data["check_in"],
                check_out=serializer.validated_data.get("check_out"),
                note=serializer.validated_data.get("note", ""),
                status=ReviewStatus.PENDING,
            )
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            TimesheetEntrySerializer(entry, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class TimesheetDetailView(generics.RetrieveAPIView):
    permission_classes = (IsActiveUser, IsStaffUser, IsTimesheetOwnerOrReviewer)
    serializer_class = TimesheetEntrySerializer

    def get_queryset(self):
        return timesheets_visible_to(self.request.user)


class TimesheetReviewView(APIView):
    """POST /api/staff/timesheets/<id>/review/ — تأیید یا رد ساعت کاری."""

    permission_classes = (IsActiveUser, IsStaffUser, IsStaffReviewer)

    def post(self, request, pk):
        serializer = ReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            entry = review_timesheet(
                entry_id=pk, actor=request.user,
                decision=serializer.validated_data["decision"],
                comment=serializer.validated_data.get("comment", ""),
                rejection_reason=serializer.validated_data.get("rejection_reason", ""),
                override_minutes=serializer.validated_data.get("override_minutes"),
            )
        except InvalidReviewError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except StaffServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(TimesheetEntrySerializer(entry, context={"request": request}).data)


class LeaveTypeListView(generics.ListAPIView):
    """GET /api/staff/leave-types/ — کاتالوگ انواع مرخصی (منبع حقیقت)."""

    permission_classes = (IsActiveUser, IsStaffUser)
    serializer_class = LeaveTypeSerializer
    queryset = LeaveType.objects.filter(is_active=True, is_deleted=False).order_by("name")


class LeaveRequestListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/staff/leave-requests/  — درخواست‌های مرخصی (دامنه: services)
    POST /api/staff/leave-requests/  — ثبت درخواست جدید
    """

    permission_classes = (IsActiveUser, IsStaffUser)
    pagination_class = None

    def get_serializer_class(self):
        if self.request.method == "POST":
            return LeaveRequestCreateSerializer
        return LeaveRequestSerializer

    def get_queryset(self):
        qs = leave_requests_visible_to(self.request.user)
        params = self.request.query_params
        if params.get("from"):
            qs = qs.filter(start_date__gte=_to_date(params["from"]))
        if params.get("to"):
            qs = qs.filter(end_date__lte=_to_date(params["to"]))
        status_param = (params.get("status") or "").strip().lower()
        if status_param:
            qs = qs.filter(status=status_param)
        leave_type = (params.get("leave_type") or "").strip()
        if leave_type:
            qs = qs.filter(leave_type_id=leave_type)
        pending_only = (params.get("pending") or "").strip().lower() in {"1", "true", "yes"}
        if pending_only:
            qs = qs.filter(status=ReviewStatus.PENDING)
        return qs.order_by("-start_date", "-pk")

    def create(self, request, *args, **kwargs):
        serializer = LeaveRequestCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            record = create_leave_request(
                user=request.user,
                leave_type=serializer.validated_data["leave_type"],
                start_date=serializer.validated_data["start_date"],
                end_date=serializer.validated_data["end_date"],
                unit=serializer.validated_data.get("unit", LeaveRequest.Unit.DAY),
                description=serializer.validated_data.get("description", ""),
                attachment=serializer.validated_data.get("attachment"),
            )
        except (LeaveOverlapError, StaffServiceError) as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            LeaveRequestSerializer(record, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class LeaveRequestDetailView(generics.RetrieveAPIView):
    permission_classes = (IsActiveUser, IsStaffUser)
    serializer_class = LeaveRequestSerializer

    def get_queryset(self):
        return leave_requests_visible_to(self.request.user)


class LeaveRequestReviewView(APIView):
    """POST /api/staff/leave-requests/<id>/review/ — تأیید یا رد مرخصی."""

    permission_classes = (IsActiveUser, IsStaffUser, IsStaffReviewer)

    def post(self, request, pk):
        serializer = ReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            record = review_leave_request(
                request_id=pk, actor=request.user,
                decision=serializer.validated_data["decision"],
                comment=serializer.validated_data.get("comment", ""),
                rejection_reason=serializer.validated_data.get("rejection_reason", ""),
            )
        except InvalidReviewError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except StaffServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(LeaveRequestSerializer(record, context={"request": request}).data)


class LeaveRequestCancelView(APIView):
    """POST /api/staff/leave-requests/<id>/cancel/ — لغو درخواست pending."""

    permission_classes = (IsActiveUser, IsStaffUser)

    def post(self, request, pk):
        try:
            record = cancel_leave_request(request_id=pk, actor=request.user)
        except InvalidReviewError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except StaffServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(LeaveRequestSerializer(record, context={"request": request}).data)


class WorkReportListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/staff/work-reports/  — گزارش‌های کاری (دامنه: services)
    POST /api/staff/work-reports/  — ثبت گزارش روزانه
    """

    permission_classes = (IsActiveUser, IsStaffUser)

    def get_serializer_class(self):
        return WorkReportSerializer if self.request.method == "GET" else WorkReportCreateSerializer

    def get_queryset(self):
        qs = work_reports_visible_to(self.request.user)
        params = self.request.query_params
        if params.get("from"):
            qs = qs.filter(report_date__gte=_to_date(params["from"]))
        if params.get("to"):
            qs = qs.filter(report_date__lte=_to_date(params["to"]))
        status_param = (params.get("status") or "").strip().lower()
        if status_param:
            qs = qs.filter(status=status_param)
        return qs.order_by("-report_date", "-pk")

    def create(self, request, *args, **kwargs):
        serializer = WorkReportCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            report = create_work_report(
                user=request.user,
                report_date=serializer.validated_data.get("report_date"),
                title=serializer.validated_data["title"],
                description=serializer.validated_data.get("description", ""),
                spent_minutes=serializer.validated_data.get("spent_minutes", 0),
                timesheet_id=serializer.validated_data.get("timesheet"),
            )
        except StaffServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            WorkReportSerializer(report, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class WorkReportDetailView(generics.RetrieveAPIView):
    permission_classes = (IsActiveUser, IsStaffUser)
    serializer_class = WorkReportSerializer

    def get_queryset(self):
        return work_reports_visible_to(self.request.user)


class WorkReportReviewView(APIView):
    """POST /api/staff/work-reports/<id>/review/ — تأیید یا رد گزارش کاری."""

    permission_classes = (IsActiveUser, IsStaffUser, IsStaffReviewer)

    def post(self, request, pk):
        serializer = ReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            report = review_work_report(
                report_id=pk, actor=request.user,
                decision=serializer.validated_data["decision"],
                comment=serializer.validated_data.get("comment", ""),
                rejection_reason=serializer.validated_data.get("rejection_reason", ""),
            )
        except InvalidReviewError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except StaffServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(WorkReportSerializer(report, context={"request": request}).data)


class ReviewHistoryView(APIView):
    """
    GET /api/staff/history/<record_type>/<record_id>/ — تاریخچه append-only.
    record_type: timesheet | leave | work_report
    """

    permission_classes = (IsActiveUser, IsStaffUser)
    _MODELS = {
        "timesheet": (TimesheetEntry, ReviewHistory.RecordType.TIMESHEET),
        "leave": (LeaveRequest, ReviewHistory.RecordType.LEAVE),
        "work_report": (WorkReport, ReviewHistory.RecordType.WORK_REPORT),
    }

    def get(self, request, record_type, record_id):
        spec = self._MODELS.get(record_type)
        if spec is None:
            return Response({"error": "نوع رکورد نامعتبر است."}, status=status.HTTP_400_BAD_REQUEST)
        model, rtype = spec
        # Visibility: own record OR approver — same rule as the list views.
        qs = model.objects.filter(pk=record_id, is_deleted=False)
        if not (IsStaffReviewer().has_permission(request, self)):
            qs = qs.filter(user=request.user)
        if not qs.exists():
            return Response({"error": "رکورد یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        return Response(review_history_for(rtype, record_id))


class StaffReportView(APIView):
    """GET /api/staff/reports/ — داشبورد گزارش ساعت کاری/مرخصی/گزارش کاری."""

    permission_classes = (IsActiveUser, IsStaffUser)

    def get(self, request):
        try:
            filters = StaffFilters.from_query(request.query_params)
        except StaffReportError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(staff_dashboard(request.user, filters))


def _to_date(raw):
    """Accept Jalali (۱۴۰۵/۰۶/۲۵) or ISO Gregorian — mirrors report selectors."""
    from apps.staff.selectors import _parse_date

    value = _parse_date(raw)
    return value
