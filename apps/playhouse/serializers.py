"""
Playhouse DRF serializers — thin: read input for the service layer, present
output mostly via ``source``/properties so formatting stays declarative.
"""
from __future__ import annotations

from rest_framework import serializers

from apps.playhouse.models import (
    PlayhouseConfig,
    PlayhouseCafePreset,
    PlayhouseInvoice,
    PlayhouseInvoiceItem,
    PlayhouseCafeOrder,
    PlayhouseCafeOrderItem,
    PlayhousePayment,
    PlayhouseMember,
    PlayhouseSession,
)
from apps.persons.validation import (
    is_valid_iranian_mobile,
    national_code_error,
    normalize_national_code,
)


class PlayhouseMemberSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(read_only=True)
    is_linked = serializers.BooleanField(read_only=True)
    temporary_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = PlayhouseMember
        fields = [
            "id", "person", "temporary_id", "first_name", "last_name", "age",
            "guardian_mobile", "guardian_name", "display_name", "is_linked",
        ]
        read_only_fields = ["id"]


class CreateSessionSerializer(serializers.Serializer):
    """Operator intake for a new playhouse entry."""

    first_name = serializers.CharField(max_length=128, required=True)
    last_name = serializers.CharField(max_length=128, required=True)
    age = serializers.IntegerField(min_value=0, max_value=120, required=False, allow_null=True)
    guardian_mobile = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")
    session_date = serializers.DateField(required=False, allow_null=True)
    member_pk = serializers.UUIDField(required=False, allow_null=True)
    person_pk = serializers.UUIDField(required=False, allow_null=True)
    national_code = serializers.CharField(max_length=10, min_length=10, required=False, allow_blank=True, default="")
    student_code = serializers.CharField(max_length=32, required=False, allow_blank=True, default="")

    def validate_guardian_mobile(self, value):
        value = (value or "").strip()
        if value and not is_valid_iranian_mobile(value):
            raise serializers.ValidationError("شماره موبایل باید دقیقاً ۱۱ رقم و با ۰۹ شروع شود.")
        return value

    def validate_national_code(self, value):
        value = normalize_national_code(value)
        if not value:
            return ""
        error = national_code_error(value, require_location=True)
        if error:
            raise serializers.ValidationError(error)
        return value


class UpdatePlayhouseMemberSerializer(serializers.Serializer):
    """Complete a visitor's canonical Person record without touching visits."""

    first_name = serializers.CharField(max_length=128, required=False)
    last_name = serializers.CharField(max_length=128, required=False)
    national_code = serializers.CharField(max_length=10, required=False, allow_blank=True)
    student_code = serializers.CharField(max_length=32, required=False, allow_blank=True)
    age = serializers.IntegerField(min_value=0, max_value=120, required=False, allow_null=True)
    guardian_mobile = serializers.CharField(max_length=20, required=False, allow_blank=True)
    guardian_name = serializers.CharField(max_length=128, required=False, allow_blank=True)

    def validate_national_code(self, value):
        value = normalize_national_code(value)
        if value:
            error = national_code_error(value, require_location=True)
            if error:
                raise serializers.ValidationError(error)
        return value

    def validate_guardian_mobile(self, value):
        value = (value or "").strip()
        if value and not is_valid_iranian_mobile(value):
            raise serializers.ValidationError("شماره موبایل باید دقیقاً ۱۱ رقم و با ۰۹ شروع شود.")
        return value

class SessionActionSerializer(serializers.Serializer):
    """Body for start/stop/end/cancel — identity comes from the URL."""


class ActiveSessionSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.display_name", read_only=True)
    age = serializers.IntegerField(source="member.age", read_only=True)
    guardian_mobile = serializers.CharField(source="member.guardian_mobile", read_only=True)
    guardian_name = serializers.CharField(source="member.guardian_name", read_only=True)
    member_notes = serializers.CharField(source="member.notes", read_only=True)
    duration_label = serializers.CharField(read_only=True)
    elapsed_label = serializers.CharField(read_only=True)
    has_invoice = serializers.SerializerMethodField()
    invoice_is_paid = serializers.SerializerMethodField()
    invoice_number = serializers.SerializerMethodField()
    invoice_detail = serializers.SerializerMethodField()
    invoice_history = serializers.SerializerMethodField()
    cafe_orders = serializers.SerializerMethodField()
    paid_amount = serializers.SerializerMethodField()
    balance_amount = serializers.SerializerMethodField()
    billable_minutes = serializers.IntegerField(read_only=True)
    billable_label = serializers.CharField(read_only=True)
    elapsed_seconds = serializers.IntegerField(read_only=True)
    operator_name = serializers.CharField(source="operator.get_full_name", read_only=True)
    member_pk = serializers.UUIDField(source="member_id", read_only=True)
    member_first_name = serializers.CharField(source="member.first_name", read_only=True)
    member_last_name = serializers.CharField(source="member.last_name", read_only=True)
    temporary_id = serializers.UUIDField(source="member.temporary_id", read_only=True, allow_null=True)
    national_code = serializers.CharField(source="member.person.national_code", read_only=True, allow_null=True, default="")

    class Meta:
        model = PlayhouseSession
        fields = [
            "id", "member_pk", "member_first_name", "member_last_name", "temporary_id", "national_code", "member_name", "age", "guardian_mobile", "guardian_name", "member_notes", "created_at", "session_date", "operator_name", "entry_at", "exit_at",
            "paused_at", "paused_seconds", "status", "duration_label", "elapsed_seconds", "elapsed_label", "billable_minutes", "billable_label",
            "has_invoice", "invoice_is_paid", "invoice_number", "invoice_detail", "invoice_history", "cafe_orders", "paid_amount", "balance_amount",
        ]

    def _invoice(self, obj):
        try:
            return obj.invoice
        except PlayhouseInvoice.DoesNotExist:
            return None

    def get_has_invoice(self, obj):
        return self._invoice(obj) is not None

    def get_invoice_is_paid(self, obj):
        invoice = self._invoice(obj)
        return bool(invoice and invoice.is_paid)

    def get_invoice_number(self, obj):
        invoice = self._invoice(obj)
        return invoice.invoice_number if invoice else ""

    def get_invoice_detail(self, obj):
        invoice = self._invoice(obj)
        return PlayhouseInvoiceSerializer(invoice).data if invoice else None

    def get_invoice_history(self, obj):
        return PlayhouseInvoiceSerializer(obj.invoices.all(), many=True).data

    def get_cafe_orders(self, obj):
        return CafeOrderSerializer(obj.cafe_orders.all(), many=True).data

    def get_paid_amount(self, obj):
        return int(sum((row.amount for row in obj.payments.filter(reversed_at__isnull=True)), 0))

    def get_balance_amount(self, obj):
        invoice = self._invoice(obj)
        return int(invoice.balance_amount) if invoice else 0


class CafeOrderItemSerializer(serializers.ModelSerializer):
    line_total = serializers.IntegerField(read_only=True)
    unit_price = serializers.IntegerField(read_only=True)

    class Meta:
        model = PlayhouseCafeOrderItem
        fields = ["id", "name", "quantity", "unit_price", "line_total", "note"]


class CafeOrderSerializer(serializers.ModelSerializer):
    items = CafeOrderItemSerializer(many=True, read_only=True)
    payments = serializers.SerializerMethodField()
    paid_amount = serializers.SerializerMethodField()
    balance_amount = serializers.SerializerMethodField()
    member_name = serializers.CharField(source="session.member.display_name", read_only=True)
    temporary_id = serializers.UUIDField(source="session.member.temporary_id", read_only=True, allow_null=True)
    created_by_name = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()
    cancelled_at = serializers.DateTimeField(read_only=True)
    cancellation_note = serializers.CharField(read_only=True)
    cancelled_by_name = serializers.SerializerMethodField()
    ready_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PlayhouseCafeOrder
        fields = ["id", "session", "member_name", "temporary_id", "status", "kitchen_note", "created_at", "ready_at", "ready_by_name", "cancelled_at", "cancelled_by_name", "cancellation_note", "created_by_name", "total_amount", "paid_amount", "balance_amount", "items", "payments"]

    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() or obj.created_by.get_username()

    def get_total_amount(self, obj):
        return int(sum((item.line_total for item in obj.items.all()), 0))

    def get_payments(self, obj):
        rows = obj.payments.all()
        return PlayhousePaymentSerializer(rows, many=True).data

    def get_paid_amount(self, obj):
        return int(sum((payment.amount for payment in obj.payments.all() if not payment.is_reversed), 0))

    def get_balance_amount(self, obj):
        return max(0, self.get_total_amount(obj) - self.get_paid_amount(obj))

    def get_cancelled_by_name(self, obj):
        return (obj.cancelled_by.get_full_name() or obj.cancelled_by.get_username()) if obj.cancelled_by_id else ""

    def get_ready_by_name(self, obj):
        return (obj.ready_by.get_full_name() or obj.ready_by.get_username()) if obj.ready_by_id else ""


class KitchenCafeOrderSerializer(serializers.ModelSerializer):
    items = CafeOrderItemSerializer(many=True, read_only=True)
    member_name = serializers.CharField(source="session.member.display_name", read_only=True)
    temporary_id = serializers.UUIDField(source="session.member.temporary_id", read_only=True, allow_null=True)
    created_by_name = serializers.SerializerMethodField()
    ready_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PlayhouseCafeOrder
        fields = ["id", "session", "member_name", "temporary_id", "status", "kitchen_note", "created_at", "created_by_name", "ready_at", "ready_by_name", "items"]

    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() or obj.created_by.get_username()

    def get_ready_by_name(self, obj):
        return (obj.ready_by.get_full_name() or obj.ready_by.get_username()) if obj.ready_by_id else ""


class CafeOrderItemInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    quantity = serializers.IntegerField(min_value=1, max_value=99, default=1)
    unit_price = serializers.IntegerField(min_value=0, required=False)
    price = serializers.IntegerField(min_value=0, required=False)
    note = serializers.CharField(max_length=300, required=False, allow_blank=True, default="")

    def validate(self, attrs):
        if "unit_price" not in attrs and "price" not in attrs:
            raise serializers.ValidationError("قیمت آیتم الزامی است.")
        attrs["unit_price"] = attrs.get("unit_price", attrs.get("price"))
        return attrs


class PaymentInputSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=PlayhousePayment.Method.choices)
    amount = serializers.IntegerField(min_value=1)
    tracking_code = serializers.CharField(max_length=64, required=False, allow_blank=True, default="")


class CreateCafeOrderSerializer(serializers.Serializer):
    items = CafeOrderItemInputSerializer(many=True, allow_empty=False)
    payments = PaymentInputSerializer(many=True, required=False, default=list)
    kitchen_note = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")


class AddPaymentSerializer(serializers.Serializer):
    payments = PaymentInputSerializer(many=True, allow_empty=False)


class VoidInvoiceSerializer(serializers.Serializer):
    note = serializers.CharField(max_length=300, allow_blank=False)


class ReversePaymentSerializer(serializers.Serializer):
    note = serializers.CharField(max_length=300, allow_blank=False)


class InvoiceItemSerializer(serializers.ModelSerializer):
    line_total = serializers.IntegerField(read_only=True)
    price = serializers.IntegerField(read_only=True)

    class Meta:
        model = PlayhouseInvoiceItem
        fields = ["id", "name", "price", "quantity", "line_total"]


class PlayhousePaymentSerializer(serializers.ModelSerializer):
    method_label = serializers.CharField(source="get_method_display", read_only=True)
    amount = serializers.IntegerField(read_only=True)
    created_by_name = serializers.SerializerMethodField()
    reversed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PlayhousePayment
        fields = ["id", "method", "method_label", "amount", "tracking_code", "created_at", "created_by_name", "is_reversed", "reversed_at", "reversal_note", "reversed_by_name"]

    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() or obj.created_by.get_username()

    def get_reversed_by_name(self, obj):
        return (obj.reversed_by.get_full_name() or obj.reversed_by.get_username()) if obj.reversed_by_id else ""


class PlayhouseCafePresetSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayhouseCafePreset
        fields = ["id", "name", "price"]
        read_only_fields = ["id"]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("نام آیتم را وارد کنید.")
        duplicates = PlayhouseCafePreset.objects.filter(name__iexact=value)
        if self.instance:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError("این نام از قبل در فهرست آماده وجود دارد.")
        return value


class PlayhouseInvoiceSerializer(serializers.ModelSerializer):
    # Money is stored as integer تومان; expose as ints (not Decimal strings)
    # so API consumers get clean numbers.
    cafe_total = serializers.IntegerField(read_only=True)
    total_amount = serializers.IntegerField(read_only=True)
    time_amount = serializers.IntegerField(read_only=True)
    price_per_15_minutes = serializers.IntegerField(read_only=True)
    items = InvoiceItemSerializer(many=True, read_only=True)
    payments = serializers.SerializerMethodField()
    member_name = serializers.CharField(source="member.display_name", read_only=True)
    paid_amount = serializers.IntegerField(read_only=True)
    balance_amount = serializers.IntegerField(read_only=True)
    voided_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PlayhouseInvoice
        fields = [
            "id", "invoice_number", "session", "member", "member_name",
            "billed_minutes", "price_per_15_minutes", "time_amount",
            "cafe_total", "discount_amount", "discount_note", "total_amount", "paid_amount", "balance_amount", "items", "payments",
            "payment_method", "tracking_code", "is_paid", "paid_at", "notes", "is_voided", "voided_at", "voided_by_name", "void_note",
        ]

    def get_voided_by_name(self, obj):
        return (obj.voided_by.get_full_name() or obj.voided_by.get_username()) if obj.voided_by_id else ""

    def get_payments(self, obj):
        rows = obj.session.payments.all()
        if obj.is_voided and obj.voided_at:
            rows = rows.filter(created_at__lte=obj.voided_at)
        return PlayhousePaymentSerializer(rows, many=True).data


class CreateInvoiceSerializer(serializers.Serializer):
    """Popup payload when billing: cafe items plus optional payment details."""

    cafe_items = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list,
        help_text="آیتم‌های کافه: [{name, price}]",
    )
    payment_method = serializers.ChoiceField(
        choices=PlayhouseInvoice.PaymentMethod.choices,
        required=False,
        allow_blank=True,
        default="",
    )
    tracking_code = serializers.CharField(
        max_length=64, required=False, allow_blank=True, default=""
    )
    discount_amount = serializers.IntegerField(min_value=0, required=False, default=0)
    discount_note = serializers.CharField(max_length=300, required=False, allow_blank=True, default="")

    def validate(self, attrs):
        method = attrs.get("payment_method", "")
        tracking = attrs.get("tracking_code", "")
        if bool(method) and method != PlayhouseInvoice.PaymentMethod.CASH and not tracking:
            raise serializers.ValidationError(
                "برای پرداخت غیرنقدی، کد رهگیری الزامی است."
            )
        if not method and tracking:
            raise serializers.ValidationError("برای ثبت کد رهگیری، روش پرداخت را انتخاب کنید.")
        return attrs


class MarkPaymentSerializer(serializers.Serializer):
    payment_method = serializers.ChoiceField(
        choices=PlayhouseInvoice.PaymentMethod.choices,
        required=True,
    )
    tracking_code = serializers.CharField(max_length=64, required=False, allow_blank=True, default="")
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        if attrs["payment_method"] != PlayhouseInvoice.PaymentMethod.CASH and not attrs.get("tracking_code"):
            raise serializers.ValidationError("برای پرداخت غیرنقدی کد رهگیری الزامی است.")
        return attrs


class PlayhouseConfigSerializer(serializers.Serializer):
    """Read/patch the singleton playhouse settings."""

    price_per_15_minutes = serializers.IntegerField(min_value=0, required=True)
    open_time = serializers.TimeField(required=False, allow_null=True)
    close_time = serializers.TimeField(required=False, allow_null=True)
    is_open_now = serializers.BooleanField(required=False, default=True)
