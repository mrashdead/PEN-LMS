from __future__ import annotations

from django.urls import path

from apps.persons.views import (
    CreateUserForPersonView,
    PersonDetailView,
    PersonListCreateView,
    StudentParentListCreateView,
)

urlpatterns = [
    path("", PersonListCreateView.as_view(), name="person-list"),
    path("<uuid:pk>/", PersonDetailView.as_view(), name="person-detail"),
    path(
        "<uuid:person_id>/create-user/",
        CreateUserForPersonView.as_view(),
        name="person-create-user",
    ),
    path(
        "student-parents/",
        StudentParentListCreateView.as_view(),
        name="student-parent-list",
    ),
]
