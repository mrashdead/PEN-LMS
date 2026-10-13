from django.urls import path

from apps.leads.pages import LeadAssessmentsPage, LeadsPage
from apps.leads.enrollment import LeadEnrollmentPage


urlpatterns = [
    path("", LeadsPage.as_view(), name="leads-dashboard"),
    path("assessments/", LeadAssessmentsPage.as_view(), name="leads-assessments"),
    path("<uuid:pk>/enrollment/", LeadEnrollmentPage.as_view(), name="lead-enrollment"),
]
