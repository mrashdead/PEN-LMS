"""django-filter FilterSets for the forms API (ORM-only, no raw SQL)."""
from __future__ import annotations

import django_filters

from apps.forms.models import FormSubmission


class FormSubmissionFilterSet(django_filters.FilterSet):
    """Filtering contract for the submission list endpoint."""

    schema = django_filters.CharFilter(field_name="form_schema__slug")
    submitted_by = django_filters.UUIDFilter(field_name="submitted_by")
    submission_number = django_filters.CharFilter(field_name="submission_number", lookup_expr="iexact")
    created_after = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")
    submitted_after = django_filters.DateTimeFilter(field_name="submitted_at", lookup_expr="gte")
    submitted_before = django_filters.DateTimeFilter(field_name="submitted_at", lookup_expr="lte")
    workflow_status = django_filters.CharFilter(
        field_name="workflow_instance__status",
        help_text="workflow.Instance status: running/completed/rejected/cancelled",
    )

    class Meta:
        model = FormSubmission
        fields = [
            "status", "schema", "submitted_by", "submission_number",
            "created_after", "created_before",
            "submitted_after", "submitted_before", "workflow_status",
        ]
