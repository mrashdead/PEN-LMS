from django.contrib import admin

from apps.calls.models import CallFollowUpLog, CallSubject, InboundCall


@admin.register(CallSubject)
class CallSubjectAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "department", "is_active")
    list_filter = ("is_active",)


@admin.register(InboundCall)
class InboundCallAdmin(admin.ModelAdmin):
    list_display = (
        "caller_display", "caller_phone", "called_at", "receiver",
        "subject", "result", "follow_up_status", "next_follow_up_at",
    )
    list_filter = ("result", "follow_up_status", "direction", "called_at")
    search_fields = ("caller_name", "caller_phone", "subject", "description")
    readonly_fields = ("created_at", "updated_at")


@admin.register(CallFollowUpLog)
class CallFollowUpLogAdmin(admin.ModelAdmin):
    list_display = ("call", "actor", "previous_status", "new_status", "created_at")
    list_filter = ("new_status",)
    readonly_fields = ("created_at", "updated_at")
