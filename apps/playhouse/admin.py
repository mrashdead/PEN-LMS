"""
Playhouse Django admin — where a manager sets the 15-minute price and audits
members / sessions / invoices.
"""
from __future__ import annotations

from django.contrib import admin

from apps.playhouse.models import (
    PlayhouseConfig,
    PlayhouseInvoice,
    PlayhouseInvoiceItem,
    PlayhouseMember,
    PlayhouseSession,
)


@admin.register(PlayhouseConfig)
class PlayhouseConfigAdmin(admin.ModelAdmin):
    list_display = ("price_per_15_minutes", "open_time", "close_time", "is_open_now", "created_at")
    fields = ("price_per_15_minutes", "open_time", "close_time", "is_open_now")

    def has_add_permission(self, request) -> bool:
        # Singleton — reuse the existing row's edit form.
        return PlayhouseConfig.objects.count() == 0


@admin.register(PlayhouseMember)
class PlayhouseMemberAdmin(admin.ModelAdmin):
    list_display = ("display_name", "age", "guardian_mobile", "is_linked", "created_at")
    search_fields = ("first_name", "last_name", "guardian_mobile")
    list_filter = ("created_at",)


@admin.register(PlayhouseSession)
class PlayhouseSessionAdmin(admin.ModelAdmin):
    list_display = ("member", "status", "session_date", "entry_at", "exit_at", "operator")
    list_filter = ("status", "session_date")
    search_fields = ("member__first_name", "member__last_name")


class PlayhouseInvoiceItemInline(admin.TabularInline):
    model = PlayhouseInvoiceItem
    extra = 0


@admin.register(PlayhouseInvoice)
class PlayhouseInvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number", "member", "billed_minutes", "time_amount",
        "cafe_total", "total_amount", "payment_method", "is_paid", "created_at",
    )
    list_filter = ("is_paid", "payment_method", "created_at")
    search_fields = ("invoice_number", "tracking_code", "member__first_name")
    readonly_fields = ("total_amount", "cafe_total")
    inlines = (PlayhouseInvoiceItemInline,)
