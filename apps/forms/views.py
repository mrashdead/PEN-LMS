"""
DRF views for the dynamic form system.

Conventions follow the existing apps (apps.workflow / apps.academics):
generic DRF views, ``required_permissions`` group checks layered with role
checks, queryset-level visibility (404 instead of leaking existence), Persian
help texts in serializers, and services carrying the business logic.

Every write endpoint:
  - requires authentication (IsActiveUser) + model permission (HasGroupPermission),
  - applies the ``form_write`` throttle (30/min per user),
  - rejects client-controlled submitter / workflow / audit fields,
  - validates data through FormDataValidator (with user + request),
  - returns field-keyed validation errors,
  - 404s unauthorized objects instead of 403-ing (no existence leak).
"""
from __future__ import annotations

import hashlib
import logging

from django.core.cache import cache
from django.db import transaction
from django.http import FileResponse
from django.shortcuts import get_object_or_404

from rest_framework import generics, pagination, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.group_permissions import HasGroupPermission
from apps.core.permissions import IsActiveUser
from apps.forms.filters import FormSubmissionFilterSet
from apps.forms.models import (
    FormAttachment,
    FormComment,
    FormSchema,
    FormSubmission,
)
from apps.forms.permissions import (
    CanAccessForms,
    CanManageFormSchemas,
    can_view_internal_comments,
    visible_schemas_for,
    visible_submissions_for,
)
from apps.forms.serializers import (
    FormAttachmentSerializer,
    FormCommentCreateSerializer,
    FormCommentSerializer,
    FormSchemaSerializer,
    FormSubmissionCreateSerializer,
    FormSubmissionDetailSerializer,
    FormSubmissionListSerializer,
    FormSubmissionUpdateSerializer,
)
from apps.forms.services import (
    FormServiceError,
    FormSubmissionService,
    ImmutableSubmissionError,
    compute_checksum,
    log_sensitive_access,
)
from apps.forms.throttles import FormWriteThrottle
from apps.forms.validation import (
    FORBIDDEN_MIME_TYPES,
    FormDataInvalid,
    attachment_limits,
)
from apps.forms.mime import MimeTypeDetectorUnavailable, detect_mime

logger = logging.getLogger(__name__)

service = FormSubmissionService()


class FormsPagination(pagination.PageNumberPagination):
    """Project default (20) with a hard cap so page_size can never balloon."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


SENSITIVE_SLUGS = {"grade-report", "grade_report", "lead-assessment", "lead_assessment"}


def _idempotency_key(request) -> str | None:
    """Public header name; strips whitespace. None when absent."""
    return (request.headers.get("Idempotency-Key") or "").strip() or None


def _idem_marker(request, scope: str) -> str | None:
    key = _idempotency_key(request)
    if not key:
        return None
    return f"forms:idem:{scope}:{request.user.pk}:{hashlib.sha256(key.encode()).hexdigest()[:32]}"


def _reject_duplicate(request, scope: str) -> Response | None:
    """
    Best-effort idempotency guard for duplicate POSTs: a request carrying an
    Idempotency-Key already marked as completed returns 409 instead of
    creating a second resource. The marker is written only after success
    (``_mark_idempotent``), so failed attempts can be retried with the same
    key. Concurrent in-flight duplicates remain possible — the throttle and
    transactional writes bound the blast radius; a distributed lock would be
    the production-grade upgrade.
    """
    marker = _idem_marker(request, scope)
    if marker and cache.get(marker):
        return Response(
            {"error": "درخواست تکراری؛ این کلید Idempotency پیش‌تر استفاده شده است."},
            status=status.HTTP_409_CONFLICT,
        )
    return None


def _mark_idempotent(request, scope: str) -> None:
    marker = _idem_marker(request, scope)
    if marker:
        cache.set(marker, "1", timeout=600)


def _attachment_key_set(submission: FormSubmission) -> set[str]:
    return set(
        str(pk) for pk in submission.attachments.values_list("pk", flat=True)
    )


# ─────────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────────

class FormSchemaListView(generics.ListAPIView):
    """Active schemas visible to the requesting user's roles."""

    permission_classes = (IsActiveUser, CanAccessForms)
    serializer_class = FormSchemaSerializer

    def get_queryset(self):
        return visible_schemas_for(self.request.user).order_by("slug", "-version")


class FormSchemaDetailView(generics.RetrieveAPIView):
    permission_classes = (IsActiveUser, CanAccessForms)
    serializer_class = FormSchemaSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return visible_schemas_for(self.request.user)


class FormSchemaAdminView(generics.ListCreateAPIView):
    """
    Schema administration: list all versions / create new versions.
    Restricted to elevated roles for every method.
    """

    permission_classes = (IsActiveUser, HasGroupPermission, CanManageFormSchemas)
    required_permissions = {
        "GET": ["forms.view_formschema"],
        "POST": ["forms.add_formschema"],
    }
    serializer_class = FormSchemaSerializer
    queryset = FormSchema.objects.all()

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        from django.db import IntegrityError

        from apps.forms.schema_validation import SchemaDefinitionError, validate_form_fields

        payload = request.data or {}
        slug = str(payload.get("slug") or "").strip()
        version = payload.get("version", 1)
        fields = payload.get("fields")
        if not slug or not isinstance(fields, list):
            return Response(
                {"error": "slug و fields الزامی هستند."}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            ordered = validate_form_fields(fields)
        except SchemaDefinitionError as exc:
            return Response({"fields": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                schema = FormSchema.objects.create(
                    slug=slug,
                    title=str(payload.get("title") or slug),
                    description=str(payload.get("description") or ""),
                    version=version,
                    is_active=bool(payload.get("is_active", True)),
                    fields=ordered,
                    metadata=payload.get("metadata") or {},
                    created_by=request.user,
                )
        except IntegrityError:
            return Response(
                {"error": "نسخه تکراری یا نسخه فعال تکراری برای این slug وجود دارد."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            FormSchemaSerializer(schema, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Submissions
# ─────────────────────────────────────────────────────────────────────────────

class FormSubmissionListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsActiveUser, HasGroupPermission, CanAccessForms)
    required_permissions = {"GET": ["forms.view_formsubmission"], "POST": ["forms.add_formsubmission"]}
    throttle_classes = (FormWriteThrottle,)
    pagination_class = FormsPagination
    filterset_class = FormSubmissionFilterSet

    def get_serializer_class(self):
        return FormSubmissionCreateSerializer if self.request.method == "POST" else FormSubmissionListSerializer

    def get_throttles(self):
        if self.request.method == "POST":
            return [throttle() for throttle in self.throttle_classes]
        return []

    def get_queryset(self):
        # Visible-only base; DjangoFilterBackend (project default) applies the
        # filterset (status, schema, submitter, date ranges, number, workflow
        # status) on top of this — never on an unscoped queryset.
        qs = visible_submissions_for(self.request.user)
        ordering = self.request.query_params.get("ordering", "-created_at")
        if ordering.lstrip("-") not in {"created_at", "submitted_at", "status"}:
            ordering = "-created_at"
        return qs.select_related(
            "form_schema", "submitted_by", "workflow_instance"
        ).order_by(ordering)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        duplicate = _reject_duplicate(request, "submission-create")
        if duplicate is not None:
            return duplicate
        serializer = FormSubmissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data
        schema = get_object_or_404(
            visible_schemas_for(request.user), slug=vd["schema_slug"]
        )
        try:
            submission = service.create_submission(
                schema=schema,
                user=request.user,
                data=vd.get("data") or {},
                request=request,
                notes=vd.get("notes") or "",
            )
        except FormDataInvalid as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
        except FormServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _mark_idempotent(request, "submission-create")
        return Response(
            FormSubmissionDetailSerializer(submission, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class FormSubmissionDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve / update a submission. Updates are allowed only for the submitter
    while the submission is a draft; non-draft submissions are immutable
    (service + object permission enforce this).
    """

    permission_classes = (IsActiveUser, HasGroupPermission, CanAccessForms)
    required_permissions = {"GET": ["forms.view_formsubmission"], "PATCH": ["forms.change_formsubmission"]}
    throttle_classes = (FormWriteThrottle,)
    lookup_url_kwarg = "submission_id"

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return FormSubmissionUpdateSerializer
        return FormSubmissionDetailSerializer

    def get_throttles(self):
        if self.request.method == "PATCH":
            return [FormWriteThrottle()]
        return []

    def get_queryset(self):
        return visible_submissions_for(self.request.user).select_related(
            "form_schema", "submitted_by", "reviewed_by", "workflow_instance"
        )

    def retrieve(self, request, *args, **kwargs):
        submission = self.get_object()
        if submission.form_schema.slug in SENSITIVE_SLUGS:
            log_sensitive_access(request, submission, allowed=True)
        output = FormSubmissionDetailSerializer(submission, context={"request": request})
        data = dict(output.data)
        # Attachments and comments ride along so detail views are single-fetch.
        attachments = submission.attachments.all()
        comments = submission.comments.select_related("author").all()
        if not can_view_internal_comments(request.user):
            comments = comments.exclude(is_internal=True)
        data["attachments"] = FormAttachmentSerializer(attachments, many=True).data
        data["comments"] = FormCommentSerializer(comments, many=True).data
        return Response(data)

    def update(self, request, *args, **kwargs):
        submission = self.get_object()
        if submission.is_immutable:
            return Response(
                {"error": "فرم ارسال‌شده غیرقابل ویرایش است."},
                status=status.HTTP_409_CONFLICT,
            )
        if submission.submitted_by_id != request.user.pk:
            return Response({"detail": "یافت نشد."}, status=status.HTTP_403_FORBIDDEN)
        serializer = FormSubmissionUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data
        # §13-4 field-level diff of the sensitive payload before overwriting.
        changed_keys: list[str] = []
        if vd.get("data") is not None and isinstance(vd["data"], dict):
            before = submission.data if isinstance(submission.data, dict) else {}
            changed_keys = sorted(
                k for k, v in vd["data"].items() if before.get(k) != v
            )
        try:
            submission = service.update_submission(
                submission=submission,
                user=request.user,
                data=vd.get("data"),
                notes=vd.get("notes"),
                request=request,
                attachment_keys=_attachment_key_set(submission),
            )
        except FormDataInvalid as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
        except FormServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        if changed_keys:
            from apps.core.models import AuditEvent

            AuditEvent.record(
                kind=AuditEvent.Kind.FIELD_CHANGE,
                summary=f"تغییر فیلدهای {', '.join(changed_keys[:10])} در پیش‌نویس فرم {submission.pk}",
                actor=request.user,
                obj=submission,
                request=request,
                metadata={"changed_keys": changed_keys},
            )
        return Response(
            FormSubmissionDetailSerializer(submission, context={"request": request}).data
        )


class FormSubmissionSubmitView(APIView):
    """POST — submit a draft: validates, snapshots the schema, starts workflow."""

    permission_classes = (IsActiveUser, HasGroupPermission, CanAccessForms)
    required_permissions = {"POST": ["forms.change_formsubmission"]}
    throttle_classes = (FormWriteThrottle,)

    def post(self, request, submission_id):
        submission = get_object_or_404(
            visible_submissions_for(request.user).select_related(
                "form_schema", "form_schema__workflow_definition"
            ),
            pk=submission_id,
        )
        if submission.submitted_by_id != request.user.pk:
            # Hide existence from non-submitters even if visibility allowed a read.
            return Response({"detail": "یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        # Replay-safe submit (§13-3): a retried POST carrying the same
        # Idempotency-Key whose submit already completed returns the CURRENT
        # submission (200) instead of a bare 409. Without a key, behavior is
        # unchanged (409 immutability).
        marker = _idem_marker(request, "submission-submit")
        if marker and cache.get(marker):
            return Response(
                FormSubmissionDetailSerializer(submission, context={"request": request}).data
            )
        try:
            submission = service.submit_submission(
                submission=submission,
                user=request.user,
                request=request,
                attachment_keys=_attachment_key_set(submission),
            )
        except FormDataInvalid as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
        except ImmutableSubmissionError:
            return Response(
                {"error": "این فرم قبلاً ارسال شده است."}, status=status.HTTP_409_CONFLICT
            )
        except FormServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _mark_idempotent(request, "submission-submit")
        return Response(
            FormSubmissionDetailSerializer(submission, context={"request": request}).data
        )


class FormWorkflowTransitionView(APIView):
    """
    POST — execute a workflow transition on a submission's workflow instance
    THROUGH the engine. Direct status writes are impossible from this API;
    the submission status is re-synced from the resulting workflow state.
    """

    permission_classes = (IsActiveUser, HasGroupPermission, CanAccessForms)
    required_permissions = {"POST": ["forms.change_formsubmission"]}
    throttle_classes = (FormWriteThrottle,)

    def _get_submission(self, request, submission_id):
        return get_object_or_404(
            visible_submissions_for(request.user).select_related(
                "form_schema", "workflow_instance", "workflow_instance__current_state"
            ),
            pk=submission_id,
        )

    def _execute(self, request, submission, transition_id):
        """Run ``transition_id`` if the engine authorizes it for this actor."""
        from apps.workflow.services import (
            InvalidTransitionError,
            WorkflowEngineError,
            WorkflowEngineService,
        )

        instance = submission.workflow_instance
        if instance is None:
            return Response(
                {"error": "این فرم به گردش کاری متصل نیست."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        engine = WorkflowEngineService()
        try:
            # Available transitions for THIS actor — authorization lives in the
            # engine (roles + guards). An id outside this list is rejected.
            available = engine.get_available_transitions(instance, request.user)
            chosen = next((t for t in available if str(t.pk) == str(transition_id)), None)
            if chosen is None:
                return Response(
                    {"error": "این انتقال برای شما در وضعیت فعلی مجاز نیست."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            # Business rules the engine guards cannot see (they operate on
            # Instance fields, not submission JSON data). lead-assessment:
            # enrollment requires a recommended course decided at assessment.
            if (
                submission.form_schema.slug == "lead-assessment"
                and chosen.name.lower() == "enroll"
                and not (submission.data or {}).get("recommended_course")
            ):
                return Response(
                    {"recommended_course": "پیش از ثبت‌نام باید دوره پیشنهادی مشخص شود."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            engine.execute_transition(
                instance_id=instance.pk,
                transition_id=chosen.pk,
                actor=request.user,
                comment=str(request.data.get("comment") or ""),
                idempotency_key=(
                    str(request.data.get("idempotency_key") or "").strip() or None
                ),
            )
        except InvalidTransitionError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except WorkflowEngineError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        submission = service.sync_status_from_workflow(submission, actor=request.user)
        return Response(
            FormSubmissionDetailSerializer(submission, context={"request": request}).data
        )

    def post(self, request, submission_id):
        submission = self._get_submission(request, submission_id)
        return self._execute(request, submission, request.data.get("transition_id"))


class FormWorkflowActionView(FormWorkflowTransitionView):
    """
    POST /approve/ and /reject/ — named sugar over the transition endpoint.
    Resolves the matching AVAILABLE transition by its semantic ``kind`` first
    (canonical, seeded by seed_form_workflows) and falls back to name aliases
    for transitions created before ``kind`` existed. The engine's role/guard
    checks remain the sole authorization authority, and the execution path is
    the shared _execute() so the lead-assessment business rule and the
    forms-status sync still run (B6).
    """

    action_kind = None   # e.g. "approve"
    action_name = None   # e.g. "approve" (legacy matching)

    def post(self, request, submission_id):
        from apps.workflow.services import WorkflowEngineService

        submission = self._get_submission(request, submission_id)
        instance = submission.workflow_instance
        if instance is None:
            return Response(
                {"error": "این فرم به گردش کاری متصل نیست."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        candidates = WorkflowEngineService().get_available_transitions(
            instance, request.user
        )
        names = self._acceptable_names()
        match = next(
            (t for t in candidates
             if (t.kind or "").strip().lower() == (self.action_kind or "")
             or t.name.strip().lower() in names),
            None,
        )
        if match is None:
            return Response(
                {"error": "هیچ انتقالی با این نام برای شما مجاز نیست."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return self._execute(request, submission, match.pk)

    def _acceptable_names(self):
        if not self.action_name:
            return set()
        base = self.action_name
        return {base, f"{base}d", f"do_{base}", f"mark_{base}"}


class FormWorkflowApproveView(FormWorkflowActionView):
    action_kind = "approve"
    action_name = "approve"


class FormWorkflowRejectView(FormWorkflowActionView):
    action_kind = "reject"
    action_name = "reject"


# ─────────────────────────────────────────────────────────────────────────────
# Comments
# ─────────────────────────────────────────────────────────────────────────────

class FormCommentListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsActiveUser, HasGroupPermission, CanAccessForms)
    required_permissions = {"GET": ["forms.view_formcomment"], "POST": ["forms.add_formcomment"]}
    throttle_classes = (FormWriteThrottle,)

    def get_throttles(self):
        if self.request.method == "POST":
            return [FormWriteThrottle()]
        return []

    def _submission(self):
        return get_object_or_404(
            visible_submissions_for(self.request.user), pk=self.kwargs["submission_id"]
        )

    def get_queryset(self):
        qs = FormComment.objects.filter(
            submission=self._submission()
        ).select_related("author")
        if not can_view_internal_comments(self.request.user):
            qs = qs.exclude(is_internal=True)
        return qs

    def get_serializer_class(self):
        return FormCommentCreateSerializer if self.request.method == "POST" else FormCommentSerializer

    def create(self, request, *args, **kwargs):
        submission = self._submission()
        serializer = FormCommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data
        if vd.get("is_internal") and not can_view_internal_comments(request.user):
            return Response(
                {"is_internal": "شما مجوز ثبت یادداشت داخلی ندارید."},
                status=status.HTTP_403_FORBIDDEN,
            )
        parent = None
        if vd.get("parent"):
            try:
                parent = FormComment.objects.get(pk=vd["parent"], submission=submission)
            except FormComment.DoesNotExist:
                return Response(
                    {"parent": "کامنت والد یافت نشد."}, status=status.HTTP_400_BAD_REQUEST
                )
        try:
            comment = service.add_comment(
                submission=submission,
                author=request.user,
                body=vd["body"],
                is_internal=vd.get("is_internal", False),
                parent=parent,
            )
        except FormServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            FormCommentSerializer(comment, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Attachments (upload + private download)
# ─────────────────────────────────────────────────────────────────────────────

class FormAttachmentUploadView(APIView):
    """
    POST (multipart) — upload a file against a submission's ``file`` field.

    Validation: extension allowlist, content-based MIME (python-magic) with
    allowlist, extension/MIME consistency, size limit, forbidden types, and
    a real checksum computed from stored bytes.
    """

    permission_classes = (IsActiveUser, HasGroupPermission, CanAccessForms)
    required_permissions = {"POST": ["forms.add_formattachment"]}
    throttle_classes = (FormWriteThrottle,)

    def post(self, request, submission_id):
        submission = get_object_or_404(
            visible_submissions_for(request.user).select_related("form_schema"),
            pk=submission_id,
        )
        if submission.submitted_by_id != request.user.pk:
            return Response({"detail": "یافت نشد."}, status=status.HTTP_404_NOT_FOUND)

        field_key = str(request.data.get("field_key") or "")
        field_definition = next(
            (f for f in submission.form_schema.fields
             if isinstance(f, dict) and f.get("key") == field_key),
            None,
        )
        # The field must exist AND be a file field (spec rule).
        if field_definition is None or field_definition.get("type") != "file":
            return Response({"field_key": "فیلد فایل نامعتبر است."}, status=status.HTTP_400_BAD_REQUEST)

        upload = request.FILES.get("file")
        if upload is None:
            return Response({"file": "فایلی ارسال نشده است."}, status=status.HTTP_400_BAD_REQUEST)

        allowed_ext, allowed_mime, max_bytes = attachment_limits()

        # Per-field limits from the schema (spec: validators.max_file_size,
        # accept, mime_types) tighten — never loosen — the global caps.
        nested = field_definition.get("validators") or {}
        field_max = field_definition.get("max_file_size") or nested.get("max_file_size")
        effective_max = min([max_bytes] + ([int(field_max)] if field_max else []))
        field_accept = field_definition.get("accept") or [
            f".{e.lstrip('.')}" for e in (nested.get("allowed_extensions") or [])
        ]
        field_mime = field_definition.get("mime_types") or nested.get("allowed_mime_types")

        ext = ""
        original = upload.name or ""
        if "." in original:
            ext = original.rsplit(".", 1)[-1].lower()
            ext = f".{ext}" if ext and ext.isalnum() else ""

        if ext and ext not in allowed_ext:
            return Response({"file": "پسوند فایل مجاز نیست."}, status=status.HTTP_400_BAD_REQUEST)
        if field_accept and ext and ext not in field_accept:
            return Response({"file": "پسوند فایل برای این فیلد مجاز نیست."}, status=status.HTTP_400_BAD_REQUEST)

        if upload.size > effective_max:
            return Response({"file": "حجم فایل بیش از حد مجاز است."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            detected = detect_mime(upload)
        except MimeTypeDetectorUnavailable as exc:
            return Response({"error": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        if detected in FORBIDDEN_MIME_TYPES:
            return Response({"file": "نوع فایل مجاز نیست."}, status=status.HTTP_400_BAD_REQUEST)
        if detected not in allowed_mime:
            return Response({"file": "نوع فایل مجاز نیست."}, status=status.HTTP_400_BAD_REQUEST)
        if field_mime and detected not in set(field_mime):
            return Response({"file": "نوع فایل برای این فیلد مجاز نیست."}, status=status.HTTP_400_BAD_REQUEST)

        # Extension/MIME consistency (content must agree with the name).
        if ext:
            from apps.forms.validation import EXTENSION_MIME_CONTRACT

            contract = EXTENSION_MIME_CONTRACT.get(ext)
            if contract and detected not in contract:
                return Response(
                    {"file": "محتوای فایل با پسوند آن مطابقت ندارد."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        checksum = compute_checksum(upload)
        try:
            attachment = service.add_attachment(
                submission=submission,
                field_key=field_key,
                uploaded_file=upload,
                uploader=request.user,
                mime_type=detected,
                checksum=checksum,
            )
        except FormServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            FormAttachmentSerializer(attachment, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class FormAttachmentDownloadView(APIView):
    """
    GET — stream a private attachment to authorized viewers.

    The response never exposes the storage path; Content-Disposition uses the
    sanitized original filename. Visibility is inherited from the submission.
    """

    permission_classes = (IsActiveUser, HasGroupPermission, CanAccessForms)
    required_permissions = {"GET": ["forms.view_formattachment"]}

    def get(self, request, attachment_id):
        attachment = get_object_or_404(
            FormAttachment.objects.select_related("submission"),
            pk=attachment_id,
        )
        if not visible_submissions_for(request.user).filter(
            pk=attachment.submission_id
        ).exists():
            return Response({"detail": "یافت نشد."}, status=status.HTTP_404_NOT_FOUND)

        if not attachment.file or not attachment.file.storage.exists(attachment.file.name):
            return Response({"detail": "فایل یافت نشد."}, status=status.HTTP_404_NOT_FOUND)

        # §13-4: every private-file download is a queryable audit event.
        from apps.core.models import AuditEvent

        AuditEvent.record(
            kind=AuditEvent.Kind.DOWNLOAD,
            summary=f"دانلود پیوست «{attachment.original_filename}» از فرم {attachment.submission_id}",
            actor=request.user,
            obj=attachment,
            request=request,
            metadata={"submission": str(attachment.submission_id), "size": attachment.file_size},
        )

        safe_name = (attachment.original_filename or "file").replace('"', "").replace("\n", "")
        response = FileResponse(attachment.file.open("rb"), content_type=attachment.mime_type)
        response["Content-Disposition"] = f'attachment; filename="{safe_name}"'
        response["Content-Length"] = str(attachment.file_size)
        return response
