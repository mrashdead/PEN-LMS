from __future__ import annotations

from django.contrib import admin

from apps.workflow.models import ActionLog, Instance, State, Transition, WorkflowDefinition


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
class WorkflowDefinitionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "version", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("code", "name")
    ordering = ("code", "version")
    readonly_fields = ("created_at", "updated_at")
    inlines = (StateInline, TransitionInline)


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "workflow_definition", "is_initial", "is_final")
    list_filter = ("is_initial", "is_final", "workflow_definition")
    search_fields = ("code", "name", "workflow_definition__code")
    autocomplete_fields = ("workflow_definition",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Transition)
class TransitionAdmin(admin.ModelAdmin):
    list_display = ("name", "workflow_definition", "from_state", "to_state", "requires_comment")
    list_filter = ("workflow_definition", "requires_comment")
    search_fields = ("name", "workflow_definition__code", "from_state__code", "to_state__code")
    autocomplete_fields = ("workflow_definition", "from_state", "to_state")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("workflow_definition", "name")}),
        ("States", {"fields": ("from_state", "to_state")}),
        ("Permissions", {"fields": ("allowed_role_codes", "requires_comment")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(Instance)
class InstanceAdmin(admin.ModelAdmin):
    list_display = ("title", "workflow_definition", "current_state", "requester", "status", "created_at")
    list_filter = ("status", "workflow_definition")
    search_fields = ("title", "requester__username", "workflow_definition__code")
    autocomplete_fields = ("workflow_definition", "current_state", "requester")
    readonly_fields = ("created_at", "updated_at")


@admin.register(ActionLog)
class ActionLogAdmin(admin.ModelAdmin):
    list_display = ("instance", "action", "actor", "from_state", "to_state", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("instance__title", "actor__username", "action")
    autocomplete_fields = ("instance", "from_state", "to_state", "actor")
    readonly_fields = ("created_at", "updated_at")
