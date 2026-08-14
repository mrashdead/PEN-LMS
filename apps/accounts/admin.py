# apps/accounts/admin.py
from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import Role, User, UserRole


class UserRoleInline(admin.TabularInline):
    model = UserRole
    fk_name = "user"
    extra = 0

    autocomplete_fields = ("role", "assigned_by")
    raw_id_fields = ("assigned_by",)
    fields = (
        "role",
        "is_active",
        "valid_from",
        "valid_to",
        "assigned_by",
        "note",
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("code", "name")
    ordering = ("priority", "code")
    prepopulated_fields = {"code": ("name",)}  # دستی بعداً code را ثابت نگه دارید
    readonly_fields = ("created_at", "updated_at")


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "role",
        "is_active",
        "valid_from",
        "valid_to",
        "assigned_by",
        "created_at",
    )
    list_filter = ("is_active", "role")
    search_fields = ("user__username", "role__code")
    autocomplete_fields = ("user", "role", "assigned_by")
    raw_id_fields = ("user", "assigned_by")


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    inlines = (UserRoleInline,)
    ordering = ("username",)
    list_display = (
        "username",
        "email",
        "employee_code",
        "department",
        "manager",
        "is_staff",
        "is_active",
    )
    list_filter = ("is_staff", "is_active", "department", "is_superuser")
    search_fields = ("username", "email", "employee_code", "first_name", "last_name")
    autocomplete_fields = ("manager",)
    readonly_fields = ("created_at", "updated_at", "last_login", "date_joined")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            _("Personal info"),
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "mobile",
                    "employee_code",
                    "department",
                    "job_title",
                    "manager",
                )
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "password1",
                    "password2",
                    "email",
                    "employee_code",
                    "department",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )
