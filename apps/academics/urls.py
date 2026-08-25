from __future__ import annotations

from django.urls import path

from apps.academics.views import (
    AcademicTermActivateView,
    AcademicTermDetailView,
    AcademicTermListCreateView,
    ClassEnrollmentDetailView,
    ClassEnrollmentListCreateView,
    ClassGroupDetailView,
    ClassGroupListCreateView,
)

urlpatterns = [
    # Academic Terms
    path("terms/", AcademicTermListCreateView.as_view(), name="academic-term-list"),
    path("terms/<uuid:pk>/", AcademicTermDetailView.as_view(), name="academic-term-detail"),
    path("terms/<uuid:pk>/activate/", AcademicTermActivateView.as_view(), name="academic-term-activate"),
    # Class Groups
    path("class-groups/", ClassGroupListCreateView.as_view(), name="class-group-list"),
    path("class-groups/<uuid:pk>/", ClassGroupDetailView.as_view(), name="class-group-detail"),
    # Enrollments
    path("enrollments/", ClassEnrollmentListCreateView.as_view(), name="enrollment-list"),
    path("enrollments/<uuid:pk>/", ClassEnrollmentDetailView.as_view(), name="enrollment-detail"),
]
