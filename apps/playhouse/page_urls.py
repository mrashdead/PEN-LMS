"""
Playhouse page routes (session auth, dashboard style) — mounted under /playhouse/.
"""
from __future__ import annotations

from django.urls import path
from django.views.generic import RedirectView

from apps.playhouse.pages import (
    PlayhouseDashboardPage,
    PlayhouseFinancePage,
)

urlpatterns = [
    path("", PlayhouseDashboardPage.as_view(), name="playhouse-dashboard"),
    path("attendance/", RedirectView.as_view(pattern_name="playhouse-dashboard", permanent=False, query_string=True), name="playhouse-attendance"),
    path("finance/", PlayhouseFinancePage.as_view(), name="playhouse-finance"),
]
