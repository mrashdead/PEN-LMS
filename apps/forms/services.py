"""
Form services — the write path for the dynamic form system.

All mutations go through these services so that:

  - transaction boundaries are explicit (one atomic block per operation),
  - the submission-number generator retries safely under concurrency,
  - schema snapshots are captured at submit time (historical submissions are
    never reinterpreted against mutated schema definitions),
  - workflow instances are created/linked through ``WorkflowEngineService``
    using its real method signatures — workflow state is never written
    directly,
  - every meaningful action on a workflow-enabled submission lands in the
    append-only ``ActionLog`` of the linked instance (forms reuse the audit
    model; they do not duplicate it).

PostgreSQL is the production concurrency backend: ``select_for_update()``
locks the sequence row. SQLite (tests) has no row locking, so the generator
relies on the DB unique constraint on ``FormSubmission.submission_number``
plus a bounded retry inside a nested atomic (savepoint) that only swallows a
confirmed submission-number collision.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import timedelta
from typing import Any, Callable, Optional

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.forms.models import (
    FormAttachment,
    FormComment,
    FormSchema,
    FormSubmission,
    Request,
    RequestType,
    SubmissionSequence,
)
from apps.forms.validation import FormDataValidator, FormDataInvalid

logger = logging.getLogger(__name__)

#: Bounded retry limit for submission-number generation (SQLite collisions).
NUMBER_RETRY_LIMIT = 5

#: Registry keys copied into the denormalized visibility columns.
CLASS_GROUP_KEYS = {"academic.class_group"}
PERSON_KEYS = {"persons.person"}


def request_type_for_schema(schema: FormSchema) -> RequestType:
    """Return the business request type for a schema, creating a legacy bridge.

    Older installations predate ``RequestType`` and only store a workflow on
    ``FormSchema``.  The bridge is deliberately deterministic and idempotent so
    those installations can adopt the unified request model without losing
    their existing schemas or requiring an unsafe data rewrite at runtime.
    """
    request_type = getattr(schema, "request_type", None)
    if request_type is not None:
        return request_type

    code = f"form-{schema.slug}"[:120]
    request_type, _created = RequestType.objects.get_or_create(
        code=code,
        defaults={
            "title": schema.title,
            "description": schema.description,
            "kind": RequestType.Kind.REQUEST,
            "workflow_definition_id": schema.workflow_definition_id,
            "metadata": {"legacy_schema_bridge": True},
        },
    )
    changed: list[str] = []
    if not request_type.workflow_definition_id and schema.workflow_definition_id:
        request_type.workflow_definition_id = schema.workflow_definition_id
        changed.append("workflow_definition")
    if changed:
        request_type.save(update_fields=[*changed, "updated_at"])
    if schema.request_type_id != request_type.pk:
        schema.request_type = request_type
        schema.save(update_fields=["request_type", "updated_at"])
    return request_type


def request_status_from_submission(submission: FormSubmission) -> str:
    """Map the compatibility form status to the unified request lifecycle."""
    mapping = {
        FormSubmission.Status.DRAFT: Request.Status.DRAFT,
        FormSubmission.Status.SUBMITTED: Request.Status.SUBMITTED,
        FormSubmission.Status.PROCESSING: Request.Status.IN_REVIEW,
        FormSubmission.Status.APPROVED: Request.Status.APPROVED,
        FormSubmission.Status.REJECTED: Request.Status.REJECTED,
        FormSubmission.Status.ARCHIVED: Request.Status.ARCHIVED,
    }
    instance = submission.workflow_instance
    if instance is not None:
        state_code = getattr(getattr(instance, "current_state", None), "code", "") or ""
        if state_code in {"changes-requested", "changes_requested"}:
            return Request.Status.CHANGES_REQUESTED
        if instance.status == "running":
            if any(token in state_code for token in ("approval", "review", "check", "pending", "financial")):
                return Request.Status.AWAITING_ACTION
            return Request.Status.IN_REVIEW
        if instance.status == "completed":
            if (submission.form_schema.metadata or {}).get("domain_action"):
                return Request.Status.COMPLETED
            return Request.Status.APPROVED
        if instance.status == "rejected":
            return Request.Status.REJECTED
        if instance.status == "cancelled":
            return Request.Status.CANCELLED
    return mapping.get(submission.status, Request.Status.SUBMITTED)


@transaction.atomic
def sync_request_from_submission(
    submission: FormSubmission,
    *,
    create: bool = True,
) -> Request | None:
    """Create/update the unified Request projection for a submission.

    ``FormSubmission`` remains the backward-compatible storage of form data;
    this function is the single synchronization point for the new business
    request aggregate.  It is safe to call after every form lifecycle action.
    """
    request_type = request_type_for_schema(submission.form_schema)
    request_status = request_status_from_submission(submission)
    completed_at = timezone.now() if request_status in {
        Request.Status.APPROVED,
        Request.Status.COMPLETED,
        Request.Status.REJECTED,
        Request.Status.CANCELLED,
        Request.Status.ARCHIVED,
    } else None
    defaults = {
        "request_type": request_type,
        "requester": submission.submitted_by,
        "subject_person": submission.subject_person,
        "request_number": submission.submission_number or None,
        "status": request_status,
        "submitted_at": submission.submitted_at,
        "completed_at": completed_at,
        "last_action_at": submission.last_action_at or submission.updated_at,
        "metadata": {
            "schema_slug": submission.form_schema.slug,
            "schema_version": submission.schema_version_snapshot,
        },
    }
    if not create and not hasattr(submission, "business_request"):
        return None

    business_request, _created = Request.objects.get_or_create(
        form_submission=submission,
        defaults=defaults,
    )
    updates: list[str] = []
    for field in ("request_type", "requester", "subject_person"):
        value = defaults[field]
        current_id = getattr(business_request, f"{field}_id")
        value_id = getattr(value, "pk", None)
        if current_id != value_id:
            setattr(business_request, field, value)
            updates.append(field)
    for field in ("status", "submitted_at", "completed_at", "last_action_at"):
        value = defaults[field]
        if field == "completed_at" and value is not None and getattr(business_request, field) is not None:
            continue
        if getattr(business_request, field) != value:
            setattr(business_request, field, value)
            updates.append(field)
    if not business_request.request_number and defaults["request_number"]:
        business_request.request_number = defaults["request_number"]
        updates.append("request_number")
    if updates:
        business_request.last_action_at = defaults["last_action_at"]
        if "last_action_at" not in updates:
            updates.append("last_action_at")
        business_request.save(update_fields=[*dict.fromkeys(updates), "updated_at"])
    return business_request


class FormServiceError(Exception):
    """Base error for the forms service layer."""


class ImmutableSubmissionError(FormServiceError):
    """The submission is not a draft and cannot be edited."""


class WorkflowIntegrationError(FormServiceError):
    pass


# ─────────────────────────────────────────────────────────────────────────────
# Submission numbers
# ─────────────────────────────────────────────────────────────────────────────

def _is_submission_number_collision(exc: IntegrityError) -> bool:
    """True only when the IntegrityError is about submission_number uniqueness."""
    message = str(exc).lower()
    return "submission_number" in message


def _generate_number(slug: str, year: int, counter: int) -> str:
    """FORM-{SLUG}-{YEAR}-{SEQ} — Gregorian year (see repository convention note)."""
    return f"FORM-{slug.upper()}-{year}-{counter:06d}"


@transaction.atomic
def next_submission_number(schema: FormSchema) -> str:
    """
    Reserve the next submission number for ``schema.slug``.

    PostgreSQL: locks the (slug, year) sequence row with select_for_update.
    SQLite:     row locking is a no-op; the final unique insert on
                ``FormSubmission`` is the source of truth and a confirmed
                collision triggers a bounded retry by the caller. A prior
                existence check is never trusted.
    """
    year = timezone.now().year  # Gregorian — see convention note in the spec.
    try:
        with transaction.atomic():
            sequence, _created = SubmissionSequence.objects.get_or_create(
                slug=schema.slug,
                year=year,
                defaults={"last_value": 0},
            )
    except IntegrityError:
        # Concurrent creation of the sequence row — take the winner.
        sequence = SubmissionSequence.objects.get(slug=schema.slug, year=year)

    sequence = SubmissionSequence.objects.select_for_update().get(pk=sequence.pk)
    sequence.last_value = (sequence.last_value or 0) + 1
    sequence.save(update_fields=["last_value", "updated_at"])
    return _generate_number(schema.slug, year, sequence.last_value)


def _create_with_unique_number(fill_factory: Callable[[], dict[str, Any]]) -> FormSubmission:
    """
    Insert a submission, retrying a bounded number of times ONLY on a
    confirmed submission-number collision; unrelated IntegrityErrors
    propagate. Each retry runs in its own savepoint and re-allocates a
    fresh number via ``fill_factory``.
    """
    last_error: Optional[IntegrityError] = None
    for attempt in range(NUMBER_RETRY_LIMIT):
        try:
            with transaction.atomic():
                return FormSubmission.objects.create(**fill_factory())
        except IntegrityError as exc:
            if not _is_submission_number_collision(exc):
                raise
            last_error = exc
            logger.warning("submission_number collision (attempt %d/%d)", attempt + 1, NUMBER_RETRY_LIMIT)
    raise FormServiceError(
        f"could not allocate a unique submission number after {NUMBER_RETRY_LIMIT} attempts"
    ) from last_error


# ─────────────────────────────────────────────────────────────────────────────
# Visibility columns
# ─────────────────────────────────────────────────────────────────────────────

def _first_relation_id(data: dict, registry_keys: set[str], fields: list[dict]) -> Optional[str]:
    """First single-relation id in ``data`` whose field maps to one of ``registry_keys``."""
    for definition in fields:
        if not isinstance(definition, dict):
            continue
        relation = definition.get("relation") or {}
        if relation.get("registry_key") not in registry_keys:
            continue
        if definition.get("type") == "relation":
            value = data.get(definition.get("key"))
            if isinstance(value, str) and value:
                return value
    return None


def derive_visibility(schema: FormSchema, data: dict) -> dict[str, Any]:
    """
    Extract class_group_id / subject_person_id for bounded queryset scoping.

    subject_person is set ONLY from a field explicitly declared in schema
    metadata (``{"subject_field": "<key>"}``). Multi-student forms
    (attendance/grade tables) deliberately leave it NULL — granting a student
    or parent visibility via one arbitrary row of a multi-row payload would
    leak the other rows; those forms are scoped through class_group for the
    teacher and submitter/elevated roles only.
    """
    fields = schema.fields or []
    data = data if isinstance(data, dict) else {}
    subject = None
    subject_key = (schema.metadata or {}).get("subject_field")
    if subject_key:
        value = data.get(subject_key)
        if isinstance(value, str) and value:
            subject = value
    return {
        "class_group_id": _first_relation_id(data, CLASS_GROUP_KEYS, fields),
        "subject_person_id": subject,
    }


def compute_checksum(fileobj) -> str:
    """SHA-256 of the actual stored bytes — never a client-provided value."""
    digest = hashlib.sha256()
    pos = fileobj.tell()
    fileobj.seek(0)
    for chunk in iter(lambda: fileobj.read(65536), b""):
        digest.update(chunk)
    fileobj.seek(pos)
    return f"sha256:{digest.hexdigest()}"


# ─────────────────────────────────────────────────────────────────────────────
# Main service
# ─────────────────────────────────────────────────────────────────────────────

class FormSubmissionService:
    """Create / update / submit form submissions with workflow + audit."""

    @staticmethod
    def sanitize_payload(schema: FormSchema, data: Any) -> Any:
        """
        Sanitize free-text input before persistence (spec: text is sanitized,
        rich text through the bleach allowlist). Structural validation already
        ran; sanitization may only shrink strings.
        """
        from apps.forms.sanitizers import (
            RichTextSanitizerUnavailable,
            sanitize_rich_text,
            sanitize_text,
        )

        if not isinstance(data, dict):
            return data
        field_map = {f.get("key"): f for f in (schema.fields or []) if isinstance(f, dict)}
        cleaned = dict(data)
        for key, value in cleaned.items():
            definition = field_map.get(key)
            if definition is None:
                continue
            ftype = definition.get("type")
            try:
                if ftype in {"text", "textarea"} and isinstance(value, str):
                    cleaned[key] = sanitize_text(value)
                elif ftype == "rich_text" and isinstance(value, str):
                    cleaned[key] = sanitize_rich_text(value)
            except RichTextSanitizerUnavailable as exc:
                # Fail closed: without bleach, rich text must not be stored.
                raise FormServiceError(str(exc)) from exc
        return cleaned

    # ── validation helper ────────────────────────────────────────────────

    def validate_data(
        self,
        schema: FormSchema,
        fields: list[dict],
        data: Any,
        user,
        request=None,
        attachment_keys: Optional[set[str]] = None,
        *,
        require_all: bool = False,
    ) -> None:
        validator = FormDataValidator(
            fields,
            data,
            user=user,
            request=request,
            schema_slug=schema.slug,
            existing_attachment_keys=attachment_keys or set(),
        )
        result = validator.run(require_all=require_all)
        if not result.ok:
            raise FormDataInvalid(result.as_dict())

    # ── create draft ─────────────────────────────────────────────────────

    @transaction.atomic
    def create_submission(
        self,
        *,
        schema: FormSchema,
        user,
        data: Any,
        request=None,
        notes: str = "",
        attachment_keys: Optional[set[str]] = None,
    ) -> FormSubmission:
        """Create a DRAFT submission owned by ``user`` (submitter is never client-controlled)."""
        self.validate_data(schema, schema.fields, data, user, request, attachment_keys)
        data = self.sanitize_payload(schema, data)
        visibility = derive_visibility(schema, data or {})

        def fill() -> dict[str, Any]:
            return {
                "form_schema": schema,
                "submitted_by": user,
                "data": data if isinstance(data, dict) else {},
                "status": FormSubmission.Status.DRAFT,
                "notes": notes or "",
                "submission_number": next_submission_number(schema),
                "schema_version_snapshot": schema.version,
                "client_ip": _client_ip(request),
                "last_action_at": timezone.now(),
                **visibility,
            }

        submission = _create_with_unique_number(fill)
        # New unified request layer.  This is a projection over the existing
        # submission record and therefore keeps legacy form APIs compatible.
        sync_request_from_submission(submission)
        self._log(submission, action="form_create", actor=user)
        return submission

    # ── update draft ─────────────────────────────────────────────────────

    @transaction.atomic
    def update_submission(
        self,
        *,
        submission: FormSubmission,
        user,
        data: Any = None,
        notes: Optional[str] = None,
        request=None,
        attachment_keys: Optional[set[str]] = None,
        allow_changes_requested: bool = False,
    ) -> FormSubmission:
        def changes_requested_state(value) -> bool:
            instance = getattr(value, "workflow_instance", None)
            return bool(
                allow_changes_requested
                and value.status == FormSubmission.Status.PROCESSING
                and getattr(getattr(instance, "current_state", None), "code", "")
                in {"changes-requested", "changes_requested"}
            )

        if submission.is_immutable and not changes_requested_state(submission):
            raise ImmutableSubmissionError(
                "Submitted forms are immutable and cannot be edited."
            )
        # Re-read + lock the row: the caller may hold a stale in-memory copy
        # (e.g. submitted by another request after it was loaded). Never trust
        # the passed object's status for the immutability decision.
        submission = FormSubmission.objects.select_for_update().get(pk=submission.pk)
        if submission.is_immutable and not changes_requested_state(submission):
            raise ImmutableSubmissionError(
                "Submitted forms are immutable and cannot be edited."
            )
        if submission.submitted_by_id != user.pk:
            # Drafts are private to their submitter (also enforced at API level).
            raise FormServiceError("Only the submitter can edit this draft.")

        fields = submission.effective_fields()
        update_fields = ["updated_at", "last_action_at"]
        if data is not None:
            self.validate_data(
                submission.form_schema, fields, data, user, request, attachment_keys
            )
            data = self.sanitize_payload(submission.form_schema, data)
            submission.data = data
            visibility = derive_visibility(submission.form_schema, data)
            submission.class_group_id = visibility["class_group_id"]
            submission.subject_person_id = visibility["subject_person_id"]
            update_fields += ["data", "class_group_id", "subject_person_id"]
        if notes is not None:
            submission.notes = notes
            update_fields.append("notes")

        submission.last_action_at = timezone.now()
        submission.save(update_fields=list(dict.fromkeys(update_fields)))
        self._log(submission, action="form_update", actor=user)
        return submission

    # ── submit ───────────────────────────────────────────────────────────

    @transaction.atomic
    def submit_submission(
        self,
        *,
        submission: FormSubmission,
        user,
        request=None,
        attachment_keys: Optional[set[str]] = None,
    ) -> FormSubmission:
        """
        Transition a draft to SUBMITTED: lock the row, re-validate, snapshot
        the schema, ensure a number, and start the workflow when configured.
        """
        # Lock the submission row so a concurrent double-submit cannot pass
        # the draft check twice (PostgreSQL row lock; SQLite serializes).
        # NOTE: no select_related here — FOR UPDATE over a LEFT OUTER JOIN
        # (nullable workflow_definition) is rejected by PostgreSQL; related
        # objects load lazily in separate plain SELECTs.
        submission = FormSubmission.objects.select_for_update().get(pk=submission.pk)
        if submission.is_immutable:
            raise ImmutableSubmissionError("This submission has already been submitted.")
        if submission.status != FormSubmission.Status.DRAFT:
            raise FormServiceError(f"Unexpected status {submission.status!r}.")
        if submission.submitted_by_id != user.pk:
            raise FormServiceError("Only the submitter can submit this draft.")

        schema = submission.form_schema
        # Re-validate against the LIVE schema at submit time with ALL required
        # fields enforced, then snapshot it so later schema edits never
        # reinterpret this submission.
        self.validate_data(
            schema, schema.fields, submission.data, user, request, attachment_keys,
            require_all=True,
        )

        if not submission.submission_number:
            # Legacy/edge path: allocate with the same bounded retry.
            for attempt in range(NUMBER_RETRY_LIMIT):
                try:
                    with transaction.atomic():
                        submission.submission_number = next_submission_number(schema)
                        submission.save(update_fields=["submission_number", "updated_at"])
                    break
                except IntegrityError as exc:
                    if not _is_submission_number_collision(exc):
                        raise
                    submission.refresh_from_db(fields=["submission_number"])
            else:
                raise FormServiceError("could not allocate a unique submission number")

        submission.version_snapshot = {"fields": schema.fields, "version": schema.version}
        submission.schema_version_snapshot = schema.version
        submission.status = FormSubmission.Status.SUBMITTED
        submission.submitted_at = timezone.now()
        submission.last_action_at = submission.submitted_at
        if schema.slug == "attendance":
            submission.projection_status = FormSubmission.ProjectionStatus.PENDING
            submission.projection_next_attempt_at = submission.submitted_at

        workflow_definition = schema.workflow_definition
        if schema.request_type_id:
            request_type = request_type_for_schema(schema)
            workflow_definition = request_type.workflow_definition or workflow_definition

        if workflow_definition is not None:
            instance = self._start_workflow(submission, user)
            submission.workflow_instance = instance
            synced = self._status_from_workflow(instance)
            if synced:
                submission.status = synced

        submission.save(
            update_fields=[
                "submission_number", "version_snapshot", "schema_version_snapshot",
                "status", "submitted_at", "last_action_at", "workflow_instance",
                "projection_status", "projection_next_attempt_at",
                "updated_at",
            ]
        )
        self._log(submission, action="form_submit", actor=user)
        # Project supported payloads into the typed education tables so the
        # DB (not the form layer) enforces attendance uniqueness (B4).
        # Fail-soft: a projection problem is logged for reconciliation and
        # never loses the submission itself.
        self._project_into_education(submission, user)
        sync_request_from_submission(submission)
        return submission

    def _project_into_education(self, submission: FormSubmission, user) -> None:
        """
        Attendance-form projection (B4). Only runs for the ``attendance``
        schema and only when the payload carries every required key; any
        mismatch is logged, never raised — the typed tables are the reporting
        layer of record, and reconciliation is a logged exception, not a lost
        submission.
        """
        from apps.core.utils import english_numbers

        if submission.form_schema.slug != "attendance":
            return
        submission.projection_attempts += 1
        data = submission.data or {}
        required = ("class_group", "session_date", "session_number",
                    "session_start", "session_end", "attendance_list")
        if any(data.get(k) in (None, "", []) for k in required):
            self._mark_projection_failed(
                submission,
                "attendance submission is missing required projection fields",
            )
            logger.warning(
                "attendance projection skipped (missing keys) submission=%s",
                submission.pk,
            )
            return
        try:
            from apps.education.services import project_attendance_submission

            rows = [
                {"student": row.get("student_id"), "status": row.get("status"),
                 "note": row.get("note", "")}
                for row in data["attendance_list"]
                if isinstance(row, dict) and row.get("student_id")
            ]
            project_attendance_submission(
                class_group_id=data["class_group"],
                session_date=data["session_date"],
                session_number=int(english_numbers(str(data["session_number"]))),
                session_start=data["session_start"],
                session_end=data["session_end"],
                rows=rows,
                actor=user,
            )
            submission.projection_status = FormSubmission.ProjectionStatus.COMPLETE
            submission.projection_last_error = ""
            submission.projection_next_attempt_at = None
            submission.save(update_fields=[
                "projection_status", "projection_attempts", "projection_last_error",
                "projection_next_attempt_at", "updated_at",
            ])
        except Exception as exc:  # noqa: BLE001 - reporting projection must never break submit
            self._mark_projection_failed(submission, str(exc or "projection failed"))
            logger.exception(
                "attendance projection failed submission=%s", submission.pk
            )

    @staticmethod
    def _mark_projection_failed(submission: FormSubmission, error: str) -> None:
        attempts = max(submission.projection_attempts, 1)
        retry_seconds = min(60 * (2 ** min(attempts - 1, 8)), 21600)
        submission.projection_status = FormSubmission.ProjectionStatus.FAILED
        submission.projection_last_error = error[:2000]
        submission.projection_next_attempt_at = timezone.now() + timedelta(seconds=retry_seconds)
        submission.save(update_fields=[
            "projection_status", "projection_attempts", "projection_last_error",
            "projection_next_attempt_at", "updated_at",
        ])

    # ── workflow integration (uses the real engine service) ──────────────

    def _start_workflow(self, submission: FormSubmission, user):
        from apps.workflow.services import WorkflowEngineError, WorkflowEngineService

        schema = submission.form_schema
        request_type = request_type_for_schema(schema)
        workflow_definition = request_type.workflow_definition or schema.workflow_definition
        if workflow_definition is None:
            raise WorkflowIntegrationError(
                f"برای نوع درخواست «{request_type.code}» گردش‌کار فعال تعریف نشده است."
            )
        engine = WorkflowEngineService()
        # subject_person از داده‌ی فرم استخراج و در submit_submission
        # به submission.subject_person_id ست شده — همین FK را به Instance
        # پاس می‌دهیم تا workflowاعلان‌ها را به شخص هدف بفرستد
        # (یکپارچه‌سازی فرم‌ها و گردش‌کار).
        subject_person_kwargs = {}
        if submission.subject_person_id:
            subject_person_kwargs["subject_person"] = submission.subject_person
        try:
            instance = engine.create_instance(
                workflow_code=workflow_definition.code,
                requester=user,
                title=f"{schema.title} — {submission.submission_number}",
                description=submission.notes or "",
                **subject_person_kwargs,
            )
            engine.link_entity(instance_id=instance.id, entity=submission)
            return instance
        except WorkflowEngineError as exc:
            raise WorkflowIntegrationError(str(exc)) from exc

    @staticmethod
    def _status_from_workflow(instance) -> Optional[str]:
        """Map terminal workflow states onto submission status (sync only)."""
        return FormSubmissionService._status_from_status_value(instance.status)

    @staticmethod
    def _status_from_status_value(status_value) -> Optional[str]:
        """Map a raw workflow Instance.status value onto submission status."""
        mapping = {
            "completed": FormSubmission.Status.APPROVED,
            "rejected": FormSubmission.Status.REJECTED,
            "cancelled": FormSubmission.Status.ARCHIVED,
        }
        return mapping.get(status_value)

    @transaction.atomic
    def sync_status_from_workflow(
        self, submission: FormSubmission, *, actor=None
    ) -> FormSubmission:
        """
        Refresh submission.status from its workflow instance. Called after an
        authorized workflow transition executed through the engine — never by
        writing workflow state directly. Status sync is exempt from the
        data-immutability rule because the engine (not the update API) drives it.
        """
        if not submission.workflow_instance_id:
            return submission
        # The caller often holds a select_related()-prefetched instance that
        # predates the transition just executed — trusting it syncs the OLD
        # status (approve returned 200 but the sheet stayed "submitted").
        # Always read the instance's status fresh from the DB.
        fresh_status = (
            type(submission.workflow_instance)._default_manager.filter(
                pk=submission.workflow_instance_id,
            )
            .values_list("status", flat=True)
            .first()
        )
        target = self._status_from_status_value(fresh_status)
        if target and submission.status != target:
            submission.status = target
            submission.last_action_at = timezone.now()
            update_fields = ["status", "last_action_at", "updated_at"]
            if target in (FormSubmission.Status.APPROVED, FormSubmission.Status.REJECTED):
                submission.reviewed_at = submission.last_action_at
                if actor is not None:
                    submission.reviewed_by = actor
                    update_fields.append("reviewed_by")
                update_fields.append("reviewed_at")
            submission.save(update_fields=update_fields)
        sync_request_from_submission(submission)
        return submission

    # ── comments ─────────────────────────────────────────────────────────

    @transaction.atomic
    def add_comment(
        self,
        *,
        submission: FormSubmission,
        author,
        body: str,
        is_internal: bool = False,
        parent: Optional[FormComment] = None,
    ) -> FormComment:
        if parent is not None and parent.submission_id != submission.pk:
            raise FormServiceError("Parent comment belongs to a different submission.")
        comment = FormComment.objects.create(
            submission=submission,
            author=author,
            body=body,
            is_internal=bool(is_internal),
            parent=parent,
        )
        self._log(submission, action="form_comment", actor=author)
        return comment

    # ── attachments ──────────────────────────────────────────────────────

    @transaction.atomic
    def add_attachment(
        self,
        *,
        submission: FormSubmission,
        field_key: str,
        uploaded_file,
        uploader,
        mime_type: str,
        checksum: str,
    ) -> FormAttachment:
        attachment = FormAttachment.objects.create(
            submission=submission,
            field_key=field_key,
            file=uploaded_file,
            original_filename=_safe_original_name(uploaded_file.name),
            mime_type=mime_type,
            file_size=uploaded_file.size,
            checksum=checksum,
            uploaded_by=uploader,
        )
        self._log(submission, action="form_attachment", actor=uploader)
        return attachment

    # ── audit ────────────────────────────────────────────────────────────

    def _log(self, submission: FormSubmission, *, action: str, actor, extra: str = "") -> None:
        """
        Append to the linked workflow instance's ActionLog when one exists.
        Forms reuse the workflow audit trail; drafts without a workflow have no
        instance to attach to yet — their trail begins at submit time
        (documented limitation: ActionLog.instance is a required FK).
        """
        instance = submission.workflow_instance
        if instance is None:
            return
        try:
            from apps.workflow.models import ActionLog

            ActionLog.objects.create(
                instance=instance,
                from_state=instance.current_state,
                to_state=None,
                action=action,
                actor=actor,
                comment=extra,
                metadata={"submission": str(submission.pk)},
            )
        except Exception:  # noqa: BLE001 - audit must never break the write path
            logger.exception("failed to append ActionLog for submission %s", submission.pk)


def _client_ip(request) -> Optional[str]:
    if request is None:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip() or None
    return request.META.get("REMOTE_ADDR") or None


#: Schema slugs whose READ access is itself sensitive (grades, lead data).
SENSITIVE_SCHEMA_SLUGS = {"grade-report", "grade_report", "lead-assessment", "lead_assessment"}


def log_sensitive_access(request, submission: FormSubmission, *, allowed: bool) -> None:
    """
    Structured audit line for reads of sensitive submissions.

    Logged via the standard logger (not ActionLog — these models have no
    workflow instance to attach to for a pure read, and inventing one would
    pollute the workflow trail). Includes actor, action, timestamp, IP,
    submission id, schema slug and the authorization result.
    """
    actor = getattr(getattr(request, "user", None), "username", "anonymous")
    logger.info(
        "forms.sensitive_access actor=%s action=read ip=%s submission=%s schema=%s allowed=%s",
        actor,
        _client_ip(request),
        submission.pk,
        submission.form_schema.slug,
        allowed,
        extra={
            "forms_audit": {
                "actor": actor,
                "action": "read",
                "ip": _client_ip(request),
                "submission_id": str(submission.pk),
                "schema_slug": submission.form_schema.slug,
                "allowed": allowed,
                "timestamp": timezone.now().isoformat(),
            }
        },
    )


def _safe_original_name(name: str) -> str:
    """Keep only the basename, stripped of path components and control chars."""
    base = (name or "file").replace("\\", "/").split("/")[-1]
    cleaned = "".join(ch for ch in base if ch.isprintable() and ch not in "\x00\r\n")
    return cleaned[:255] or "file"


class RequestService:
    """Canonical application service for the unified request pipeline.

    The service intentionally delegates form validation to
    ``FormSubmissionService`` and state changes to ``WorkflowEngineService``.
    It is the boundary that future UI/API clients should use instead of
    coupling themselves to either implementation detail.
    """

    def __init__(self) -> None:
        self.forms = FormSubmissionService()

    @transaction.atomic
    def create_draft(
        self,
        *,
        schema: FormSchema,
        requester,
        data: Any,
        request=None,
        notes: str = "",
        attachment_keys: Optional[set[str]] = None,
        idempotency_key: Optional[str] = None,
    ) -> Request:
        if idempotency_key:
            existing = Request.objects.filter(
                requester=requester,
                metadata__client_idempotency_key=idempotency_key,
            ).first()
            if existing is not None:
                return existing
        submission = self.forms.create_submission(
            schema=schema,
            user=requester,
            data=data,
            request=request,
            notes=notes,
            attachment_keys=attachment_keys,
        )
        business_request = sync_request_from_submission(submission)
        if idempotency_key:
            metadata = dict(business_request.metadata or {})
            metadata["client_idempotency_key"] = idempotency_key
            business_request.metadata = metadata
            business_request.save(update_fields=["metadata", "updated_at"])
        return business_request

    @transaction.atomic
    def update_data(
        self,
        business_request: Request,
        *,
        actor,
        data: Any = None,
        notes: Optional[str] = None,
        request=None,
    ) -> Request:
        business_request = Request.objects.select_for_update().select_related(
            "form_submission", "form_submission__workflow_instance",
        ).get(pk=business_request.pk)
        if business_request.requester_id != actor.pk:
            raise FormServiceError("فقط درخواست‌کننده می‌تواند اطلاعات درخواست را اصلاح کند.")
        if business_request.status not in {
            Request.Status.DRAFT,
            Request.Status.CHANGES_REQUESTED,
        }:
            raise FormServiceError("این درخواست در وضعیت قابل اصلاح نیست.")
        self.forms.update_submission(
            submission=business_request.form_submission,
            user=actor,
            data=data,
            notes=notes,
            request=request,
            allow_changes_requested=True,
        )
        business_request.refresh_from_db()
        return sync_request_from_submission(business_request.form_submission)

    @transaction.atomic
    def submit(self, business_request: Request, *, actor, request=None, attachment_keys=None) -> Request:
        submission = business_request.form_submission
        self.forms.submit_submission(
            submission=submission,
            user=actor,
            request=request,
            attachment_keys=attachment_keys,
        )
        business_request.refresh_from_db()
        return sync_request_from_submission(business_request.form_submission)

    @transaction.atomic
    def transition(
        self,
        business_request: Request,
        *,
        actor,
        transition_id,
        comment: str = "",
        metadata: Optional[dict] = None,
        idempotency_key: Optional[str] = None,
    ) -> Request:
        business_request = Request.objects.select_for_update().select_related(
            "request_type", "form_submission", "form_submission__form_schema"
        ).get(pk=business_request.pk)
        submission = business_request.form_submission
        if submission is None or not submission.workflow_instance_id:
            raise FormServiceError("این درخواست گردش‌کار فعالی ندارد.")

        from apps.workflow.services import WorkflowEngineService

        instance = WorkflowEngineService().execute_transition(
            instance_id=submission.workflow_instance_id,
            transition_id=transition_id,
            actor=actor,
            comment=comment,
            metadata=metadata or {},
            idempotency_key=idempotency_key,
        )
        submission.refresh_from_db()
        self.forms.sync_status_from_workflow(submission, actor=actor)
        submission.refresh_from_db()
        if instance.status == instance.Status.COMPLETED:
            from apps.forms.domain_actions import DomainActionError, execute_domain_action

            try:
                execute_domain_action(
                    business_request=business_request,
                    actor=actor,
                    transition=None,
                )
            except DomainActionError as exc:
                # The surrounding transaction rolls back the approval, so the
                # request cannot appear approved while its domain side-effect
                # is missing.
                raise FormServiceError(str(exc)) from exc
            business_request.refresh_from_db()
        return sync_request_from_submission(submission)

    @transaction.atomic
    def cancel(self, business_request: Request, *, actor, reason: str = "") -> Request:
        submission = business_request.form_submission
        if submission is None or not submission.workflow_instance_id:
            raise FormServiceError("این درخواست گردش‌کار فعالی ندارد.")
        from apps.workflow.services import WorkflowEngineService

        WorkflowEngineService().cancel_instance(
            submission.workflow_instance_id,
            actor,
            reason=reason,
        )
        submission.refresh_from_db()
        self.forms.sync_status_from_workflow(submission, actor=actor)
        submission.refresh_from_db()
        return sync_request_from_submission(submission)
