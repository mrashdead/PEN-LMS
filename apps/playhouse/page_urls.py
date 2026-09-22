"""
Playhouse page routes (session auth, dashboard style) — mounted under /playhouse/.
"""
from __future__ import annotations

from django.urls import path

from apps.playhouse.pages import PlayhouseDashboardPage, PlayhouseFinancePage

urlpatterns = [
    path("", PlayhouseDashboardPage.as_view(), name="playhouse-dashboard"),
    path("finance/", PlayhouseFinancePage.as_view(), name="playhouse-finance"),
]
