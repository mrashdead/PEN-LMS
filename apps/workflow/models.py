"""
Workflow Engine Models

مدل‌های هسته موتور گردش کار:
  - WorkflowDefinition: قالب یک فرآیند (مثلاً «مرخصی»، «ثبت نمره»)
  - State: یک وضعیت در فرآیند (draft, pending-manager, approved, ...)
  - Transition: قانون جابه‌جایی بین دو وضعیت + شرط نقش + شرط پیشرفته (guard)
  - Instance: یک اجرای زنده از یک فرآیند
  - ActionLog: تاریخچه قطعی هر اقدام
  - EntityWorkflow: پل GenericForeignKey بین Instance و هر موجودیت دامنه

تمامی مدل‌ها از DomainModel ارث‌بری می‌کنند که = UUID PK + TimeStamped + SoftDelete.
"""
from __future__ import annotations

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import DomainModel


class WorkflowDefinition(DomainModel):
    """
    قالب یک فرآیند — مثل «درخواست مرخصی»، «ثبت نمره»، «تعیین سطح».

    Each definition has:
      - States (وضعیت‌ها): multiple State records
      - Transitions (انتقال‌ها): multiple Transition records between states
      - Instances (نمونه‌ها): multiple running/completed instances
    """

    code = models.SlugField(
        max_length=64,
        unique=True,
        help_text="Business key / شناسه یکتای فرآیند — مثلاً leave-request, grade-submission",
    )
    name = models.CharField(
        max_length=256,
        help_text="نام نمایشی فرآیند — مثلاً «درخواست مرخصی»",
    )
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)
    version = models.PositiveIntegerField(
        default=1,
        help_text="نسخه — برای به‌روزرسانی تعریف بدون شکستن نمونه‌های در حال اجرا",
    )

    class Meta:
        app_label = "workflow"
        db_table = "workflow_definition"
        verbose_name = "Workflow Definition (تعریف فرآیند)"
        verbose_name_plural = "Workflow Definitions (تعاریف فرآیند)"
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
            raise ValidationError({"code": "وارد کردن code الزامی است."})

    def save(self, *args, **kwargs) -> None:
        self.code = (self.code or "").strip().lower()
        super().save(*args, **kwargs)


class State(DomainModel):
    """
    یک وضعیت در تعریف فرآیند.
    مثال: draft, pending-manager, pending-hr, approved, rejected

    هر State متعلق به یک WorkflowDefinition است.
    یک State می‌تواند is_initial (وضعیت شروع) یا is_final (وضعیت پایان) باشد.
    """

    workflow_definition = models.ForeignKey(
        WorkflowDefinition,
        on_delete=models.CASCADE,
        related_name="states",
    )
    code = models.SlugField(
        max_length=64,
        help_text="شناسه وضعیت — مثلاً pending-manager, approved",
    )
    name = models.CharField(
        max_length=256,
        help_text="نام نمایشی وضعیت — مثلاً «در انتظار تأیید مدیر»",
    )
    is_initial = models.BooleanField(
        default=False,
        db_index=True,
        help_text="آیا این وضعیت شروع فرآیند است؟",
    )
    is_final = models.BooleanField(
        default=False,
        db_index=True,
        help_text="آیا این وضعیت پایان فرآیند است؟",
    )

    class Meta:
        app_label = "workflow"
        db_table = "workflow_state"
        verbose_name = "State (وضعیت)"
        verbose_name_plural = "States (وضعیت‌ها)"
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
            raise ValidationError({"code": "وارد کردن code الزامی است."})
        if self.is_initial and self.is_final:
            raise ValidationError("یک State نمی‌تواند هم initial باشد هم final.")

    def save(self, *args, **kwargs) -> None:
        self.code = (self.code or "").strip().lower()
        super().save(*args, **kwargs)


class Transition(DomainModel):
    """
    قانون جابه‌جایی از یک State به State دیگر.

    هر Transition مشخص می‌کند:
      - از چه وضعیتی به چه وضعیتی می‌رود
      - چه نقش‌هایی مجاز به انجام آن هستند (allowed_role_codes)
      - آیا حتماً کامنت لازم است (requires_comment)
      - چه شرط پیشرفته‌ای دارد (guard_expression)

    guard_expression به صورت JSON تعریف می‌شود و توسط GuardEvaluator ارزیابی می‌گردد.
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
    name = models.CharField(
        max_length=256,
        help_text="نام اقدام — مثلاً submit, approve, reject",
    )
    allowed_role_codes = models.JSONField(
        default=list,
        blank=True,
        help_text=(
            'نقش‌های مجاز برای انجام این انتقال. مثال: ["manager"], ["hr", "admin"].\n'
            "خالی = همه می‌توانند (فقط با داشتن Instance و State مناسب)."
        ),
    )
    requires_comment = models.BooleanField(
        default=False,
        help_text="آیا کاربر حتماً باید کامنت وارد کند؟",
    )
    guard_expression = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "شرط پیشرفته برای این انتقال (JSON). مثال:\n"
            '{"type": "always_true"} — همیشه مجاز\n'
            '{"type": "field_not_equals", "field": "requester_id", "source": "actor.id"}\n'
            '    — مدیر نتواند درخواست خودش را تأیید کند\n'
            '{"type": "entity_field_lt", "field": "enrolled_count", "other_field": "capacity"}\n'
            '    — اگر ظرفیت پر است، اجازه تأیید نده\n'
            '{"type": "all", "guards": [...]} — همه زیرشرط‌ها باید درست باشند\n'
            '{"type": "any", "guards": [...]} — حداقل یکی از زیرشرط‌ها باید درست باشد\n'
            "خالی/{} = همیشه مجاز. نوع ناشناخته = مسدود (fail-closed)."
        ),
    )

    class Meta:
        app_label = "workflow"
        db_table = "workflow_transition"
        verbose_name = "Transition (انتقال)"
        verbose_name_plural = "Transitions (انتقال‌ها)"
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
        # جلوگیری از Transition به خودش
        if self.from_state_id and self.to_state_id and self.from_state_id == self.to_state_id:
            raise ValidationError("from_state و to_state نمی‌توانند یکی باشند.")
        # اطمینان از اینکه هر دو State متعلق به همین WorkflowDefinition هستند
        if self.from_state and self.to_state:
            if self.from_state.workflow_definition_id != self.workflow_definition_id:
                raise ValidationError("from_state باید متعلق به همین WorkflowDefinition باشد.")
            if self.to_state.workflow_definition_id != self.workflow_definition_id:
                raise ValidationError("to_state باید متعلق به همین WorkflowDefinition باشد.")


class Instance(DomainModel):
    """
    یک نمونه اجرایی (زنده یا تمام‌شده) از یک WorkflowDefinition.

    Instance مسیر خود را طی می‌کند:
      RUNNING → COMPLETED / REJECTED / CANCELLED

    هر Instance می‌تواند به یک موجودیت دامنه متصل شود
    (از طریق EntityWorkflow) تا Transitionها بتوانند
    فیلدهای آن موجودیت را بررسی کنند.
    """

    class Status(models.TextChoices):
        RUNNING = "running", "Running (در حال اجرا)"
        COMPLETED = "completed", "Completed (تکمیل)"
        REJECTED = "rejected", "Rejected (رد شده)"
        CANCELLED = "cancelled", "Cancelled (لغو شده)"

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
    title = models.CharField(
        max_length=512,
        help_text="عنوان درخواست — مثلاً «مرخصی ۳ روزه از ۱۵ تا ۱۷ مهر»",
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="توضیحات تکمیلی درخواست",
    )
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.RUNNING,
        db_index=True,
    )

    class Meta:
        app_label = "workflow"
        db_table = "workflow_instance"
        verbose_name = "Instance (نمونه فرآیند)"
        verbose_name_plural = "Instances (نمونه‌های فرآیند)"
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
    تاریخچه قطعی هر اقدام روی یک Instance.

    تمام تغییرات وضعیت در این جدول ثبت می‌شوند:
      - ایجاد Instance (action="create")
      - اجرای Transition (action=transition.name)
      - لغو (action="cancel")

    این جدول فقط Append-Only است — هیچوقت ویرایش یا حذف نمی‌شود.
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
        help_text="نام اقدام — create, submit, approve, reject, cancel",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="action_logs",
    )
    comment = models.TextField(
        blank=True,
        default="",
        help_text="کامنت کاربر در زمان انجام اقدام",
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="داده‌های اضافی (مثلاً مقادیر فرم در زمان ثبت)",
    )

    class Meta:
        app_label = "workflow"
        db_table = "workflow_action_log"
        verbose_name = "Action Log (تاریخچه)"
        verbose_name_plural = "Action Logs (تاریخچه‌ها)"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["instance", "created_at"]),
            models.Index(fields=["actor", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.instance_id}: {self.action} by {self.actor_id}"


class EntityWorkflow(DomainModel):
    """
    پل GenericForeignKey: Instance را به هر موجودیت دامنه متصل می‌کند.

    چرا به جای FK مستقیم؟
      - هر Instance ممکن است به انواع مختلفی از موجودیت‌ها وصل شود
        (CourseOffering, Lead, GradeForm, ...)
      - GenericForeignKey این تنوع را بدون چندین FK تهی ممکن می‌کند

    هر موجودیت حداکثر می‌تواند به یک Instance متصل شود
    (اجرا توسط UniqueConstraint روی content_type + object_id).
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
    object_id = models.UUIDField(
        db_index=True,
        help_text="PK موجودیت دامنه (UUID)",
    )
    entity = GenericForeignKey("content_type", "object_id")

    class Meta:
        app_label = "workflow"
        db_table = "workflow_entity_link"
        verbose_name = "Entity Workflow Link (اتصال موجودیت)"
        verbose_name_plural = "Entity Workflow Links (اتصالات موجودیت)"
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "object_id"],
                name="uniq_workflow_entity_link",
                violation_error_message="این موجودیت قبلاً به یک Instance دیگر متصل شده است.",
            ),
        ]
        indexes = [
            models.Index(fields=["instance", "content_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.instance_id} ↔ {self.content_type}.{self.object_id}"