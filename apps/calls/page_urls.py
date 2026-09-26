from django.urls import path

from apps.calls.pages import CallsDashboardPage

urlpatterns = [path("", CallsDashboardPage.as_view(), name="calls-dashboard")]
