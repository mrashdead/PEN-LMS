"""
Server-rendered pages for the forms UI (dashboard-style, session auth).

These views are thin: they resolve visibility through the SAME queryset
helpers the API uses (``visible_schemas_for`` / ``visible_submissions_for``)
and render templates. All business authorization and validation remain on
the API/service side — the templates never decide access.

Schema administration UI (the ``/forms/admin/schemas/`` list and the visual
builder) is not shipped in this build: schema authoring goes through the
Django admin and the ``/api/forms/admin/schemas/`` endpoint.
"""
from __future__ import annotations


from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView, TemplateView

from apps.forms import relations
from apps.forms.models import FormSubmission
from apps.forms.permissions import (
    can_view_internal_comments,
    visible_request_types_for,
    visible_schemas_for,
    visible_submissions_for,
)

#: Cap relation option lists rendered into <select>/<fieldset> widgets.
RELATION_OPTION_LIMIT = 200


class FormsPageMixin(LoginRequiredMixin):
    """Pages require a logged-in session user (dashboard convention)."""


class SchemaPickerPage(FormsPageMixin, TemplateView):
    template_name = "forms/schema_picker.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["schemas"] = (
            visible_schemas_for(self.request.user)
            .select_related("request_type", "workflow_definition")
            .order_by("request_type__title", "title", "slug", "-version")
        )
        context["request_types"] = visible_request_types_for(self.request.user).order_by(
            "title", "code"
        )
        from apps.workflow.models import WorkflowDefinition

        context["workflow_definitions"] = WorkflowDefinition.objects.filter(
            is_active=True, is_deleted=False
        ).order_by("name", "code")
        return context


class SubmissionListPage(FormsPageMixin, ListView):
    template_name = "forms/submission_list.html"
    context_object_name = "submission_list"
    paginate_by = 20

    def get_queryset(self):
        qs = visible_submissions_for(self.request.user).select_related(
            "form_schema", "form_schema__request_type", "form_schema__workflow_definition",
            "submitted_by", "business_request"
        )
        status_param = self.request.GET.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        number = self.request.GET.get("submission_number")
        if number:
            qs = qs.filter(submission_number__iexact=number.strip())
        ordering = self.request.GET.get("ordering", "-created_at")
        if ordering.lstrip("-") not in {"created_at", "submitted_at", "status", "submission_number"}:
            ordering = "-created_at"
        return qs.order_by(ordering)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statuses"] = FormSubmission.Status.choices
        params = {k: v for k, v in self.request.GET.items() if k not in {"page"}}
        querystring = "".join(f"&{k}={v}" for k, v in params.items() if v)
        context["querystring"] = querystring
        return context


def _relation_options(schema: FormSchema, user) -> dict[str, list[dict]]:
    """Server-side option lists for relation fields (never client-supplied)."""
    options: dict[str, list[dict]] = {}
    for definition in schema.fields or []:
        if not isinstance(definition, dict):
            continue
        relation = definition.get("relation") or {}
        registry_key = relation.get("registry_key")
        if not registry_key or definition.get("type") not in {"relation", "multi_relation"}:
            continue
        try:
            spec = relations.resolve(registry_key)
            if not spec.is_available():
                continue
            qs = spec.queryset_for_user(user)
            schema_filter = relation.get("filter")
            if isinstance(schema_filter, dict) and schema_filter:
                qs = qs.filter(**schema_filter)
            items = []
            for obj in qs[:RELATION_OPTION_LIMIT]:
                label = getattr(obj, spec.display_field, None) or str(obj)
                items.append({"value": str(obj.pk), "label": str(label)})
            options[definition["key"]] = items
        except relations.RelationError:
            options[definition["key"]] = []
        except Exception:  # noqa: BLE001 - a page must never 500 on option lookup
            options[definition["key"]] = []
    return options


def _rendered_fields(submission: FormSubmission):
    """Build display rows from the submission's effective (snapshotted) fields."""
    data = submission.data or {}
    rendered = []
    for definition in submission.effective_fields():
        if not isinstance(definition, dict):
            continue
        key = definition.get("key")
        value = data.get(key)
        ftype = definition.get("type")
        entry = {
            "label": definition.get("label") or key,
            "is_rich": ftype == "rich_text",
            "is_file": ftype == "file",
            "is_table": ftype in {"table", "attendance_table", "grade_table"},
        }
        if entry["is_table"]:
            entry["display"] = value if isinstance(value, list) else []
        elif entry["is_file"]:
            count = len(value) if isinstance(value, list) else (1 if value else 0)
            entry["display"] = f"{count} پیوست" if count else "—"
        elif isinstance(value, list):
            entry["display"] = "، ".join(str(v) for v in value) or "—"
        else:
            entry["display"] = "" if value is None else str(value)
        rendered.append(entry)
    return rendered


class SubmissionCreatePage(FormsPageMixin, TemplateView):
    template_name = "forms/submission_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        schema = get_object_or_404(visible_schemas_for(self.request.user), slug=self.kwargs["slug"])
        if not schema.is_active:
            raise Http404("این فرم فعال نیست.")
        context["schema"] = schema
        context["fields"] = schema.fields
        context["form_data"] = {}
        context["errors"] = {}
        context["relation_options"] = _relation_options(schema, self.request.user)
        context["request_type"] = schema.request_type
        context["request_id"] = ""
        context["workflow_config"] = schema.workflow_config or {}
        context["form_execution_mode"] = _execution_mode(schema)
        context["can_submit_on_behalf"] = _can_submit_on_behalf(schema, self.request.user)
        return context


class SubmissionEditPage(FormsPageMixin, TemplateView):
    """Edit a draft (GET only — saving goes through the API like the create page)."""

    template_name = "forms/submission_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        submission = get_object_or_404(
            visible_submissions_for(self.request.user), pk=self.kwargs["submission_id"]
        )
        if submission.is_immutable or submission.submitted_by_id != self.request.user.pk:
            raise Http404
        schema = submission.form_schema
        context["schema"] = schema
        context["fields"] = submission.effective_fields()
        context["form_data"] = submission.data or {}
        context["errors"] = {}
        context["relation_options"] = _relation_options(schema, self.request.user)
        context["submission"] = submission
        context["request_type"] = schema.request_type
        business_request = getattr(submission, "business_request", None)
        context["request_id"] = str(business_request.pk) if business_request else ""
        context["workflow_config"] = schema.workflow_config or {}
        context["form_execution_mode"] = _execution_mode(schema)
        context["can_submit_on_behalf"] = _can_submit_on_behalf(schema, self.request.user)
        return context


def _can_submit_on_behalf(schema: FormSchema, user) -> bool:
    config = schema.workflow_config or {}
    if not config.get("allow_on_behalf"):
        return False
    roles = set(user.role_codes()) if hasattr(user, "role_codes") else set()
    eligible = set(config.get("eligible_initiator_roles") or [])
    return bool(getattr(user, "is_superuser", False) or (eligible and roles & eligible))


def _execution_mode(schema: FormSchema) -> str:
    configured = (schema.workflow_config or {}).get("execution_mode")
    if configured in {"direct", "workflow"}:
        return configured
    workflow = schema.workflow_definition
    if schema.request_type_id:
        workflow = schema.request_type.workflow_definition or workflow
    return "workflow" if workflow else "direct"


class SubmissionDetailPage(FormsPageMixin, DetailView):
    template_name = "forms/submission_detail.html"
    context_object_name = "submission"
    # The URLconf kwarg is ``submission_id`` (uuid); without this mapping the
    # generic detail view raises AttributeError → the page 500s for everyone.
    pk_url_kwarg = "submission_id"

    def get_queryset(self):
        return visible_submissions_for(self.request.user).select_related(
            "form_schema", "submitted_by", "reviewed_by",
            "workflow_instance", "workflow_instance__workflow_definition",
            "workflow_instance__current_state",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        submission = self.object
        context["rendered_fields"] = _rendered_fields(submission)
        context["attachments"] = submission.attachments.all()
        comments = submission.comments.select_related("author")
        if not can_view_internal_comments(self.request.user):
            comments = comments.exclude(is_internal=True)
        context["comments"] = comments
        context["business_request"] = getattr(submission, "business_request", None)
        context["can_edit"] = (
            submission.status == FormSubmission.Status.DRAFT
            and submission.submitted_by_id == self.request.user.pk
        )
        instance = submission.workflow_instance
        if instance is not None:
            context["workflow_state"] = instance.current_state
            context["action_logs"] = instance.action_logs.select_related("actor")[:50]
            try:
                from apps.workflow.services import WorkflowEngineService

                context["available_transitions"] = WorkflowEngineService().get_available_transitions(
                    instance, self.request.user
                )
            except Exception:  # noqa: BLE001 - page must not 500 on engine errors
                context["available_transitions"] = []
        return context
