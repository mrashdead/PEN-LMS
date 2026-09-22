from django.urls import path

from apps.leads.pages import LeadTeacherAssessmentsPage, LeadsPage


urlpatterns = [
    path("", LeadsPage.as_view(), name="leads-dashboard"),
    path("assessments/", LeadTeacherAssessmentsPage.as_view(), name="leads-teacher-assessments"),
]
