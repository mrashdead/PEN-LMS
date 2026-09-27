"""
Dynamic form builder models.

RequestType     — business request catalog item connected to a form/workflow.
FormSchema      — versioned, immutable form definition (fields as JSON).
FormSubmission  — a filled instance of a schema version (data as JSON).
Request         — the unified business request aggregate over a submission.
FormAttachment  — private file uploaded against a ``file`` field.
FormComment     — threaded comment on a submission (internal flag).
SubmissionSequence — per-(slug, year) counter for concurrency-safe numbers.

All domain models reuse ``DomainModel`` (UUID PK + timestamps + soft delete).
Submitted (non-draft) submissions are immutable through the ordinary update
API — enforced in ``services.FormSubmissionService`` and API permissions.
"""
from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.core.models import DomainModel
from apps.forms.schema_validation import SchemaDefinitionError, validate_form_fields
from apps.forms.storage import build_upload_path, private_storage


def default_workflow_config() -> dict:
    return {
        "execution_mode": "direct",
        "allow_on_behalf": False,
        "eligible_initiator_roles": [],
        "routing_rules": [],
    }


class RequestType(DomainModel):
    """Catalog entry describing what a submitted form means to the business.

    A form answers *which data should be collected*.  A request type answers
    *what business process that data starts*.  Keeping the catalog separate
    from ``FormSchema`` lets multiple schema versions share one business
    process while the workflow definition remains configurable.
    """

    class Kind(models.TextChoices):
        INFORMATIONAL = "informational", "اطلاعاتی"
        REQUEST = "request", "درخواستی"
        OPERATIONAL = "operational", "عملیاتی"

    code = models.SlugField(max_length=120, unique=True, db_index=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    kind = models.CharField(
        max_length=20,
        choices=Kind.choices,
        default=Kind.REQUEST,
        db_index=True,
    )
    is_active = models.BooleanField(default=True, db_index=True)
    workflow_definition = models.ForeignKey(
        "workflow.WorkflowDefinition",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="request_types",
    )
    allowed_roles = models.ManyToManyField(
        "accounts.Role",
        related_name="request_types",
        blank=True,
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        app_label = "forms"
        db_table = "forms_request_type"
        verbose_name = "Request Type (نوع درخواست)"
        verbose_name_plural = "Request Types (انواع درخواست)"
        ordering = ("code",)
        indexes = [
            models.Index(fields=["code", "is_active"], name="forms_reque_code_f2b6d4_idx"),
            models.Index(fields=["kind", "is_active"], name="forms_reque_kind_a31fed_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.code} — {self.title}"

    def clean(self) -> None:
        self.code = (self.code or "").strip().lower()
        if not self.code:
            raise ValidationError({"code": "کد نوع درخواست الزامی است."})

    def save(self, *args, **kwargs) -> None:
        self.code = (self.code or "").strip().lower()
        super().save(*args, **kwargs)


class FormSchema(DomainModel):
    """A versioned form definition. ``(slug, version)`` is unique."""

    class Category(models.TextChoices):
        PERSONS = "persons", "افراد"
        DEPARTMENTS = "departments", "دپارتمان‌ها"
        COURSES = "courses", "درس‌ها و دوره‌ها"
        CLASSES = "classes", "برگزاری‌ها و کلاس‌ها"
        MESSAGES = "messages", "پیام‌ها"
        GENERAL = "general", "سایر خدمات"

    slug = models.SlugField(max_length=120, db_index=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    category = models.CharField(
        max_length=24, choices=Category.choices, default=Category.GENERAL, db_index=True,
    )
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True, db_index=True)
    allowed_roles = models.ManyToManyField(
        "accounts.Role",
        related_name="form_schemas",
        blank=True,
    )
    fields = models.JSONField(
        default=list,
        help_text="Ordered list of FieldDefinition objects (see schema_validation).",
    )
    request_type = models.ForeignKey(
        RequestType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="form_schemas",
        help_text="نوع کسب‌وکاری درخواستی که این نسخهٔ فرم ایجاد می‌کند.",
    )
    workflow_definition = models.ForeignKey(
        "workflow.WorkflowDefinition",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="form_schemas",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_form_schemas",
    )
    published_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    workflow_config = models.JSONField(
        default=default_workflow_config,
        blank=True,
        help_text=(
            "تنظیمات اجرای فرم: execution_mode, allow_on_behalf, "
            "eligible_initiator_roles و routing_rules."
        ),
    )

    class Meta:
        app_label = "forms"
        db_table = "forms_schema"
        verbose_name = "Form Schema"
        verbose_name_plural = "Form Schemas"
        ordering = ("slug", "-version")
        constraints = [
            models.UniqueConstraint(
                fields=["slug", "version"],
                name="uniq_forms_schema_slug_version",
            ),
            # Only one active version per slug (partial unique index).
            models.UniqueConstraint(
                fields=["slug"],
                condition=models.Q(is_active=True, is_deleted=False),
                name="uniq_forms_schema_active_per_slug",
            ),
        ]
        indexes = [
            models.Index(fields=["slug", "is_active"]),
            models.Index(fields=["workflow_definition"]),
        ]

    def __str__(self) -> str:
        return f"{self.slug} v{self.version}"

    @property
    def field_map(self) -> dict[str, dict]:
        return {f["key"]: f for f in self.fields}

    def clean(self) -> None:
        try:
            validate_form_fields(self.fields)
        except SchemaDefinitionError as exc:
            raise ValidationError({"fields": str(exc)}) from exc

    def save(self, *args, **kwargs) -> None:
        if self.is_active and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)


class FormSubmission(DomainModel):
    """A submission of a specific FormSchema version."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        PROCESSING = "processing", "Processing"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        ARCHIVED = "archived", "Archived"

    class ProjectionStatus(models.TextChoices):
        NOT_APPLICABLE = "not_applicable", "Not applicable"
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETE = "complete", "Complete"
        FAILED = "failed", "Failed"

    #: Statuses after which the submission is immutable via the update API.
    IMMUTABLE_STATUSES = {
        Status.SUBMITTED, Status.PROCESSING,
        Status.APPROVED, Status.REJECTED, Status.ARCHIVED,
    }

    form_schema = models.ForeignKey(
        FormSchema,
        on_delete=models.PROTECT,
        related_name="submissions",
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="form_submissions",
    )
    initiator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="initiated_form_submissions",
    )
    subject_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subject_form_submissions_as_user",
    )
    is_on_behalf = models.BooleanField(default=False, db_index=True)
    data = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.DRAFT, db_index=True,
    )
    workflow_instance = models.ForeignKey(
        "workflow.Instance",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="form_submissions",
    )
    submission_number = models.CharField(
        max_length=200, unique=True, null=True, blank=True,
        help_text="FORM-{SLUG}-{YEAR}-{SEQ}; NULL until allocated.",
    )
    # ── Denormalized visibility columns ────────────────────────────────────
    # Derived by the service from validated relation fields so that
    # get_queryset() can scope teacher/student/parent access with bounded SQL
    # instead of scanning JSON payloads.
    class_group = models.ForeignKey(
        "academics.ClassGroup",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="form_submissions",
        help_text="کلاس مرتبط — برای محدودسازی دسترسی معلم",
    )
    subject_person = models.ForeignKey(
        "persons.Person",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subject_form_submissions",
        help_text="شخص مرتبط (دانش‌آموز/مدرس) — برای محدودسازی دسترسی دانش‌آموز و والدین",
    )
    notes = models.TextField(blank=True, default="")
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_form_submissions",
    )
    schema_version_snapshot = models.PositiveIntegerField(default=1)
    version_snapshot = models.JSONField(
        default=dict,
        blank=True,
        help_text="Immutable copy of the schema fields at submission time.",
    )
    schema_snapshot = models.JSONField(
        default=dict,
        blank=True,
        help_text="Snapshot تغییرناپذیر schema و تنظیمات اجرا در زمان ثبت.",
    )
    client_ip = models.GenericIPAddressField(null=True, blank=True)
    last_action_at = models.DateTimeField(null=True, blank=True)
    projection_status = models.CharField(
        max_length=20,
        choices=ProjectionStatus.choices,
        default=ProjectionStatus.NOT_APPLICABLE,
        db_index=True,
    )
    projection_attempts = models.PositiveSmallIntegerField(default=0)
    projection_next_attempt_at = models.DateTimeField(null=True, blank=True, db_index=True)
    projection_last_error = models.TextField(blank=True, default="")

    class Meta:
        app_label = "forms"
        db_table = "forms_submission"
        verbose_name = "Form Submission"
        verbose_name_plural = "Form Submissions"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["form_schema", "submitted_by", "status"]),
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["submitted_by", "created_at"]),
            models.Index(fields=["form_schema", "created_at"]),
            models.Index(fields=["class_group"]),
            models.Index(fields=["subject_person"]),
        ]

    def __str__(self) -> str:
        return self.submission_number or f"{self.form_schema_id}/{self.pk}"

    @property
    def is_immutable(self) -> bool:
        return self.status in self.IMMUTABLE_STATUSES

    def effective_fields(self) -> list[dict]:
        """Fields to validate against: the snapshot if present, else schema."""
        snap = self.version_snapshot or {}
        return snap.get("fields") or self.form_schema.fields


class Request(DomainModel):
    """Unified business request aggregate backed by a form submission.

    ``FormSubmission`` remains the compatibility/data-capture record.  This
    model gives the product a stable business vocabulary: requester, subject,
    request type and lifecycle.  Workflow execution is still owned by
    ``workflow.Instance`` and is reached through ``form_submission``.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "پیش‌نویس"
        SUBMITTED = "submitted", "ارسال‌شده"
        IN_REVIEW = "in_review", "در حال بررسی"
        AWAITING_ACTION = "awaiting_action", "منتظر اقدام"
        CHANGES_REQUESTED = "changes_requested", "نیازمند اصلاح"
        APPROVED = "approved", "تأییدشده"
        REJECTED = "rejected", "ردشده"
        CANCELLED = "cancelled", "لغوشده"
        COMPLETED = "completed", "تکمیل‌شده"
        BLOCKED_ASSIGNMENT = "blocked_assignment", "بدون مسئول"
        ARCHIVED = "archived", "بایگانی‌شده"

    request_type = models.ForeignKey(
        RequestType,
        on_delete=models.PROTECT,
        related_name="requests",
    )
    form_submission = models.OneToOneField(
        FormSubmission,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="business_request",
    )
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="business_requests",
    )
    initiator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="initiated_requests",
    )
    subject_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="beneficiary_requests",
    )
    is_on_behalf = models.BooleanField(default=False, db_index=True)
    schema_snapshot = models.JSONField(default=dict, blank=True)
    subject_person = models.ForeignKey(
        "persons.Person",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="business_requests",
    )
    request_number = models.CharField(
        max_length=200,
        unique=True,
        null=True,
        blank=True,
        help_text="شمارهٔ قابل پیگیری؛ معمولاً از شمارهٔ submission یا workflow می‌آید.",
    )
    status = models.CharField(
        max_length=24,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_action_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        app_label = "forms"
        db_table = "forms_request"
        verbose_name = "Request (درخواست)"
        verbose_name_plural = "Requests (درخواست‌ها)"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["request_type", "status"], name="forms_reque_request_b4571c_idx"),
            models.Index(fields=["requester", "status"], name="forms_reque_request_b2cbee_idx"),
            models.Index(fields=["subject_person", "status"], name="forms_reque_subject_622f33_idx"),
            models.Index(fields=["status", "created_at"], name="forms_reque_status_c362c3_idx"),
        ]

    def __str__(self) -> str:
        return self.request_number or f"{self.request_type.code}/{self.pk}"

    @property
    def workflow_instance(self):
        submission = self.form_submission
        return getattr(submission, "workflow_instance", None) if submission else None

    @property
    def workflow_instance_id(self):
        instance = self.workflow_instance
        return getattr(instance, "pk", None)

    @property
    def current_state(self):
        instance = self.workflow_instance
        return getattr(instance, "current_state", None)

    @property
    def is_terminal(self) -> bool:
        return self.status in {
            self.Status.APPROVED,
            self.Status.REJECTED,
            self.Status.CANCELLED,
            self.Status.COMPLETED,
            self.Status.ARCHIVED,
        }


class FormAttachment(DomainModel):
    """A privately-stored file uploaded against a ``file`` field."""

    submission = models.ForeignKey(
        FormSubmission,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    field_key = models.CharField(max_length=100)
    file = models.FileField(
        upload_to=build_upload_path,
        storage=private_storage,
        max_length=500,
    )
    original_filename = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=150)
    file_size = models.PositiveBigIntegerField()
    checksum = models.CharField(max_length=128, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="form_attachments",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "forms"
        db_table = "forms_attachment"
        verbose_name = "Form Attachment"
        verbose_name_plural = "Form Attachments"
        ordering = ("uploaded_at",)
        indexes = [
            models.Index(fields=["submission", "field_key"]),
        ]

    def __str__(self) -> str:
        return f"{self.original_filename} ({self.field_key})"


class FormComment(DomainModel):
    """Threaded comment on a submission; may be internal-only."""

    submission = models.ForeignKey(
        FormSubmission,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="form_comments",
    )
    body = models.TextField()
    is_internal = models.BooleanField(default=False)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
    )

    class Meta:
        app_label = "forms"
        db_table = "forms_comment"
        verbose_name = "Form Comment"
        verbose_name_plural = "Form Comments"
        ordering = ("created_at",)
        indexes = [
            models.Index(fields=["submission", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"comment by {self.author_id} on {self.submission_id}"

    def clean(self) -> None:
        if self.parent_id:
            if self.parent_id == self.pk:
                raise ValidationError({"parent": "A comment cannot reply to itself."})
            if self.parent.submission_id != self.submission_id:
                raise ValidationError(
                    {"parent": "Parent comment must belong to the same submission."}
                )
            # Reject circular parent chains (walk up to the root).
            seen = {self.pk}
            node = self.parent
            while node is not None:
                if node.pk in seen:
                    raise ValidationError({"parent": "Circular comment thread detected."})
                seen.add(node.pk)
                node = node.parent


class SubmissionSequence(models.Model):
    """
    Per-(slug, year) counter backing concurrency-safe submission numbers.

    On PostgreSQL the row is locked with ``select_for_update()`` by the
    service layer. On SQLite (test backend) row locking is unavailable, so the
    service relies on the unique constraint on ``FormSubmission.submission_number``
    plus a bounded retry around the final insert. The DB unique constraint is
    always the final source of truth; a prior existence check is never trusted.

    PostgreSQL is the production concurrency backend; SQLite support exists
    so the test suite stays runnable.
    """

    slug = models.SlugField(max_length=120)
    year = models.PositiveIntegerField()
    last_value = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "forms"
        db_table = "forms_submission_sequence"
        verbose_name = "Submission Sequence"
        verbose_name_plural = "Submission Sequences"
        constraints = [
            models.UniqueConstraint(
                fields=["slug", "year"],
                name="uniq_forms_submission_sequence",
            ),
        ]
        indexes = [
            models.Index(fields=["slug", "year"]),
        ]

    def __str__(self) -> str:
        return f"{self.slug}/{self.year}={self.last_value}"
