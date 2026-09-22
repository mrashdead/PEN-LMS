"""
Playhouse API URL routes — mounted under /api/playhouse/ in pen/urls.py.
"""
from __future__ import annotations

from django.urls import path

from apps.playhouse import views

urlpatterns = [
    path("config/", views.ConfigView.as_view(), name="ph-config"),
    path("sessions/", views.SessionListCreateView.as_view(), name="ph-session-create"),
    path("sessions/active/", views.ActiveSessionsView.as_view(), name="ph-sessions-active"),
    # invoice route MUST precede the generic <str:action> route so that
    # `/sessions/<uuid>/invoice/` resolves here, not as action="invoice".
    path("sessions/<uuid:session_pk>/invoice/", views.InvoiceCreateView.as_view(), name="ph-invoice-create"),
    path("sessions/<uuid:pk>/<str:action>/", views.SessionActionView.as_view(), name="ph-session-action"),
    path("members/search/", views.MemberAutocompleteView.as_view(), name="ph-member-search"),
    path("invoices/<uuid:pk>/", views.InvoiceDetailView.as_view(), name="ph-invoice-detail"),
    path("invoices/<uuid:pk>/pay/", views.InvoiceMarkPaidView.as_view(), name="ph-invoice-pay"),
    path("finance/report/", views.FinanceReportView.as_view(), name="ph-finance-report"),
]
