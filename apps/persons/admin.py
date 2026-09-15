from __future__ import annotations

from django.contrib import admin

from apps.core.admin import JalaliAdminMixin
from apps.persons.models import Person


@admin.register(Person)
class PersonAdmin(JalaliAdminMixin, admin.ModelAdmin):
    list_display = (
        "national_code",
        "first_name",
        "last_name",
        "person_type",
        "mobile",
        "is_active",
        "has_user",
        "created_at_jalali_display",
    )
    list_filter = ("person_type", "is_active", "gender")
    search_fields = (
        "national_code",
        "first_name",
        "last_name",
        "mobile",
        "student_code",
        "employee_code",
    )
    autocomplete_fields = ("user", "registered_by")
    readonly_fields = ("created_at_jalali_display", "updated_at_jalali_display", "created_at", "updated_at")
    fieldsets = (
        ("هویت", {"fields": ("national_code", "first_name", "last_name", "father_name", "birth_date", "gender")}),
        ("تماس", {"fields": ("mobile", "email", "phone", "address", "postal_code")}),
        ("نوع", {"fields": ("person_type",)}),
        ("دانش‌آموز", {"fields": ("student_code",), "classes": ("collapse",)}),
        ("کارمند / معلم", {"fields": ("employee_code", "department", "job_title", "hire_date"), "classes": ("collapse",)}),
        ("سیستمی", {"fields": ("user", "is_active", "photo", "registered_by", "created_at_jalali_display", "updated_at_jalali_display")}),
    )

    @admin.display(boolean=True, description="User")
    def has_user(self, obj: Person) -> bool:
        return obj.user_id is not None
