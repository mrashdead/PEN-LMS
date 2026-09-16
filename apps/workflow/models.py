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
    default_due_hours = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="مهلت پیش‌فرض تسک‌های این وضعیت (ساعت). خالی = بدون مهلت.",
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
    kind = models.CharField(
        max_length=32,
        blank=True,
        default="",
        help_text=(
            "نوع معنایی انتقال برای سرویس‌های سطح‌بالاتر: approve, reject, "
            "return, complete, submit. خالی = سفارشی (فقط نام)."
        ),
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
    # ── شناسه پیگیری (Tracking ID) ─────────────────────────────────────────
    # The card-table needs a short human-readable code to quote in calls/SMS;
    # a UUID is not dictatable. Allocated inside create_instance from
    # ``RequestSequence`` (year-scoped), so it survives soft-delete without
    # reuse — same rule as FormSubmission.submission_number (B-round).
    tracking_number = models.CharField(
        max_length=32, blank=True, default="", db_index=True,
        help_text="شناسه پیگیری انسانی، مثال REQ-2026-000123 — هنگام ایجاد پر می‌شود.",
    )

    class Meta:
        app_label = "workflow"
        db_table = "workflow_instance"
        verbose_name = "Instance (نمونه فرآیند)"
        verbose_name_plural = "Instances (نمونه‌های فرآیند)"
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["tracking_number"],
                condition=models.Q(is_deleted=False) & ~models.Q(tracking_number=""),
                name="uniq_workflow_tracking_number_alive",
            ),
        ]
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
    idempotency_key = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text=(
            "کلید یکتای کلاینت برای جلوگیری از اجرای دوباره (double-click / "
            "retry). کلید تکراری => همان نتیجه‌ی اول بازگردانده می‌شود نه خطا."
        ),
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
        constraints = [
            # Replay-safety (§13-3): one transition per client key. NULLs are
            # unlimited (older logs / logs without a key).
            models.UniqueConstraint(
                fields=["idempotency_key"],
                condition=models.Q(idempotency_key__isnull=False),
                name="uniq_workflow_actionlog_idempotency_key",
            ),
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


class ApprovalRecord(DomainModel):
    """
    رکورد تایید مستقل از status (§14.5 گزارش مهندسی / B6).

    «تایید» یک تغییر وضعیت نیست؛ یک رخداد امضاشده است:
      چه کسی (approver)، با چه نقشی (role_code)، در چه واحدی (unit)،
      روی کدام وضعیت/انتقال (state/transition)، در چه زمانی، با چه توضیحی —
      و آیا قابل پس‌گرفتن است (revoked_at).
    execute_transition هر بار که kind/name انتقال approve باشد یک رکورد
    می‌سازد؛ sync_status forms هم می‌تواند آخرین رکورد را بخواند.
    """

    instance = models.ForeignKey(
        Instance,
        on_delete=models.CASCADE,
        related_name="approvals",
    )
    transition = models.ForeignKey(
        Transition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approval_records",
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="workflow_approvals",
    )
    role_code = models.CharField(
        max_length=64, blank=True, default="",
        help_text="نقش موثر تاییدکننده در لحظه‌ی تایید.",
    )
    unit = models.CharField(
        max_length=128, blank=True, default="",
        help_text="واحد/دپارتمان تاییدکننده (رشته آزاد تا مدل سازمان ساخته شود).",
    )
    action = models.CharField(
        max_length=64,
        help_text="approve / reject / return …",
    )
    comment = models.TextField(blank=True, default="")
    state = models.ForeignKey(
        State, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="approval_records",
        help_text="وضعیتی که تایید در آن انجام شد.",
    )
    is_revoked = models.BooleanField(default=False, db_index=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="revoked_approvals",
    )

    class Meta:
        app_label = "workflow"
        db_table = "workflow_approval_record"
        verbose_name = "Approval Record (رکورد تایید)"
        verbose_name_plural = "Approval Records (رکوردهای تایید)"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["instance", "created_at"]),
            models.Index(fields=["approver", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.instance_id}: {self.action} by {self.approver_id}"


class InstanceCopy(DomainModel):
    """
    رونوشت (§14.4 send_copy / B6): ارسال یک نمونه برای اطلاع به کاربر دیگر.
    گیرنده‌ی رونوشت می‌بیند اما مسئول اقدام نیست (تسکی برایش ساخته نمی‌شود).
    """

    instance = models.ForeignKey(
        Instance,
        on_delete=models.CASCADE,
        related_name="copies",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workflow_copies_received",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="workflow_copies_sent",
    )
    note = models.CharField(max_length=500, blank=True, default="")
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "workflow"
        db_table = "workflow_instance_copy"
        verbose_name = "Instance Copy (رونوشت)"
        verbose_name_plural = "Instance Copies (رونوشت‌ها)"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["recipient", "read_at"]),
            models.Index(fields=["instance", "recipient"]),
        ]

    def __str__(self) -> str:
        return f"{self.instance_id} → {self.recipient_id}"


class NotificationOutbox(DomainModel):
    """
    صندوق خروجی اعلان‌ها (B6): هیچ ارسال بیرونی (ایمیل/SMS) داخل تراکنشِ
    انتقال انجام نمی‌شود؛ رخداد اینجا صف می‌شود و یک worker (یا فراخوانی
    after-commit) آن را تحویل می‌دهد. خرابی ارسال هرگز تراکنش گردش‌کار را
    برنمی‌گرداند (§6 گزارش: «ارسال email نباید transaction اصلی را وابسته کند»).
    """

    class Channel(models.TextChoices):
        IN_APP = "in_app", "درون‌برنامه"
        EMAIL = "email", "ایمیل"
        SMS = "sms", "پیامک"

    class Status(models.TextChoices):
        PENDING = "pending", "در انتظار ارسال"
        SENT = "sent", "ارسال‌شده"
        FAILED = "failed", "ناموفق"

    instance = models.ForeignKey(
        Instance,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workflow_notifications",
    )
    channel = models.CharField(
        max_length=16, choices=Channel.choices, default=Channel.IN_APP, db_index=True,
    )
    template = models.CharField(
        max_length=64, blank=True, default="",
        help_text="کلید قالب اعلان — مثلاً task_created, approved, rejected.",
    )
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True,
    )
    attempts = models.PositiveSmallIntegerField(default=0)
    last_error = models.TextField(blank=True, default="")
    sent_at = models.DateTimeField(null=True, blank=True)
    # Read receipt for in-app notifications (delivery status ≠ viewed).
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "workflow"
        db_table = "workflow_notification_outbox"
        verbose_name = "Notification Outbox (صندوق خروجی اعلان)"
        verbose_name_plural = "Notification Outbox (اعلان‌های خروجی)"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["recipient", "status"]),
            # User inbox queries: "my in-app, unread, newest first".
            models.Index(fields=["recipient", "channel", "is_read"]),
        ]

    def __str__(self) -> str:
        return f"{self.instance_id} → {self.recipient_id} [{self.channel}/{self.status}]"


class RequestSequence(models.Model):
    """
    Per-year counter backing the human Tracking ID (``Instance.tracking_number``).

    The sequence is GLOBAL per year — not per workflow code — because
    ``tracking_number`` carries only ``REQ-<year>-N``: a per-code counter made
    ``REQ-2026-000001`` collide across ``leave-request`` and every other first
    request of the year, and the live-unique index rejected it (the exact
    failure the first migrate produced on real data). A global counter makes
    uniqueness structural, and the short number stays dictatable over the
    phone — which is the whole purpose of a tracking ID. The workflow type is
    one JOIN away whenever it matters.

    Deliberately NOT a DomainModel: pure counter infrastructure with no
    identity; soft-delete semantics would make "the next number" ambiguous.
    Mirrors forms.SubmissionSequence — PostgreSQL serialises the bump with
    ``select_for_update``; SQLite (tests) falls back to the unique constraint.
    Production concurrency backend is PostgreSQL (per the project's stated
    architecture).
    """

    year = models.PositiveIntegerField(unique=True)
    last_value = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "workflow"
        db_table = "workflow_request_sequence"
        verbose_name = "Request Sequence (شمارنده پیگیری)"
        verbose_name_plural = "Request Sequences (شمارنده‌های پیگیری)"
        ordering = ("year",)

    def __str__(self) -> str:
        return f"REQ-{self.year}={self.last_value}"