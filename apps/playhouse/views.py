"""
Playhouse API views — mounted under /api/playhouse/.

Thin HTTP layer: validate with serializers, call the service, return
serialised results. No business logic here.
"""
from __future__ import annotations

from datetime import date, timedelta

from django.db.models import Count, Sum
from rest_framework import status
from rest_framework.generics import (
    CreateAPIView,
    GenericAPIView,
    ListAPIView,
    RetrieveAPIView,
)
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.playhouse import selectors
from apps.playhouse.models import (
    PlayhouseConfig,
    PlayhouseInvoice,
    PlayhouseInvoiceItem,
    PlayhouseSession,
)
from apps.playhouse.permissions import IsPlayhouseFinance, IsPlayhouseOperator
from apps.playhouse.serializers import (
    ActiveSessionSerializer,
    CreateInvoiceSerializer,
    CreateSessionSerializer,
    MarkPaymentSerializer,
    PlayhouseInvoiceSerializer,
    PlayhouseMemberSerializer,
)
from apps.playhouse.services import PlayhouseService, PlayhouseServiceError


def _handle(fn):
    """Decorator: map PlayhouseServiceError to an HTTP 400 JSON body."""
    from functools import wraps

    @wraps(fn)
    def wrapper(self, request, *args, **kwargs):
        try:
            return fn(self, request, *args, **kwargs)
        except PlayhouseServiceError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return wrapper


class ConfigView(GenericAPIView):
    """GET — expose the current 15-minute price so the operator page shows it."""

    permission_classes = [IsPlayhouseOperator]

    def get(self, request):
        config = PlayhouseConfig.get_solo()
        return Response({"price_per_15_minutes": config.price_per_15_minutes})


class SessionListCreateView(CreateAPIView):
    """POST — create a new playhouse entry (operator intake)."""

    permission_classes = [IsPlayhouseOperator]
    serializer_class = CreateSessionSerializer

    @_handle
    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        session = PlayhouseService().create_session(
            operator=request.user,
            first_name=data["first_name"],
            last_name=data["last_name"],
            age=data.get("age"),
            guardian_mobile=data.get("guardian_mobile", ""),
            session_date=data.get("session_date"),
            member_pk=data.get("member_pk"),
            person_pk=data.get("person_pk"),
            national_code=data.get("national_code", ""),
            student_code=data.get("student_code", ""),
        )
        return Response({"id": session.pk}, status=status.HTTP_201_CREATED)


class MemberAutocompleteView(APIView):
    """GET ?q=… — searchable member picker for the intake form."""

    permission_classes = [IsPlayhouseOperator]
    def get(self, request):
        q = request.query_params.get("q", "")
        return Response({"results": selectors.member_and_person_autocomplete(q, limit=25)})


class SessionListView(ListAPIView):
    """GET — today's sessions (with running timers plus finished/cancelled)."""

    permission_classes = [IsPlayhouseOperator]
    serializer_class = ActiveSessionSerializer

    def get_queryset(self):
        return selectors.sessions_today()


class ActiveSessionsView(ListAPIView):
    """GET — only sessions with a running timer (polled by the operator page)."""

    permission_classes = [IsPlayhouseOperator]
    serializer_class = ActiveSessionSerializer

    def get_queryset(self):
        return selectors.active_sessions()


class SessionActionView(GenericAPIView):
    """
    POST /{pk}/{action}/ where action ∈ {start, stop, end}.
    The timer lifecycle for a single session.
    """

    permission_classes = [IsPlayhouseOperator]

    def post(self, request, pk, action):
        session = PlayhouseSession.objects.filter(pk=pk).first()
        if session is None:
            return Response({"detail": "نوبت پیدا نشد."}, status=status.HTTP_404_NOT_FOUND)
        service = PlayhouseService()
        try:
            if action == "start":
                session = service.start_session(session=session, operator=request.user)
            elif action == "stop":
                session = service.stop_session(session=session, operator=request.user)
            elif action == "end":
                session = service.end_session(session=session, operator=request.user)
            elif action == "cancel":
                session = service.cancel_session(session=session, operator=request.user)
            else:
                return Response(
                    {"detail": "عملیات نامعتبر."}, status=status.HTTP_400_BAD_REQUEST
                )
        except PlayhouseServiceError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(ActiveSessionSerializer(session).data)


class InvoiceCreateView(GenericAPIView):
    """
    POST /{session_pk}/invoice/ — bill a finished session (time +
    optional cafe items) creating the invoice row.
    """

    permission_classes = [IsPlayhouseOperator]
    serializer_class = CreateInvoiceSerializer

    @_handle
    def post(self, request, session_pk):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        session = PlayhouseSession.objects.filter(pk=session_pk).first()
        if session is None:
            return Response({"detail": "نوبت پیدا نشد."}, status=status.HTTP_404_NOT_FOUND)
        invoice = PlayhouseService().create_invoice(
            session=session,
            operator=request.user,
            cafe_items=ser.validated_data.get("cafe_items", []),
            payment_method=ser.validated_data.get("payment_method", ""),
            tracking_code=ser.validated_data.get("tracking_code", ""),
        )
        return Response(PlayhouseInvoiceSerializer(invoice).data, status=status.HTTP_201_CREATED)


class InvoiceDetailView(RetrieveAPIView):
    """GET — an invoice with its items and totals."""

    permission_classes = [IsPlayhouseOperator]
    queryset = PlayhouseInvoice.objects.select_related("session", "member")
    serializer_class = PlayhouseInvoiceSerializer
    lookup_url_kwarg = "pk"


class InvoiceMarkPaidView(GenericAPIView):
    """POST /invoices/{pk}/pay/ — record POS/card-transfer payment + tracking code."""

    permission_classes = [IsPlayhouseOperator, IsPlayhouseFinance]
    serializer_class = MarkPaymentSerializer

    @_handle
    def post(self, request, pk):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        invoice = PlayhouseInvoice.objects.filter(pk=pk).first()
        if invoice is None:
            return Response({"detail": "فاکتور پیدا نشد."}, status=status.HTTP_404_NOT_FOUND)
        invoice = PlayhouseService().record_payment(
            invoice=invoice,
            operator=request.user,
            payment_method=ser.validated_data["payment_method"],
            tracking_code=ser.validated_data["tracking_code"],
            paid=True,
        )
        return Response(PlayhouseInvoiceSerializer(invoice).data)


class FinanceReportView(GenericAPIView):
    """
    GET — financial report for the playhouse (گزارش مالی).

    Query params:
      ?from=YYYY-MM-DD &to=YYYY-MM-DD | ?period=daily|weekly|monthly
    Returns paid-invoice totals split by time vs cafe, plus grouped rows.
    """

    permission_classes = [IsPlayhouseOperator, IsPlayhouseFinance]

    def get(self, request):
        row = self.request.query_params
        today = date.today()
        start = end = None
        try:
            if row.get("from") and row.get("to"):
                start = date.fromisoformat(row["from"])
                end = date.fromisoformat(row["to"])
            elif row.get("period") == "weekly":
                start = today - timedelta(days=6)
                end = today
            elif row.get("period") == "monthly":
                start = today.replace(day=1)
                end = today
            else:  # default daily
                start = end = today
        except ValueError:
            return Response({"detail": "بازه تاریخ نامعتبر."}, status=400)

        base = PlayhouseInvoice.objects.filter(paid_at__date__range=[start, end])
        time_agg = base.aggregate(invoices=Count("id"), time_total=Sum("time_amount"))
        items_total = (
            PlayhouseInvoiceItem.objects.filter(
                invoice__paid_at__date__range=[start, end]
            ).aggregate(total=Sum("price"))["total"]
            or 0
        )
        by_method = (
            base.values("payment_method")
            .annotate(count=Count("id"), total=Sum("time_amount"))
            .order_by()
        )
        invoices = selectors.invoices_between(start, end).filter(
            paid_at__date__range=[start, end]
        )
        return Response(
            {
                "period": {"from": start.isoformat(), "to": end.isoformat()},
                "summary": {
                    "invoices": time_agg["invoices"] or 0,
                    "time_total": time_agg["time_total"] or 0,
                    "items_total": items_total,
                    "grand_total": (time_agg["time_total"] or 0) + items_total,
                },
                "by_method": [
                    {
                        "method": m["payment_method"] or "unpaid",
                        "count": m["count"],
                        "total": m["total"] or 0,
                    }
                    for m in by_method
                ],
                "invoices": [
                    {
                        "id": str(i.pk),
                        "number": i.invoice_number,
                        "member": i.member.display_name,
                        "method": i.payment_method,
                        "tracking": i.tracking_code,
                        "time_amount": i.time_amount,
                        "cafe_total": i.cafe_total,
                        "total": i.total_amount,
                        "paid_at": i.paid_at,
                    }
                    for i in invoices
                ],
            }
        )
