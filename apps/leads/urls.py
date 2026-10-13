from __future__ import annotations

from django.urls import path

from apps.leads import views
from apps.leads.enrollment import LeadFinancialEnrollmentView, LeadOfferingDetailView, LeadOfferingListView


urlpatterns = [
    path("", views.LeadListCreateView.as_view(), name="lead-list-create"),
    path("assessors/", views.LeadAssessorListView.as_view(), name="lead-assessors"),
    path("courses/", views.LeadCourseListView.as_view(), name="lead-courses"),
    path("<uuid:pk>/create-person/", views.LeadPersonCreateView.as_view(), name="lead-create-person"),
    path("<uuid:lead_pk>/offerings/", LeadOfferingListView.as_view(), name="lead-offerings"),
    path("<uuid:lead_pk>/offerings/<uuid:pk>/", LeadOfferingDetailView.as_view(), name="lead-offering-detail"),
    path("<uuid:lead_pk>/enrollments/", LeadFinancialEnrollmentView.as_view(), name="lead-financial-enrollment"),
    path("assessments/", views.LeadAssessorQueueView.as_view(), name="lead-assessment-queue"),
    path("assessments/<uuid:pk>/assess/", views.LeadAssessorResultView.as_view(), name="lead-assessment-result"),
    path("assessments/<uuid:pk>/", views.LeadAssessorDetailView.as_view(), name="lead-assessment-detail"),
    path("<uuid:pk>/", views.LeadDetailView.as_view(), name="lead-detail"),
    path("<uuid:pk>/<str:action>/", views.LeadActionView.as_view(), name="lead-action"),
]
