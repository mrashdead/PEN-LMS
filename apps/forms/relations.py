"""
Server-side relation allowlist.

Dynamic ``relation``/``multi_relation`` fields may only point at models
declared in this static registry. Request data can never supply an app label
or model name — only a registry key from this file is accepted, and each key
resolves to a fixed model label via ``apps.get_model`` called with the
constants below (never with client-controlled values).

Each spec also carries a permission filter so relation pickers and the data
validator enforce object-level access (e.g. a teacher may only reference
their own class groups via ``ClassGroup.teacher`` → ``persons.Person``).

Verified against the current repository:
  - ``academics.ClassGroup.teacher``  → persons.Person (nullable FK)
  - ``academics.ClassEnrollment.class_group`` / ``.student`` (student → Person)
  - ``persons.Person.user`` OneToOne, reverse accessor ``user.person``
  - ``persons.StudentParent`` exists: parent → Person, student → Person,
    with ``is_active`` / ``is_deleted`` flags and related names
    ``parent_links`` (from parent) / ``parent_of`` (from student).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from django.apps import apps
from django.db.models import QuerySet

# Elevated roles that may see all relation targets (existing repo conventions:
# apps.core.permissions.IsManagerOrAdmin / workflow views use the same trio).
ELEVATED_ROLES = {"manager", "workflow_admin", "hr"}


class RelationError(Exception):
    """Base error for relation resolution."""


class UnknownRelationKey(RelationError):
    """Raised when a request/schema references a key not in the allowlist."""


class MissingRequiredRelation(RelationError):
    """Raised when a required relation target model is not installed."""

    def __init__(self, key: str, model_label: str, schema_slugs: list[str] | None = None):
        self.key = key
        self.model_label = model_label
        self.schema_slugs = schema_slugs or []
        where = f" (used by: {', '.join(self.schema_slugs)})" if self.schema_slugs else ""
        super().__init__(
            f"Required relation '{key}' maps to model '{model_label}' which is not "
            f"installed{where}. Create the model or adjust the schema."
        )


@dataclass(frozen=True)
class RelationSpec:
    key: str
    app_label: str
    model_name: str
    display_field: str = "name"
    allowed_lookup_fields: tuple[str, ...] = ("id",)
    optional: bool = False
    # (user, queryset) -> queryset filter applied on top of the base queryset.
    permission_filter: Optional[Callable[[Any, QuerySet], QuerySet]] = None
    # Extra metadata recorded when an optional target is unavailable.
    fallback: dict[str, Any] = field(default_factory=dict)

    @property
    def model_label(self) -> str:
        return f"{self.app_label}.{self.model_name}"

    def is_available(self) -> bool:
        # _model_exists() is authoritative: apps.get_model() only resolves
        # when the app is installed AND the model exists. (apps.is_installed()
        # expects the full dotted name, e.g. "apps.persons", not the label
        # "persons", so it is deliberately NOT used here.)
        return _model_exists(self.app_label, self.model_name)

    def get_model(self):
        if not self.is_available():
            raise MissingRequiredRelation(self.key, self.model_label)
        # Fixed labels only — declared in this file, never client input.
        return apps.get_model(self.app_label, self.model_name)

    def base_queryset(self) -> QuerySet:
        return self.get_model()._default_manager.all()

    def queryset_for_user(self, user) -> QuerySet:
        qs = self.base_queryset()
        if self.permission_filter is not None:
            qs = self.permission_filter(user, qs)
        return qs


def _model_exists(app_label: str, model_name: str) -> bool:
    try:
        apps.get_model(app_label, model_name)
        return True
    except LookupError:
        return False


def _roles_of(user) -> set[str]:
    if user is None or not getattr(user, "is_authenticated", False):
        return set()
    return set(user.role_codes()) if hasattr(user, "role_codes") else set()


def _person_of(user):
    """persons.Person linked to this user (Person.user OneToOne, related_name='person')."""
    return getattr(user, "person", None)


# ── Permission filters (use real relationship names; subqueries, no lists) ──

def _person_filter(user, qs):
    """Active persons; students/parents limited to themselves + linked children."""
    qs = qs.filter(is_active=True)
    roles = _roles_of(user)
    if roles & ELEVATED_ROLES or roles & {"teacher", "employee"}:
        return qs
    person = _person_of(user)
    if person is None:
        return qs.none()
    if "student" in roles:
        return qs.filter(pk=person.pk)
    if "parent" in roles:
        # Subquery over StudentParent links — never materialize into Python.
        return qs.filter(
            parent_of__parent=person,
            parent_of__is_active=True,
            parent_of__is_deleted=False,
        ).distinct()
    return qs.none()


def _class_group_filter(user, qs):
    """Teacher → own classes (ClassGroup.teacher); student → enrolled classes;
    parent → classes their children are enrolled in; elevated → all.

    Multiple roles compose with OR (a teacher who is also a student sees both
    sets), never AND — an AND would silently hide legitimate rows.
    """
    from django.db.models import Q

    qs = qs.filter(is_active=True)
    roles = _roles_of(user)
    if roles & ELEVATED_ROLES:
        return qs
    person = _person_of(user)
    if person is None:
        return qs.none()

    condition = Q()
    if "teacher" in roles:
        condition |= Q(teacher=person)
    if "student" in roles:
        condition |= Q(
            enrollments__student=person,
            enrollments__is_active=True,
            enrollments__is_deleted=False,
        )
    if "parent" in roles:
        condition |= Q(
            enrollments__student__parent_of__parent=person,
            enrollments__student__parent_of__is_active=True,
            enrollments__student__parent_of__is_deleted=False,
            enrollments__is_active=True,
            enrollments__is_deleted=False,
        )
    if not condition:
        return qs.none()
    return qs.filter(condition).distinct()


def _term_filter(user, qs):
    """Terms are institution-wide reference data: readable by any active user."""
    return qs.filter(is_active=True)


# ── Static allowlist ──────────────────────────────────────────────────────

REGISTRY: dict[str, RelationSpec] = {
    "persons.person": RelationSpec(
        key="persons.person",
        app_label="persons",
        model_name="Person",
        display_field="display_name",
        allowed_lookup_fields=("id", "national_code", "student_code", "employee_code"),
        permission_filter=_person_filter,
    ),
    "academic.class_group": RelationSpec(
        key="academic.class_group",
        app_label="academics",
        model_name="ClassGroup",
        display_field="name",
        allowed_lookup_fields=("id", "code"),
        permission_filter=_class_group_filter,
    ),
    "academic.term": RelationSpec(
        key="academic.term",
        app_label="academics",
        model_name="AcademicTerm",
        display_field="title",
        allowed_lookup_fields=("id",),
        permission_filter=_term_filter,
    ),
    # ── Optional targets (model may not exist yet; explicit fallback only) ──
    "academic.venue": RelationSpec(
        key="academic.venue",
        app_label="academics",
        model_name="Location",
        display_field="name",
        optional=True,
        fallback={
            "type": "text",
            "reason": "academics.Location model not installed; venue captured as free text.",
        },
    ),
    # ── Required targets that are NOT yet installed (fail closed at seed) ──
    # These map to the planned `education` app (PHASE_PLAN.md فاز ۱). Until the
    # models exist, schemas referencing them cannot be seeded or submitted.
    "academic.lesson": RelationSpec(
        key="academic.lesson",
        app_label="education",
        model_name="Lesson",
        display_field="title",
        optional=False,
    ),
    "academic.course": RelationSpec(
        key="academic.course",
        app_label="education",
        model_name="Course",
        display_field="title",
        optional=False,
    ),
    "academic.course_offering": RelationSpec(
        key="academic.course_offering",
        app_label="education",
        model_name="CourseOffering",
        display_field="title",
        optional=False,
    ),
    "academic.department": RelationSpec(
        key="academic.department",
        app_label="education",
        model_name="Department",
        display_field="name",
        optional=False,
    ),
}


def resolve(key: str) -> RelationSpec:
    """Return the spec for a registry key or raise UnknownRelationKey (fail closed)."""
    spec = REGISTRY.get(key) if isinstance(key, str) else None
    if spec is None:
        raise UnknownRelationKey(f"Relation key '{key}' is not in the allowlist.")
    return spec


def ensure_available(spec: RelationSpec, schema_slugs: list[str] | None = None) -> None:
    """Raise MissingRequiredRelation for an unavailable required target."""
    if not spec.is_available() and not spec.optional:
        raise MissingRequiredRelation(spec.key, spec.model_label, schema_slugs)
