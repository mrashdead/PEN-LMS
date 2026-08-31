from __future__ import annotations

from django.contrib import admin

from apps.core.admin import JalaliAdminMixin
from apps.workflow.models import ActionLog, EntityWorkflow, Instance, State, Transition, WorkflowDefinition


class StateInline(admin.TabularInline):
    model = State
    extra = 0
    fields = ("code", "name", "is_initial", "is_final")
    autocomplete_fields = ()


class TransitionInline(admin.TabularInline):
    model = Transition
    extra = 0
    fk_name = "workflow_definition"
    fields = ("from_state", "to_state", "name", "allowed_role_codes", "requires_comment")
    autocomplete_fields = ("from_state", "to_state")


@admin.register(WorkflowDefinition)
class WorkflowDefinitionAdmin(JalaliAdminMixin, admin.ModelAdmin):
    list_display = ("code", "name", "version", "is_active", "created_at_jalali_display")
    list_filter = ("is_active",)
    search_fields = ("code", "name")
    ordering = ("code", "version")
    readonly_fields = ("created_at_jalali_display", "updated_at_jalali_display", "created_at", "updated_at")
    inlines = (StateInline, TransitionInline)


@admin.register(State)
class StateAdmin(JalaliAdminMixin, admin.ModelAdmin):
    list_display = ("code", "name", "workflow_definition", "is_initial", "is_final", "created_at_jalali_display")
    list_filter = ("is_initial", "is_final", "workflow_definition")
    search_fields = ("code", "name", "workflow_definition__code")
    autocomplete_fields = ("workflow_definition",)
    readonly_fields = ("created_at_jalali_display", "updated_at_jalali_display", "created_at", "updated_at")


@admin.register(Transition)
class TransitionAdmin(JalaliAdminMixin, admin.ModelAdmin):
    list_display = ("name", "workflow_definition", "from_state", "to_state", "requires_comment", "created_at_jalali_display")
    list_filter = ("workflow_definition", "requires_comment")
    search_fields = ("name", "workflow_definition__code", "from_state__code", "to_state__code")
    autocomplete_fields = ("workflow_definition", "from_state", "to_state")
    readonly_fields = ("created_at_jalali_display", "updated_at_jalali_display", "created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("workflow_definition", "name")}),
        ("States", {"fields": ("from_state", "to_state")}),
        ("Permissions", {"fields": ("allowed_role_codes", "requires_comment", "guard_expression")}),
        ("Timestamps", {"fields": ("created_at_jalali_display", "updated_at_jalali_display")}),
    )


@admin.register(Instance)
class InstanceAdmin(JalaliAdminMixin, admin.ModelAdmin):
    list_display = ("title", "workflow_definition", "current_state", "requester", "status", "created_at_jalali_display")
    list_filter = ("status", "workflow_definition")
    search_fields = ("title", "requester__username", "workflow_definition__code")
    autocomplete_fields = ("workflow_definition", "current_state", "requester")
    readonly_fields = ("created_at_jalali_display", "updated_at_jalali_display", "created_at", "updated_at")


@admin.register(ActionLog)
class ActionLogAdmin(JalaliAdminMixin, admin.ModelAdmin):
    list_display = ("instance", "action", "actor", "from_state", "to_state", "created_at_jalali_display")
    list_filter = ("action", "created_at")
    search_fields = ("instance__title", "actor__username", "action")
    autocomplete_fields = ("instance", "from_state", "to_state", "actor")
    readonly_fields = ("created_at_jalali_display", "updated_at_jalali_display", "created_at", "updated_at")


@admin.register(EntityWorkflow)
class EntityWorkflowAdmin(JalaliAdminMixin, admin.ModelAdmin):
    list_display = ("instance", "content_type", "object_id", "created_at_jalali_display")
    list_filter = ("content_type",)
    search_fields = ("instance__title", "object_id")
    autocomplete_fields = ("instance",)
    readonly_fields = ("created_at_jalali_display", "updated_at_jalali_display", "created_at", "updated_at")
