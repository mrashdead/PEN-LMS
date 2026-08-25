from __future__ import annotations

from django.contrib import admin

from apps.academics.models import AcademicTerm, ClassEnrollment, ClassGroup
from apps.core.admin import JalaliAdminMixin


class ClassEnrollmentInline(admin.TabularInline):
    model = ClassEnrollment
    extra = 0
    fields = ("student", "enrollment_date", "is_active")
    autocomplete_fields = ("student",)
    raw_id_fields = ("student",)


@admin.register(AcademicTerm)
class AcademicTermAdmin(JalaliAdminMixin, admin.ModelAdmin):
    list_display = ("title", "start_date", "end_date", "is_current", "is_active", "created_at_jalali_display")
    list_filter = ("is_current", "is_active")
    search_fields = ("title",)
    readonly_fields = ("created_at_jalali_display", "updated_at_jalali_display", "created_at", "updated_at")
    fieldsets = (
        ("مشخصات ترم", {"fields": ("title", "is_current", "is_active")}),
        ("تاریخ", {"fields": ("start_date", "end_date")}),
        ("سایر", {"fields": ("note", "created_at_jalali_display", "updated_at_jalali_display")}),
    )
    actions = ["make_current"]

    @admin.action(description="انتخاب به عنوان ترم جاری")
    def make_current(self, request, queryset):
        updated = queryset.update(is_current=True)
        self.message_user(request, f"{updated} ترم به عنوان جاری انتخاب شد.")


@admin.register(ClassGroup)
class ClassGroupAdmin(JalaliAdminMixin, admin.ModelAdmin):
    list_display = ("name", "code", "term", "teacher", "room", "capacity", "enrollment_count", "is_active", "created_at_jalali_display")
    list_filter = ("is_active", "term")
    search_fields = ("name", "code", "room", "teacher__first_name", "teacher__last_name")
    autocomplete_fields = ("term", "teacher")
    readonly_fields = ("created_at_jalali_display", "updated_at_jalali_display", "created_at", "updated_at")
    inlines = (ClassEnrollmentInline,)
    fieldsets = (
        ("مشخصات کلاس", {"fields": ("code", "name", "term", "is_active")}),
        ("معلم و مکان", {"fields": ("teacher", "room", "capacity")}),
        ("زمان‌بندی", {"fields": ("schedule",)}),
        ("سیستمی", {"fields": ("created_at_jalali_display", "updated_at_jalali_display")}),
    )


@admin.register(ClassEnrollment)
class ClassEnrollmentAdmin(JalaliAdminMixin, admin.ModelAdmin):
    list_display = ("student", "class_group", "enrollment_date", "is_active", "created_at_jalali_display")
    list_filter = ("is_active", "class_group__term")
    search_fields = ("student__first_name", "student__last_name", "student__student_code", "class_group__name")
    autocomplete_fields = ("class_group", "student")
    raw_id_fields = ("student",)
    readonly_fields = ("created_at_jalali_display", "updated_at_jalali_display", "created_at", "updated_at")
