from __future__ import annotations

from django.urls import path

from apps.leads import views


urlpatterns = [
    path("", views.LeadListCreateView.as_view(), name="lead-list-create"),
    path("assessors/", views.LeadAssessorListView.as_view(), name="lead-assessors"),
    path("<uuid:pk>/create-person/", views.LeadPersonCreateView.as_view(), name="lead-create-person"),
    path("teacher/", views.TeacherLeadListView.as_view(), name="teacher-lead-list"),
    path("teacher/<uuid:pk>/assess/", views.TeacherLeadAssessmentView.as_view(), name="teacher-lead-assess"),
    path("teacher/<uuid:pk>/", views.TeacherLeadDetailView.as_view(), name="teacher-lead-detail"),
    path("<uuid:pk>/", views.LeadDetailView.as_view(), name="lead-detail"),
    path("<uuid:pk>/<str:action>/", views.LeadActionView.as_view(), name="lead-action"),
]
