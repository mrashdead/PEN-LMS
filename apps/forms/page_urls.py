"""Session-auth page routes for the forms UI (mounted under /forms/)."""
from __future__ import annotations

from django.urls import path

from apps.forms.pages import (
    SchemaAdminPage,
    SchemaBuilderPage,
    SchemaPickerPage,
    SubmissionCreatePage,
    SubmissionDetailPage,
    SubmissionEditPage,
    SubmissionListPage,
)

urlpatterns = [
    path("submissions/", SubmissionListPage.as_view(), name="submission-list"),
    path("submissions/new/", SchemaPickerPage.as_view(), name="submission-picker"),
    path("submissions/new/<slug:slug>/", SubmissionCreatePage.as_view(), name="submission-create"),
    path(
        "submissions/<uuid:submission_id>/",
        SubmissionDetailPage.as_view(),
        name="submission-detail-page",
    ),
    path(
        "submissions/<uuid:submission_id>/edit/",
        SubmissionEditPage.as_view(),
        name="submission-edit-page",
    ),
    # Schema administration (elevated roles only)
    path("admin/schemas/", SchemaAdminPage.as_view(), name="schema-admin"),
    path("admin/schemas/new/", SchemaBuilderPage.as_view(), name="schema-builder-create"),
    path(
        "admin/schemas/<slug:slug>/",
        SchemaBuilderPage.as_view(),
        name="schema-builder",
    ),
]
