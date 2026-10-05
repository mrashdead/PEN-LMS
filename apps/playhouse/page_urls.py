"""
Playhouse page routes (session auth, dashboard style) — mounted under /playhouse/.
"""
from __future__ import annotations

from django.urls import path

from apps.playhouse.pages import (
    PlayhouseAttendancePage,
    PlayhouseDashboardPage,
    PlayhouseFinancePage,
    PlayhouseSettingsPage,
)

urlpatterns = [
    path("", PlayhouseDashboardPage.as_view(), name="playhouse-dashboard"),
    path("attendance/", PlayhouseAttendancePage.as_view(), name="playhouse-attendance"),
    path("finance/", PlayhouseFinancePage.as_view(), name="playhouse-finance"),
    path("settings/", PlayhouseSettingsPage.as_view(), name="playhouse-settings"),
]
