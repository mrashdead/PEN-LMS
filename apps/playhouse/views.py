"""
Playhouse API views — mounted under /api/playhouse/.

Thin HTTP layer: validate with serializers, call the service, return
serialised results. No business logic here.
"""
from __future__ import annotations

from datetime import date, timedelta

from django.db.models import Count, F, Q, Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import (
    CreateAPIView,
    GenericAPIView,
    ListAPIView,
    RetrieveAPIView,
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from apps.playhouse import selectors
from apps.playhouse.models import (
    PlayhouseConfig,
    PlayhouseCafePreset,
    PlayhouseCafeOrder,
    PlayhouseInvoice,
    PlayhouseInvoiceItem,
    PlayhouseMember,
    PlayhousePayment,
    PlayhouseSession,
)
from apps.playhouse.permissions import (
    FINANCE_ROLES,
    IsPlayhouseFinance,
    IsPlayhouseKitchen,
    IsPlayhouseOperator,
    PRICE_EDITOR_ROLES,
)
from apps.playhouse.serializers import (
    ActiveSessionSerializer,
    CreateInvoiceSerializer,
    CreateSessionSerializer,
    MarkPaymentSerializer,
    ReversePaymentSerializer,
    PlayhouseConfigSerializer,
    PlayhouseInvoiceSerializer,
    PlayhouseMemberSerializer,
    PlayhouseCafePresetSerializer,
    UpdatePlayhouseMemberSerializer,
    CreateCafeOrderSerializer,
    AddPaymentSerializer,
    CafeOrderSerializer,
    KitchenCafeOrderSerializer,
    PlayhousePaymentSerializer,
    VoidInvoiceSerializer,
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
    """GET — current settings; PUT/PATCH — update (manager-level)."""

    permission_classes = [IsPlayhouseOperator]
    serializer_class = PlayhouseConfigSerializer

    def get(self, request):
        config = PlayhouseConfig.get_solo()
        return Response({
            "price_per_15_minutes": config.price_per_15_minutes,
            "open_time": config.open_time,
            "close_time": config.close_time,
            "is_open_now": config.is_open_now,
        })

    @_handle
    def put(self, request):
        # Only finance/manager roles may change billing settings.
        roles = set(request.user.role_codes()) if hasattr(request.user, "role_codes") else set()
        if not roles & PRICE_EDITOR_ROLES:
            return Response(
                {"detail": "فقط سرپرستان و مدیران می‌توانند نرخ خانه بازی را تغییر دهند."},
                status=status.HTTP_403_FORBIDDEN,
            )
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        current = PlayhouseConfig.get_solo()
        config = PlayhouseService().update_config(
            operator=request.user,
            price_per_15_minutes=d["price_per_15_minutes"],
            open_time=d.get("open_time", current.open_time),
            close_time=d.get("close_time", current.close_time),
            is_open_now=d.get("is_open_now", current.is_open_now),
        )
        return Response({
            "price_per_15_minutes": config.price_per_15_minutes,
            "open_time": config.open_time,
            "close_time": config.close_time,
            "is_open_now": config.is_open_now,
        })

    # PATCH mirrors PUT (partial semantics handled by the serializer defaults).
    patch = put


class CafePresetListCreateView(ListAPIView):
    """GET/POST — list or add reusable cafe items for invoices."""

    permission_classes = [IsPlayhouseOperator]
    serializer_class = PlayhouseCafePresetSerializer
    queryset = PlayhouseCafePreset.objects.all()

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CafePresetDetailView(RetrieveAPIView):
    """PATCH/DELETE — update or remove a saved cafe item."""

    permission_classes = [IsPlayhouseOperator]
    serializer_class = PlayhouseCafePresetSerializer
    queryset = PlayhouseCafePreset.objects.all()

    def patch(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        self.get_object().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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
        return Response({
            "id": session.pk,
            "temporary_id": str(session.member.temporary_id) if session.member.temporary_id else "",
        }, status=status.HTTP_201_CREATED)


class MemberAutocompleteView(APIView):
    """GET ?q=… — searchable member picker for the intake form."""

    permission_classes = [IsPlayhouseOperator]
    def get(self, request):
        q = request.query_params.get("q", "")
        return Response({"results": selectors.member_and_person_autocomplete(q, limit=25)})


class PlayhouseMemberDetailView(GenericAPIView):
    """PATCH a child's identity; session/timer columns are never written here."""

    permission_classes = [IsPlayhouseOperator]
    serializer_class = UpdatePlayhouseMemberSerializer

    @_handle
    def patch(self, request, pk):
        member = PlayhouseMember.objects.filter(pk=pk).first()
        if member is None:
            return Response({"detail": "کودک پیدا نشد."}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = PlayhouseService().update_member(member=member, data=serializer.validated_data)
        return Response(PlayhouseMemberSerializer(updated).data)


class SessionListView(ListAPIView):
    """GET — today's sessions (with running timers plus finished/cancelled)."""

    permission_classes = [IsPlayhouseOperator]
    serializer_class = ActiveSessionSerializer

    def get_queryset(self):
        raw_day = self.request.query_params.get("date")
        if not raw_day:
            return selectors.sessions_today()
        try:
            return selectors.sessions_on(date.fromisoformat(raw_day))
        except ValueError:
            raise ValidationError({"date": "تاریخ باید به شکل YYYY-MM-DD باشد."})


class ActiveSessionsView(ListAPIView):
    """GET — only sessions with a running timer (polled by the operator page)."""

    permission_classes = [IsPlayhouseOperator]
    serializer_class = ActiveSessionSerializer

    def get_queryset(self):
        return selectors.active_sessions()


class CafeOrderCreateView(GenericAPIView):
    permission_classes = [IsPlayhouseOperator]
    serializer_class = CreateCafeOrderSerializer

    @_handle
    def post(self, request, session_pk):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        session = PlayhouseSession.objects.filter(pk=session_pk).first()
        if session is None:
            return Response({"detail": "مراجعه پیدا نشد."}, status=404)
        order = PlayhouseService().create_cafe_order(
            session=session, operator=request.user,
            items=ser.validated_data["items"],
            payments=ser.validated_data.get("payments", []),
            kitchen_note=ser.validated_data.get("kitchen_note", ""),
        )
        return Response(CafeOrderSerializer(order).data, status=201)


class SessionPaymentsView(GenericAPIView):
    permission_classes = [IsPlayhouseOperator]
    serializer_class = AddPaymentSerializer

    @_handle
    def post(self, request, session_pk):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        session = PlayhouseSession.objects.filter(pk=session_pk).first()
        if session is None:
            return Response({"detail": "مراجعه پیدا نشد."}, status=404)
        if session.status == PlayhouseSession.Status.FINISHED:
            roles = set(request.user.role_codes()) if hasattr(request.user, "role_codes") else set()
            if not roles & FINANCE_ROLES:
                return Response({"detail": "ثبت پرداخت پس از پایان مراجعه به دسترسی مالی نیاز دارد."}, status=403)
        rows = PlayhouseService().add_session_payments(
            session=session, operator=request.user, payments=ser.validated_data["payments"]
        )
        return Response(PlayhousePaymentSerializer(rows, many=True).data, status=201)


class KitchenOrdersView(ListAPIView):
    permission_classes = [IsPlayhouseKitchen]
    serializer_class = KitchenCafeOrderSerializer
    pagination_class = None

    def get_queryset(self):
        return PlayhouseCafeOrder.objects.filter(
            status__in=[PlayhouseCafeOrder.Status.NEW, PlayhouseCafeOrder.Status.PREPARING, PlayhouseCafeOrder.Status.READY],
            created_at__date=timezone.localdate(),
        ).select_related("session", "session__member", "created_by", "ready_by", "cancelled_by").prefetch_related("items").order_by("created_at")


class KitchenOrderStatusView(GenericAPIView):
    permission_classes = [IsPlayhouseKitchen]

    @_handle
    def post(self, request, pk):
        order = PlayhouseCafeOrder.objects.filter(pk=pk).first()
        if order is None:
            return Response({"detail": "سفارش پیدا نشد."}, status=404)
        status_value = request.data.get("status", PlayhouseCafeOrder.Status.READY)
        order = PlayhouseService().set_cafe_order_status(order=order, operator=request.user, status_value=status_value)
        return Response(KitchenCafeOrderSerializer(order).data)


class CafeOrderCancelView(GenericAPIView):
    permission_classes = [IsPlayhouseOperator, IsPlayhouseFinance]

    @_handle
    def post(self, request, pk):
        order = PlayhouseCafeOrder.objects.filter(pk=pk).first()
        if order is None:
            return Response({"detail": "سفارش پیدا نشد."}, status=404)
        order = PlayhouseService().cancel_cafe_order(
            order=order, operator=request.user, note=request.data.get("note", "")
        )
        return Response(CafeOrderSerializer(order).data)


class AttendanceReportView(ListAPIView):
    """Daily register including waiting, active, finished and cancelled visits."""
    permission_classes = [IsPlayhouseOperator]
    serializer_class = ActiveSessionSerializer
    pagination_class = None

    def get_queryset(self):
        raw_day = self.request.query_params.get("date")
        try:
            day = date.fromisoformat(raw_day) if raw_day else timezone.localdate()
        except ValueError:
            raise ValidationError({"date": "تاریخ باید به شکل YYYY-MM-DD باشد."})
        return selectors.sessions_on(day)


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
                session = service.start_session(session=session, operator=request.user, entry_at=request.data.get("entry_at"))
            elif action == "stop":
                session = service.stop_session(session=session, operator=request.user)
            elif action == "end":
                session = service.end_session(session=session, operator=request.user, exit_at=request.data.get("exit_at"))
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
        if ser.validated_data.get("is_free"):
            roles = set(request.user.role_codes()) if hasattr(request.user, "role_codes") else set()
            if not roles & FINANCE_ROLES:
                return Response({"detail": "صدور فاکتور رایگان به دسترسی مالی نیاز دارد."}, status=403)
        if ser.validated_data.get("discount_amount", 0):
            roles = set(request.user.role_codes()) if hasattr(request.user, "role_codes") else set()
            if not roles & FINANCE_ROLES:
                return Response({"detail": "ثبت تخفیف نیاز به دسترسی مالی دارد."}, status=403)
        session = PlayhouseSession.objects.filter(pk=session_pk).first()
        if session is None:
            return Response({"detail": "نوبت پیدا نشد."}, status=status.HTTP_404_NOT_FOUND)
        invoice = PlayhouseService().create_invoice(
            session=session,
            operator=request.user,
            cafe_items=ser.validated_data.get("cafe_items", []),
            payments=ser.validated_data.get("payments", []),
            is_free=ser.validated_data.get("is_free", False),
            free_reason=ser.validated_data.get("free_reason", ""),
            payment_method=ser.validated_data.get("payment_method", ""),
            tracking_code=ser.validated_data.get("tracking_code", ""),
            discount_amount=ser.validated_data.get("discount_amount", 0),
            discount_note=ser.validated_data.get("discount_note", ""),
        )
        return Response(PlayhouseInvoiceSerializer(invoice).data, status=status.HTTP_201_CREATED)


class InvoiceDetailView(RetrieveAPIView):
    """GET — an invoice with its items and totals."""

    permission_classes = [IsPlayhouseOperator]
    queryset = PlayhouseInvoice.objects.select_related("session", "member").prefetch_related("session__payments", "items")
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


class InvoiceVoidView(GenericAPIView):
    permission_classes = [IsPlayhouseOperator, IsPlayhouseFinance]
    serializer_class = VoidInvoiceSerializer

    @_handle
    def post(self, request, pk):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        invoice = PlayhouseInvoice.objects.filter(pk=pk).first()
        if invoice is None:
            return Response({"detail": "فاکتور پیدا نشد."}, status=404)
        invoice = PlayhouseService().void_invoice(
            invoice=invoice, operator=request.user, note=ser.validated_data["note"]
        )
        return Response(PlayhouseInvoiceSerializer(invoice).data)


class PaymentReverseView(GenericAPIView):
    permission_classes = [IsPlayhouseOperator, IsPlayhouseFinance]
    serializer_class = ReversePaymentSerializer

    @_handle
    def post(self, request, pk):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        payment = PlayhousePayment.objects.filter(pk=pk).first()
        if payment is None:
            return Response({"detail": "پرداخت پیدا نشد."}, status=404)
        payment = PlayhouseService().reverse_payment(
            payment=payment, operator=request.user, note=ser.validated_data["note"]
        )
        return Response(PlayhousePaymentSerializer(payment).data)


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
        from apps.core.report_dates import ReportDateError, ReportRange
        try:
            bounds = ReportRange.from_query(row)
        except ReportDateError as exc:
            return Response({"detail": str(exc)}, status=400)
        start, end = bounds.start, bounds.end

        base = PlayhouseInvoice.objects.filter(is_voided=False).filter(
            Q(paid_at__gte=bounds.start_at, paid_at__lt=bounds.end_before)
            | Q(session__payments__created_at__gte=bounds.start_at, session__payments__created_at__lt=bounds.end_before, session__payments__reversed_at__isnull=True)
        ).distinct()
        invoices = list(base.select_related("session", "member", "operator").prefetch_related(
            "items", "session__payments"
        ).order_by("-created_at"))
        time_total = sum((invoice.time_amount for invoice in invoices), 0)
        items_total = (
            PlayhouseInvoiceItem.objects.filter(
                invoice__in=base,
            ).aggregate(total=Sum(F("price") * F("quantity")))["total"]
            or 0
        )
        payment_rows = list(PlayhousePayment.objects.filter(
            created_at__gte=bounds.start_at, created_at__lt=bounds.end_before, reversed_at__isnull=True
        ).select_related("session", "created_by"))
        payment_totals = {}
        period_paid_by_session = {}
        period_last_payment_by_session = {}
        for payment in payment_rows:
            row = payment_totals.setdefault(payment.method, {"count": 0, "total": 0})
            row["count"] += 1
            row["total"] += payment.amount
            period_paid_by_session[payment.session_id] = period_paid_by_session.get(payment.session_id, 0) + payment.amount
            prior = period_last_payment_by_session.get(payment.session_id)
            if prior is None or payment.created_at > prior:
                period_last_payment_by_session[payment.session_id] = payment.created_at
        legacy_paid = list(PlayhouseInvoice.objects.filter(
            is_voided=False, is_paid=True, paid_at__gte=bounds.start_at, paid_at__lt=bounds.end_before,
            session__payments__isnull=True,
        ).select_related("session"))
        legacy_total = sum((invoice.total_amount for invoice in legacy_paid), 0)
        received_total = sum((payment.amount for payment in payment_rows), 0) + legacy_total
        cafe_sales = (
            PlayhouseInvoiceItem.objects.filter(
                invoice__in=base,
            )
            .values("name")
            .annotate(quantity_sold=Sum("quantity"), total=Sum(F("price") * F("quantity")))
            .order_by("-quantity_sold", "name")
        )
        return Response(
            {
                "period": {"from": start.isoformat(), "to": end.isoformat(), "start_at": bounds.start_at.isoformat(), "end_before": bounds.end_before.isoformat(), "timezone": str(timezone.get_default_timezone())},
                "summary": {
                    "invoices": len(invoices),
                    "time_total": time_total,
                    "items_total": items_total,
                    "grand_total": received_total,
                },
                "by_method": [
                    {
                        "method": method,
                        "count": values["count"],
                        "total": values["total"],
                    }
                    for method, values in sorted(payment_totals.items())
                ],
                "cafe_item_sales": [
                    {
                        "name": item["name"],
                        "quantity": item["quantity_sold"],
                        "total": item["total"] or 0,
                    }
                    for item in cafe_sales
                ],
                "invoices": [
                    {
                        "id": str(i.pk),
                        "number": i.invoice_number,
                        "member": i.member.display_name,
                        "member_age": i.member.age,
                        "guardian_name": i.member.guardian_name,
                        "guardian_mobile": i.member.guardian_mobile,
                        "operator": i.operator.get_full_name() or i.operator.get_username(),
                        "entry_at": i.session.entry_at,
                        "exit_at": i.session.exit_at,
                        "method": "split" if len({p.method for p in i.session.payments.all() if not p.is_reversed}) > 1 else i.payment_method,
                        "tracking": i.tracking_code,
                        "time_amount": i.time_amount,
                        "cafe_total": i.cafe_total,
                        "total": i.total_amount,
                        "discount_amount": i.discount_amount,
                        "discount_note": i.discount_note,
                        "paid_amount": i.paid_amount,
                        "balance_amount": i.balance_amount,
                        "period_paid_amount": period_paid_by_session.get(i.session_id, i.total_amount if i in legacy_paid else 0),
                        "paid_at": period_last_payment_by_session.get(i.session_id, i.paid_at),
                        "payments": [
                            {"method": p.method, "amount": p.amount, "tracking_code": p.tracking_code}
                            for p in i.session.payments.filter(reversed_at__isnull=True)
                        ],
                        "items": [
                            {"name": item.name, "price": item.price, "quantity": item.quantity, "line_total": item.line_total}
                            for item in i.items.all()
                        ],
                    }
                    for i in invoices
                ],
            }
        )
