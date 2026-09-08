from __future__ import annotations

from django.contrib import admin

from apps.core.admin import JalaliAdminMixin
from apps.forms.models import (
    FormAttachment,
    FormComment,
    FormSchema,
    FormSubmission,
    SubmissionSequence,
)


class FormCommentInline(admin.TabularInline):
    model = FormComment
    extra = 0
    fields = ("author", "body", "is_internal", "created_at")
    readonly_fields = ("created_at",)


class FormAttachmentInline(admin.TabularInline):
    model = FormAttachment
    extra = 0
    fields = ("field_key", "original_filename", "mime_type", "file_size", "uploaded_by", "uploaded_at")
    readonly_fields = ("uploaded_at",)


@admin.register(FormSchema)
class FormSchemaAdmin(JalaliAdminMixin, admin.ModelAdmin):
    list_display = ("slug", "title", "version", "is_active", "published_at", "created_at_jalali_display")
    list_filter = ("is_active", "slug")
    search_fields = ("slug", "title", "description")
    filter_horizontal = ("allowed_roles",)
    readonly_fields = ("published_at", "created_at_jalali_display", "updated_at_jalali_display")
    fieldsets = (
        ("مشخصات فرم", {"fields": ("slug", "title", "description", "version", "is_active")}),
        ("دسترسی", {"fields": ("allowed_roles", "workflow_definition", "created_by")}),
        ("تعریف فیلدها (JSON)", {"fields": ("fields", "metadata")}),
        ("سیستمی", {"fields": ("published_at", "created_at_jalali_display", "updated_at_jalali_display")}),
    )


@admin.register(FormSubmission)
class FormSubmissionAdmin(JalaliAdminMixin, admin.ModelAdmin):
    list_display = (
        "submission_number", "form_schema", "submitted_by", "status",
        "submitted_at", "created_at_jalali_display",
    )
    list_filter = ("status", "form_schema__slug")
    search_fields = ("submission_number", "submitted_by__username", "notes")
    autocomplete_fields = ("submitted_by", "reviewed_by")
    readonly_fields = (
        "submission_number", "version_snapshot", "schema_version_snapshot",
        "client_ip", "created_at_jalali_display", "updated_at_jalali_display",
    )
    inlines = (FormAttachmentInline, FormCommentInline)
    fieldsets = (
        ("اطلاعات فرم", {"fields": ("form_schema", "submitted_by", "status", "submission_number")}),
        ("داده پویا", {"fields": ("data", "notes")}),
        ("گردش کار", {"fields": ("workflow_instance", "reviewed_by", "reviewed_at", "submitted_at")}),
        ("اسنپ‌شات نسخه", {"fields": ("schema_version_snapshot", "version_snapshot")}),
        ("سیستمی", {"fields": ("client_ip", "created_at_jalali_display", "updated_at_jalali_display")}),
    )

    def has_delete_permission(self, request, obj=None):
        # Audit trail: submissions are soft-deleted via restore/soft_delete,
        # never hard-deleted from admin.
        return False


@admin.register(FormAttachment)
class FormAttachmentAdmin(admin.ModelAdmin):
    list_display = ("original_filename", "submission", "field_key", "mime_type", "file_size", "uploaded_by")
    list_filter = ("mime_type", "field_key")
    search_fields = ("original_filename", "submission__submission_number")
    readonly_fields = ("checksum", "file_size", "mime_type", "uploaded_at")


@admin.register(FormComment)
class FormCommentAdmin(admin.ModelAdmin):
    list_display = ("submission", "author", "is_internal", "created_at")
    list_filter = ("is_internal",)
    search_fields = ("body", "author__username")


@admin.register(SubmissionSequence)
class SubmissionSequenceAdmin(admin.ModelAdmin):
    list_display = ("slug", "year", "last_value", "updated_at")
    readonly_fields = ("updated_at",)
