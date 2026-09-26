"""Call-log API routes — mounted under /api/calls/."""
from django.urls import path

from apps.calls.views import (
    CallDetailView,
    CallFollowUpView,
    CallListCreateView,
    CallReportView,
    CallSubjectListView,
)

urlpatterns = [
    path("", CallListCreateView.as_view(), name="call-list"),
    path("subjects/", CallSubjectListView.as_view(), name="call-subject-list"),
    path("<uuid:pk>/", CallDetailView.as_view(), name="call-detail"),
    path("<uuid:pk>/follow-up/", CallFollowUpView.as_view(), name="call-follow-up"),
    path("reports/", CallReportView.as_view(), name="call-report"),
]
