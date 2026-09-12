"""Internal messaging URL configuration — mounted under /api/messaging/."""
from __future__ import annotations

from django.urls import path

from apps.messaging.views import (
    DirectoryView,
    InboxView,
    ThreadCreateView,
    ThreadDetailView,
    ThreadHideView,
    ThreadReadView,
    ThreadReplyView,
    UnreadCountView,
)

urlpatterns = [
    path("", InboxView.as_view(), name="messaging-inbox"),
    path("unread-count/", UnreadCountView.as_view(), name="messaging-unread-count"),
    path("directory/", DirectoryView.as_view(), name="messaging-directory"),
    path("threads/", ThreadCreateView.as_view(), name="messaging-thread-create"),
    path("threads/<uuid:pk>/", ThreadDetailView.as_view(), name="messaging-thread-detail"),
    path("threads/<uuid:pk>/reply/", ThreadReplyView.as_view(), name="messaging-thread-reply"),
    path("threads/<uuid:pk>/read/", ThreadReadView.as_view(), name="messaging-thread-read"),
    path("threads/<uuid:pk>/hide/", ThreadHideView.as_view(), name="messaging-thread-hide"),
]
