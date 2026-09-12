"""Notification inbox URL configuration — mounted under /api/notifications/."""
from __future__ import annotations

from django.urls import path

from apps.workflow.notification_views import (
    NotificationInboxView,
    NotificationReadAllView,
    NotificationReadView,
)

urlpatterns = [
    path("", NotificationInboxView.as_view(), name="notification-inbox"),
    path("read-all/", NotificationReadAllView.as_view(), name="notification-read-all"),
    path("<uuid:pk>/read/", NotificationReadView.as_view(), name="notification-read"),
]
