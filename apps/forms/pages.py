"""
Server-rendered pages for the forms UI (dashboard-style, session auth).

These views are thin: they resolve visibility through the SAME queryset
helpers the API uses (``visible_schemas_for`` / ``visible_submissions_for``)
and render templates. All business authorization and validation remain on
the API/service side — the templates never decide access.

Schema-admin pages (``SchemaAdminPage`` / ``SchemaBuilderPage``) additionally
restrict to elevated roles (same trio the API's ``CanManageFormSchemas``
uses); writes always go through the admin API endpoint, never direct ORM.
"""
from __future__ import annotations

import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView, TemplateView

from apps.forms import relations
from apps.forms.models import FormSchema, FormSubmission
from apps.forms.permissions import (
    ELEVATED_ROLES,
    can_view_internal_comments,
    visible_schemas_for,
    visible_submissions_for,
)

#: Cap relation option lists rendered into <select>/<fieldset> widgets.
RELATION_OPTION_LIMIT = 200


class FormsPageMixin(LoginRequiredMixin):
    """Pages require a logged-in session user (dashboard convention)."""


class SchemaAdminRequiredMixin(LoginRequiredMixin):
    """Schema-admin pages mirror the API's CanManageFormSchemas role trio."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        roles = set(request.user.role_codes()) if hasattr(request.user, "role_codes") else set()
        if not roles & ELEVATED_ROLES:
            raise Http404  # 404, not 403: don't advertise the admin surface
        return super().dispatch(request, *args, **kwargs)


class SchemaPickerPage(FormsPageMixin, TemplateView):
    template_name = "forms/schema_picker.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["schemas"] = visible_schemas_for(self.request.user).order_by("slug")
        return context


class SubmissionListPage(FormsPageMixin, ListView):
    template_name = "forms/submission_list.html"
    context_object_name = "submission_list"
    paginate_by = 20

    def get_queryset(self):
        qs = visible_submissions_for(self.request.user).select_related(
            "form_schema", "submitted_by"
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
        return context


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


# ─────────────────────────────────────────────────────────────────────────────
# Schema administration UI (elevated roles only)
# ─────────────────────────────────────────────────────────────────────────────

#: Registry keys exposed to the builder's relation picker, with availability.
def _relation_registry_context() -> list[dict]:
    entries = []
    for key, spec in relations.REGISTRY.items():
        entries.append({
            "key": key,
            "model": spec.model_label,
            "available": spec.is_available(),
            "display_field": spec.display_field,
        })
    entries.sort(key=lambda e: (not e["available"], e["key"]))
    return entries


class SchemaAdminPage(SchemaAdminRequiredMixin, TemplateView):
    """All schema versions (active + history) with field counts."""

    template_name = "forms/schema_admin.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        schemas = (
            FormSchema.objects.all()
            .prefetch_related("allowed_roles", "submissions")
            .order_by("slug", "-version")
        )
        grouped: dict[str, list] = {}
        for schema in schemas:
            grouped.setdefault(schema.slug, []).append(schema)
        cards = []
        for slug, versions in grouped.items():
            versions.sort(key=lambda s: -s.version)
            cards.append({
                "slug": slug,
                "title": versions[0].title,
                "description": versions[0].description,
                "versions": versions,
            })
        cards.sort(key=lambda c: c["slug"])
        context["schema_cards"] = cards
        context["total_schemas"] = sum(len(v) for v in grouped.values())
        return context


class SchemaBuilderPage(SchemaAdminRequiredMixin, TemplateView):
    """
    Visual builder for one schema slug.

    GET (no slug) → "create new" mode: fields start from a minimal skeleton.
    GET with slug  → edit mode: prefilled from the LATEST version; saving
    posts a NEW version through /api/forms/admin/schemas/ (immutability of
    published versions is a server contract — the UI never edits in place).
    """

    template_name = "forms/schema_builder.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs.get("slug")
        context["mode"] = "edit" if slug else "create"
        context["source_slug"] = slug
        source = None
        if slug:
            source = (
                FormSchema.objects.filter(slug=slug)
                .order_by("-version")
                .first()
            )
            if source is None:
                raise Http404
        context["schema"] = source
        context["fields_json"] = json.dumps(
            source.fields if source else [], ensure_ascii=False, indent=2
        )
        context["relation_registry"] = _relation_registry_context()
        context["next_version"] = (source.version + 1) if source else 1
        # Single JSON island for the builder JS (safe embedding via json_script).
        context["builder_ctx"] = {
            "mode": context["mode"],
            "slug": slug or "",
            "title": source.title if source else "",
            "description": source.description if source else "",
            "nextVersion": context["next_version"],
            "fields": source.fields if source else [],
            "relationRegistry": context["relation_registry"],
            "adminApiUrl": "/api/forms/admin/schemas/",
            "djangoAdminUrl": "/admin/forms/formschema/",
        }
        return context
