from __future__ import annotations

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import DomainModel


class WorkflowDefinition(DomainModel):
    """
    قالب یک فرآیند — مثلاً «مرخصی»، «ماموریت»، «درخواست خرید».
    """

    code = models.SlugField(
        max_length=64,
        unique=True,
        help_text="Business key, e.g. leave-request, mission-order",
    )
    name = models.CharField(max_length=256)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        app_label = "workflow"
        db_table = "workflow_definition"
        verbose_name = "Workflow Definition"
        verbose_name_plural = "Workflow Definitions"
        ordering = ("code", "version")
        permissions = [
            ("manage_workflow_definition", "مدیریت تعاریف فرآیند"),
        ]
        indexes = [
            models.Index(fields=["code", "is_active"]),
            models.Index(fields=["version"]),
        ]

    def __str__(self) -> str:
        return f"{self.code} v{self.version}"

    def clean(self) -> None:
        self.code = (self.code or "").strip().lower()
        if not self.code:
            raise ValidationError({"code": "code is required"})

    def save(self, *args, **kwargs) -> None:
        self.code = (self.code or "").strip().lower()
        super().save(*args, **kwargs)


class State(DomainModel):
    """
    یک وضعیت در تعریف فرآیند.
    مثال: draft, pending-manager, pending-hr, approved, rejected
    """

    workflow_definition = models.ForeignKey(
        WorkflowDefinition,
        on_delete=models.CASCADE,
        related_name="states",
    )
    code = models.SlugField(max_length=64, help_text="e.g. pending-manager")
    name = models.CharField(max_length=256)
    is_initial = models.BooleanField(default=False, db_index=True)
    is_final = models.BooleanField(default=False, db_index=True)

    class Meta:
        app_label = "workflow"
        db_table = "workflow_state"
        verbose_name = "State"
        verbose_name_plural = "States"
        ordering = ("workflow_definition", "code")
        constraints = [
            models.UniqueConstraint(
                fields=["workflow_definition", "code"],
                name="uniq_workflow_state_code_per_wf",
            ),
        ]
        indexes = [
            models.Index(fields=["workflow_definition", "is_initial"]),
            models.Index(fields=["workflow_definition", "is_final"]),
        ]

    def __str__(self) -> str:
        return f"{self.workflow_definition.code}/{self.code}"

    def clean(self) -> None:
        self.code = (self.code or "").strip().lower()
        if not self.code:
            raise ValidationError({"code": "code is required"})
        if self.is_initial and self.is_final:
            raise ValidationError("A state cannot be both initial and final.")

    def save(self, *args, **kwargs) -> None:
        self.code = (self.code or "").strip().lower()
        super().save(*args, **kwargs)


class Transition(DomainModel):
    """
    قانون جابه‌جایی از یک State به State دیگر.
    مشخص می‌کند چه نقشی می‌تواند این انتقال را انجام دهد.
    """

    workflow_definition = models.ForeignKey(
        WorkflowDefinition,
        on_delete=models.CASCADE,
        related_name="transitions",
    )
    from_state = models.ForeignKey(
        State,
        on_delete=models.CASCADE,
        related_name="outgoing_transitions",
    )
    to_state = models.ForeignKey(
        State,
        on_delete=models.CASCADE,
        related_name="incoming_transitions",
    )
    name = models.CharField(max_length=256, help_text="e.g. approve, reject, submit")
    allowed_role_codes = models.JSONField(
        default=list,
        blank=True,
        help_text='List of role codes allowed to perform this transition, e.g. ["manager"]',
    )
    requires_comment = models.BooleanField(default=False)
    guard_expression = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Optional guard conditions as JSON. Examples:\n"
            '{"type": "always_true"}\n'
            '{"type": "role_not_in", "roles": ["manager"], "field": "requester"}\n'
            '{"type": "entity_field_lt", "field": "enrolled_count", "other_field": "capacity"}\n'
            '{"type": "all", "guards": [...]}\n'
            '{"type": "any", "guards": [...]}\n'
            "Empty/{} = always true (allow). Unknown type = deny (fail closed)."
        ),
    )

    class Meta:
        app_label = "workflow"
        db_table = "workflow_transition"
        verbose_name = "Transition"
        verbose_name_plural = "Transitions"
        ordering = ("workflow_definition", "from_state", "to_state")
        indexes = [
            models.Index(fields=["workflow_definition", "from_state"]),
            models.Index(fields=["workflow_definition", "to_state"]),
        ]

    def __str__(self) -> str:
        return (
            f"{self.workflow_definition.code}: {self.from_state.code}"
            f" → {self.to_state.code} ({self.name})"
        )

    def clean(self) -> None:
        if self.from_state_id and self.to_state_id and self.from_state_id == self.to_state_id:
            raise ValidationError("from_state and to_state cannot be the same.")
        if self.from_state and self.to_state:
            if self.from_state.workflow_definition_id != self.workflow_definition_id:
                raise ValidationError("from_state must belong to the same workflow definition.")
            if self.to_state.workflow_definition_id != self.workflow_definition_id:
                raise ValidationError("to_state must belong to the same workflow definition.")


class Instance(DomainModel):
    """
    یک اجرای زنده (یا تمام‌شده) از یک WorkflowDefinition.
    """

    class Status(models.TextChoices):
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"

    workflow_definition = models.ForeignKey(
        WorkflowDefinition,
        on_delete=models.PROTECT,
        related_name="instances",
    )
    current_state = models.ForeignKey(
        State,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="instances",
    )
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="workflow_instances",
    )
    title = models.CharField(max_length=512)
    description = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.RUNNING,
        db_index=True,
    )

    class Meta:
        app_label = "workflow"
        db_table = "workflow_instance"
        verbose_name = "Instance"
        verbose_name_plural = "Instances"
        ordering = ("-created_at",)
        permissions = [
            ("view_all_instances", "مشاهده همه درخواست‌ها"),
            ("approve_instance", "تأیید درخواست"),
            ("cancel_any_instance", "لغو هر درخواست"),
        ]
        indexes = [
            models.Index(fields=["workflow_definition", "status"]),
            models.Index(fields=["requester", "status"]),
            models.Index(fields=["current_state"]),
        ]

    def __str__(self) -> str:
        return f"{self.workflow_definition.code}/{self.title} [{self.status}]"


class ActionLog(DomainModel):
    """
    تاریخچهٔ قطعی هر اقدام روی یک Instance.
    """

    instance = models.ForeignKey(
        Instance,
        on_delete=models.CASCADE,
        related_name="action_logs",
    )
    from_state = models.ForeignKey(
        State,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="action_logs_from",
    )
    to_state = models.ForeignKey(
        State,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="action_logs_to",
    )
    action = models.CharField(
        max_length=64,
        db_index=True,
        help_text="e.g. submit, approve, reject, cancel",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="action_logs",
    )
    comment = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        app_label = "workflow"
        db_table = "workflow_action_log"
        verbose_name = "Action Log"
        verbose_name_plural = "Action Logs"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["instance", "created_at"]),
            models.Index(fields=["actor", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.instance_id}: {self.action} by {self.actor_id}"


class EntityWorkflow(DomainModel):
    """
    GenericForeignKey bridge: connects a Workflow Instance to any domain entity
    (CourseOffering, Lead, GradeForm, …) so transitions can inspect the entity's
    state without a direct FK on Instance.
    """

    instance = models.ForeignKey(
        Instance,
        on_delete=models.CASCADE,
        related_name="entity_links",
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
    )
    object_id = models.UUIDField(db_index=True)
    entity = GenericForeignKey("content_type", "object_id")

    class Meta:
        app_label = "workflow"
        db_table = "workflow_entity_link"
        verbose_name = "Entity Workflow Link"
        verbose_name_plural = "Entity Workflow Links"
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "object_id"],
                name="uniq_workflow_entity_link",
            ),
        ]
        indexes = [
            models.Index(fields=["instance", "content_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.instance_id} ↔ {self.content_type}.{self.object_id}"
