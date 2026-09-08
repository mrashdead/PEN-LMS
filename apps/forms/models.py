"""
Dynamic form builder models.

FormSchema      — versioned, immutable form definition (fields as JSON).
FormSubmission  — a filled instance of a schema version (data as JSON).
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


class FormSchema(DomainModel):
    """A versioned form definition. ``(slug, version)`` is unique."""

    slug = models.SlugField(max_length=120, db_index=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
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
    client_ip = models.GenericIPAddressField(null=True, blank=True)
    last_action_at = models.DateTimeField(null=True, blank=True)

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
