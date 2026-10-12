"""
Playhouse API URL routes — mounted under /api/playhouse/ in pen/urls.py.
"""
from __future__ import annotations

from django.urls import path

from apps.playhouse import views

urlpatterns = [
    path("config/", views.ConfigView.as_view(), name="ph-config"),
    path("cafe-presets/", views.CafePresetListCreateView.as_view(), name="ph-cafe-presets"),
    path("cafe-presets/<uuid:pk>/", views.CafePresetDetailView.as_view(), name="ph-cafe-preset-detail"),
    path("sessions/", views.SessionListCreateView.as_view(), name="ph-session-create"),
    path("sessions/active/", views.ActiveSessionsView.as_view(), name="ph-sessions-active"),
    path("sessions/<uuid:session_pk>/cafe-orders/", views.CafeOrderCreateView.as_view(), name="ph-cafe-order-create"),
    path("sessions/<uuid:session_pk>/payments/", views.SessionPaymentsView.as_view(), name="ph-session-payment-create"),
    path("kitchen/orders/", views.KitchenOrdersView.as_view(), name="ph-kitchen-orders"),
    path("kitchen/orders/<uuid:pk>/status/", views.KitchenOrderStatusView.as_view(), name="ph-kitchen-order-status"),
    path("cafe-orders/<uuid:pk>/cancel/", views.CafeOrderCancelView.as_view(), name="ph-cafe-order-cancel"),
    path("attendance/", views.AttendanceReportView.as_view(), name="ph-attendance"),
    # invoice route MUST precede the generic <str:action> route so that
    # `/sessions/<uuid>/invoice/` resolves here, not as action="invoice".
    path("sessions/<uuid:session_pk>/invoice/", views.InvoiceCreateView.as_view(), name="ph-invoice-create"),
    path("sessions/<uuid:pk>/<str:action>/", views.SessionActionView.as_view(), name="ph-session-action"),
    path("members/search/", views.MemberAutocompleteView.as_view(), name="ph-member-search"),
    path("members/<uuid:pk>/", views.PlayhouseMemberDetailView.as_view(), name="ph-member-detail"),
    path("invoices/<uuid:pk>/", views.InvoiceDetailView.as_view(), name="ph-invoice-detail"),
    path("invoices/<uuid:pk>/pay/", views.InvoiceMarkPaidView.as_view(), name="ph-invoice-pay"),
    path("invoices/<uuid:pk>/void/", views.InvoiceVoidView.as_view(), name="ph-invoice-void"),
    path("payments/<uuid:pk>/reverse/", views.PaymentReverseView.as_view(), name="ph-payment-reverse"),
    path("finance/report/", views.FinanceReportView.as_view(), name="ph-finance-report"),
]
