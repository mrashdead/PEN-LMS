from django.contrib import admin

from apps.staff.models import (
    LeaveRequest,
    LeaveType,
    ReviewHistory,
    TimesheetEntry,
    WorkReport,
)


@admin.register(TimesheetEntry)
class TimesheetEntryAdmin(admin.ModelAdmin):
    list_display = ("user", "work_date", "check_in", "check_out", "kind", "status")
    list_filter = ("status", "kind", "work_date")
    search_fields = ("user__username", "note")
    readonly_fields = ("created_at", "updated_at")


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "accrual", "default_days", "is_active")
    list_filter = ("accrual", "is_active")


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "leave_type", "start_date", "end_date", "duration", "status")
    list_filter = ("status", "leave_type", "start_date")
    search_fields = ("user__username", "description")
    readonly_fields = ("created_at", "updated_at")


@admin.register(WorkReport)
class WorkReportAdmin(admin.ModelAdmin):
    list_display = ("user", "report_date", "title", "spent_minutes", "status")
    list_filter = ("status", "report_date")
    search_fields = ("user__username", "title", "description")


@admin.register(ReviewHistory)
class ReviewHistoryAdmin(admin.ModelAdmin):
    list_display = ("record_type", "record_id", "from_status", "to_status", "actor", "created_at")
    list_filter = ("record_type", "to_status")
    readonly_fields = ("created_at", "updated_at")
