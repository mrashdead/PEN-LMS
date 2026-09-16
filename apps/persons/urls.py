from __future__ import annotations

from django.urls import path

from apps.persons.onboarding_views import (
    OnboardingCreateView,
    OnboardingSchemaView,
    OnboardingTargetsView,
)
from apps.persons.views import (
    CreateUserForPersonView,
    GuardianLinkView,
    PersonDetailView,
    PersonListCreateView,
    PersonRestoreView,
    PersonSoftDeleteView,
    PersonTypeAssignView,
)

urlpatterns = [
    path("", PersonListCreateView.as_view(), name="person-list"),
    # ── Dynamic onboarding wizard (hierarchy-guarded, atomic) ────────────
    path(
        "onboarding/targets/",
        OnboardingTargetsView.as_view(),
        name="person-onboarding-targets",
    ),
    path(
        "onboarding/schema/",
        OnboardingSchemaView.as_view(),
        name="person-onboarding-schema",
    ),
    path(
        "onboarding/create/",
        OnboardingCreateView.as_view(),
        name="person-onboarding-create",
    ),
    path("<uuid:pk>/", PersonDetailView.as_view(), name="person-detail"),
    path("<uuid:pk>/delete/", PersonSoftDeleteView.as_view(), name="person-delete"),
    path("<uuid:pk>/restore/", PersonRestoreView.as_view(), name="person-restore"),
    path(
        "<uuid:person_id>/create-user/",
        CreateUserForPersonView.as_view(),
        name="person-create-user",
    ),
    path(
        "<uuid:person_id>/types/",
        PersonTypeAssignView.as_view(),
        name="person-type-assign",
    ),
    # ── Guardianship (تکفل) management on an existing student ────────────
    path(
        "<uuid:person_id>/guardians/",
        GuardianLinkView.as_view(),
        name="person-guardians",
    ),
]
