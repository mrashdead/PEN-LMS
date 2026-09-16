from __future__ import annotations

from django.contrib import admin

from apps.core.admin import JalaliAdminMixin
from apps.persons.models import (
    GuardianProfile,
    Person,
    StaffProfile,
    StudentGuardian,
    StudentProfile,
)


# ── role-specific profile inlines ───────────────────────────────────────────
# Declared BEFORE PersonAdmin and attached in its class body: mutating
# `PersonAdmin.inlines` after the @register decorator runs would work (the
# admin site stores the class, not an instance) but reads like a bug.
#
# Profiles are edited on the Person page rather than as separate changelists —
# one human, one identity record (the same argument as the extension-table
# design note in models.py).

class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    fk_name = "person"
    extra = 0
    can_delete = False
    fields = (
        "grade_level", "class_section", "school_year", "enrollment_date",
        "birth_certificate_no", "has_special_needs", "is_custody_case",
        "custody_note", "health_notes", "is_active",
    )


class GuardianshipInline(admin.TabularInline):
    """Wards ← guardians of THIS student (the link owns custody + rights)."""

    model = StudentGuardian
    fk_name = "student"
    extra = 0
    autocomplete_fields = ("guardian",)
    fields = (
        "guardian", "relation", "custody_status", "phone_override",
        "can_view_grades", "can_view_attendance", "can_submit_requests",
        "can_receive_billing", "valid_from", "valid_to", "is_active",
    )


class StaffProfileInline(admin.StackedInline):
    model = StaffProfile
    fk_name = "person"
    extra = 0
    can_delete = False
    fieldsets = (
        ("قرارداد", {"fields": (
            "kind", "contract_no", "contract_type", "contract_start",
            "contract_end", "hourly_rate", "weekly_max_hours", "department")}),
        ("تخصص و سوابق", {"fields": (
            "specialization", "academic_degree", "experience_years", "bio")}),
        ("مدارک", {"fields": ("credentials", "is_verified", "is_active")}),
    )


class GuardianProfileInline(admin.StackedInline):
    model = GuardianProfile
    fk_name = "person"
    extra = 0
    can_delete = False
    fields = ("occupation", "education_level", "preferred_contact",
              "is_primary", "is_active")


class WardenLinkInline(admin.TabularInline):
    """The mirror view: which students this guardian is attached to."""

    model = StudentGuardian
    fk_name = "guardian"
    extra = 0
    autocomplete_fields = ("student",)
    fields = ("student", "relation", "custody_status", "phone_override",
              "can_submit_requests", "can_receive_billing", "is_active")


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
    inlines = [
        StudentProfileInline,
        GuardianshipInline,
        WardenLinkInline,
        StaffProfileInline,
        GuardianProfileInline,
    ]

    @admin.display(boolean=True, description="User")
    def has_user(self, obj: Person) -> bool:
        return obj.user_id is not None


@admin.register(StudentGuardian)
class StudentGuardianAdmin(JalaliAdminMixin, admin.ModelAdmin):
    """Ad-hoc custody management across the institute (search from either side).

    The wizard (apps.persons.onboarding) is the intended bulk path; this is the
    corrective surface for the cases it cannot express (a parent discovered
    years later, a custody change by court order).
    """

    list_display = ("student", "relation", "guardian", "custody_status",
                    "is_primary_flag", "is_active")
    list_filter = ("relation", "custody_status", "is_active")
    autocomplete_fields = ("student", "guardian")
    search_fields = (
        "student__national_code", "student__last_name",
        "guardian__national_code", "guardian__last_name",
    )
    readonly_fields = ("created_at", "updated_at")

    @admin.display(boolean=True, description="ولی اصلی")
    def is_primary_flag(self, obj) -> bool:
        profile = GuardianProfile.objects.filter(person=obj.guardian).first()
        return bool(profile and profile.is_primary)
