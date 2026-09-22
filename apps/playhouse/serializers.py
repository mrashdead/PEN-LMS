"""
Playhouse DRF serializers — thin: read input for the service layer, present
output mostly via ``source``/properties so formatting stays declarative.
"""
from __future__ import annotations

from rest_framework import serializers

from apps.playhouse.models import (
    PlayhouseInvoice,
    PlayhouseInvoiceItem,
    PlayhouseMember,
    PlayhouseSession,
)


class PlayhouseMemberSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(read_only=True)
    is_linked = serializers.BooleanField(read_only=True)

    class Meta:
        model = PlayhouseMember
        fields = [
            "id", "person", "first_name", "last_name", "age",
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

    def validate_national_code(self, value):
        value = (value or "").strip()
        if value and (not value.isdigit() or len(value) != 10):
            raise serializers.ValidationError("کد ملی باید دقیقاً ۱۰ رقم باشد.")
        return value


class SessionActionSerializer(serializers.Serializer):
    """Body for start/stop/end/cancel — identity comes from the URL."""


class ActiveSessionSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.display_name", read_only=True)
    age = serializers.IntegerField(source="member.age", read_only=True)
    guardian_mobile = serializers.CharField(source="member.guardian_mobile", read_only=True)
    duration_label = serializers.CharField(read_only=True)
    elapsed_label = serializers.CharField(read_only=True)
    has_invoice = serializers.SerializerMethodField()
    invoice_is_paid = serializers.SerializerMethodField()
    invoice_number = serializers.SerializerMethodField()
    billable_minutes = serializers.IntegerField(read_only=True)
    billable_label = serializers.CharField(read_only=True)
    elapsed_seconds = serializers.IntegerField(read_only=True)

    class Meta:
        model = PlayhouseSession
        fields = [
            "id", "member_name", "age", "guardian_mobile", "created_at", "entry_at", "exit_at",
            "paused_at", "paused_seconds", "status", "duration_label", "elapsed_seconds", "elapsed_label", "billable_minutes", "billable_label",
            "has_invoice", "invoice_is_paid", "invoice_number",
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


class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayhouseInvoiceItem
        fields = ["id", "name", "price"]


class PlayhouseInvoiceSerializer(serializers.ModelSerializer):
    # Money is stored as integer تومان; expose as ints (not Decimal strings)
    # so API consumers get clean numbers.
    cafe_total = serializers.IntegerField(read_only=True)
    total_amount = serializers.IntegerField(read_only=True)
    time_amount = serializers.IntegerField(read_only=True)
    price_per_15_minutes = serializers.IntegerField(read_only=True)
    items = InvoiceItemSerializer(many=True, read_only=True)
    member_name = serializers.CharField(source="member.display_name", read_only=True)

    class Meta:
        model = PlayhouseInvoice
        fields = [
            "id", "invoice_number", "session", "member", "member_name",
            "billed_minutes", "price_per_15_minutes", "time_amount",
            "cafe_total", "total_amount", "items",
            "payment_method", "tracking_code", "is_paid", "paid_at", "notes",
        ]


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

    def validate(self, attrs):
        method = attrs.get("payment_method", "")
        tracking = attrs.get("tracking_code", "")
        if bool(method) != bool(tracking):
            raise serializers.ValidationError(
                "برای ثبت پرداخت، روش پرداخت و کد رهگیری هر دو الزامی هستند."
            )
        return attrs


class MarkPaymentSerializer(serializers.Serializer):
    payment_method = serializers.ChoiceField(
        choices=PlayhouseInvoice.PaymentMethod.choices,
        required=True,
    )
    tracking_code = serializers.CharField(max_length=64, required=True, allow_blank=False)
    notes = serializers.CharField(required=False, allow_blank=True, default="")
