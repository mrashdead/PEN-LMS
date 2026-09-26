from django.urls import path

from apps.staff.pages import StaffDashboardPage

urlpatterns = [path("", StaffDashboardPage.as_view(), name="staff-dashboard")]
