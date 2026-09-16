from __future__ import annotations

from django.urls import path

from apps.academics.views import (
    AcademicTermActivateView,
    AcademicTermDetailView,
    AcademicTermListCreateView,
    AcademicTermRestoreView,
    AcademicTermSoftDeleteView,
    ClassEnrollmentDetailView,
    ClassEnrollmentListCreateView,
    ClassEnrollmentRestoreView,
    ClassEnrollmentSoftDeleteView,
    ClassGroupDetailView,
    ClassGroupListCreateView,
    ClassGroupRestoreView,
    ClassGroupSoftDeleteView,
)

urlpatterns = [
    # Academic Terms
    path("terms/", AcademicTermListCreateView.as_view(), name="academic-term-list"),
    path("terms/<uuid:pk>/", AcademicTermDetailView.as_view(), name="academic-term-detail"),
    path("terms/<uuid:pk>/delete/", AcademicTermSoftDeleteView.as_view(), name="academic-term-delete"),
    path("terms/<uuid:pk>/restore/", AcademicTermRestoreView.as_view(), name="academic-term-restore"),
    path("terms/<uuid:pk>/activate/", AcademicTermActivateView.as_view(), name="academic-term-activate"),
    # Class Groups
    path("class-groups/", ClassGroupListCreateView.as_view(), name="class-group-list"),
    path("class-groups/<uuid:pk>/", ClassGroupDetailView.as_view(), name="class-group-detail"),
    path("class-groups/<uuid:pk>/delete/", ClassGroupSoftDeleteView.as_view(), name="class-group-delete"),
    path("class-groups/<uuid:pk>/restore/", ClassGroupRestoreView.as_view(), name="class-group-restore"),
    # Enrollments
    path("enrollments/", ClassEnrollmentListCreateView.as_view(), name="enrollment-list"),
    path("enrollments/<uuid:pk>/", ClassEnrollmentDetailView.as_view(), name="enrollment-detail"),
    path("enrollments/<uuid:pk>/delete/", ClassEnrollmentSoftDeleteView.as_view(), name="enrollment-delete"),
    path("enrollments/<uuid:pk>/restore/", ClassEnrollmentRestoreView.as_view(), name="enrollment-restore"),
]
