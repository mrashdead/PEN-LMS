# apps/accounts/admin.py
from __future__ import annotations

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import Role, User, UserRole
from apps.accounts.role_policy import LEGACY_ROLE_CODES
from apps.core.admin import JalaliAdminMixin


class UserRoleAdminForm(forms.ModelForm):
    class Meta:
        model = UserRole
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        active_assignable = Role.all_objects.filter(
            is_active=True,
            is_deleted=False,
        ).exclude(code__in=LEGACY_ROLE_CODES)
        if self.instance.pk and self.instance.role_id:
            active_assignable = Role.all_objects.filter(
                Q(pk=self.instance.role_id)
                | (
                    Q(is_active=True, is_deleted=False)
                    & ~Q(code__in=LEGACY_ROLE_CODES)
                ),
            )
        self.fields["role"].queryset = active_assignable


class UserRoleInline(admin.TabularInline):
    model = UserRole
    form = UserRoleAdminForm
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
class RoleAdmin(JalaliAdminMixin, admin.ModelAdmin):
    list_display = ("code", "name", "priority", "is_active", "created_at_jalali_display")
    list_filter = ("is_active",)
    search_fields = ("code", "name")
    ordering = ("priority", "code")
    prepopulated_fields = {"code": ("name",)}
    readonly_fields = ("created_at_jalali_display", "updated_at_jalali_display", "created_at", "updated_at")


@admin.register(UserRole)
class UserRoleAdmin(JalaliAdminMixin, admin.ModelAdmin):
    form = UserRoleAdminForm
    list_display = (
        "user",
        "role",
        "is_active",
        "valid_from",
        "valid_to",
        "assigned_by",
        "created_at_jalali_display",
    )
    list_filter = ("is_active", "role")
    search_fields = ("user__username", "role__code")
    autocomplete_fields = ("user", "role", "assigned_by")
    raw_id_fields = ("user", "assigned_by")
    readonly_fields = ("created_at_jalali_display", "updated_at_jalali_display", "created_at", "updated_at")


@admin.register(User)
class UserAdmin(JalaliAdminMixin, DjangoUserAdmin):
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
        "created_at_jalali_display",
    )
    list_filter = ("is_staff", "is_active", "department", "is_superuser")
    search_fields = ("username", "email", "employee_code", "first_name", "last_name")
    autocomplete_fields = ("manager",)
    readonly_fields = ("created_at_jalali_display", "updated_at_jalali_display", "created_at", "updated_at", "last_login", "date_joined")

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
        (
            _("Important dates"),
            {
                "fields": ("last_login", "date_joined", "created_at_jalali_display", "updated_at_jalali_display")
            },
        ),
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
