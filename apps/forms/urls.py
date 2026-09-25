"""
Forms URL configuration — mounted under /api/forms/ in pen/urls.py.
"""
from __future__ import annotations

from django.urls import path

from apps.forms.views import (
    FormAttachmentDownloadView,
    FormAttachmentUploadView,
    FormCommentListCreateView,
    FormSchemaAdminView,
    FormSchemaDetailView,
    FormSchemaListView,
    FormSubmissionDetailView,
    FormSubmissionListCreateView,
    FormSubmissionRestoreView,
    FormSubmissionSoftDeleteView,
    FormSubmissionSubmitView,
    FormWorkflowApproveView,
    FormWorkflowRejectView,
    FormWorkflowTransitionView,
)
from apps.forms.request_views import (
    MyWorkView,
    RequestCancelView,
    RequestDetailView,
    RequestListCreateView,
    RequestSubmitView,
    RequestTransitionView,
    RequestTypeListView,
    RequestUpdateView,
)

urlpatterns = [
    # Unified business request API
    path("request-types/", RequestTypeListView.as_view(), name="request-type-list"),
    path("requests/", RequestListCreateView.as_view(), name="request-list-create"),
    path("requests/<uuid:request_id>/", RequestDetailView.as_view(), name="request-detail"),
    path("requests/<uuid:request_id>/update/", RequestUpdateView.as_view(), name="request-update"),
    path("requests/<uuid:request_id>/submit/", RequestSubmitView.as_view(), name="request-submit"),
    path("requests/<uuid:request_id>/transition/", RequestTransitionView.as_view(), name="request-transition"),
    path("requests/<uuid:request_id>/cancel/", RequestCancelView.as_view(), name="request-cancel"),
    path("my-work/", MyWorkView.as_view(), name="request-my-work"),
    # Schemas
    path("schemas/", FormSchemaListView.as_view(), name="form-schema-list"),
    path("schemas/<slug:slug>/", FormSchemaDetailView.as_view(), name="form-schema-detail"),
    # Schema administration (elevated roles)
    path("admin/schemas/", FormSchemaAdminView.as_view(), name="form-schema-admin"),
    # Submissions
    path("submissions/", FormSubmissionListCreateView.as_view(), name="form-submission-list"),
    path(
        "submissions/<uuid:submission_id>/",
        FormSubmissionDetailView.as_view(),
        name="form-submission-detail",
    ),
    path(
        "submissions/<uuid:submission_id>/delete/",
        FormSubmissionSoftDeleteView.as_view(),
        name="form-submission-delete",
    ),
    path(
        "submissions/<uuid:submission_id>/restore/",
        FormSubmissionRestoreView.as_view(),
        name="form-submission-restore",
    ),
    path(
        "submissions/<uuid:submission_id>/submit/",
        FormSubmissionSubmitView.as_view(),
        name="form-submission-submit",
    ),
    path(
        "submissions/<uuid:submission_id>/transition/",
        FormWorkflowTransitionView.as_view(),
        name="form-submission-transition",
    ),
    path(
        "submissions/<uuid:submission_id>/approve/",
        FormWorkflowApproveView.as_view(),
        name="form-submission-approve",
    ),
    path(
        "submissions/<uuid:submission_id>/reject/",
        FormWorkflowRejectView.as_view(),
        name="form-submission-reject",
    ),
    # Comments
    path(
        "submissions/<uuid:submission_id>/comments/",
        FormCommentListCreateView.as_view(),
        name="form-submission-comments",
    ),
    # Attachments
    path(
        "submissions/<uuid:submission_id>/attachments/",
        FormAttachmentUploadView.as_view(),
        name="form-submission-attachment-upload",
    ),
    path(
        "attachments/<uuid:attachment_id>/download/",
        FormAttachmentDownloadView.as_view(),
        name="form-attachment-download",
    ),
]
