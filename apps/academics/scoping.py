"""
DataScope — central queryset scoping for academics/education (criterion §13-2).

Replaces view-level ad-hoc filtering with service/queryset-level functions, so
ANY future view, report or serializer reuses the identical rule and cannot
forget it. Conventions mirror apps/forms/permissions.py (proven patterns):

  - elevated roles (manager/workflow_admin/hr) → everything;
  - role code alone never grants rows — the user's persons.Person must be
    related to the object (teaches it / enrolled in it / parent of an
    enrolled child);
  - conditions compose with OR across a user's multiple roles, never AND.
"""
from __future__ import annotations

from typing import Optional

from django.db.models import Q

from apps.academics.models import ClassEnrollment, ClassGroup

ELEVATED_ROLES = {"manager", "workflow_admin", "hr"}


def _person_of(user):
    return getattr(user, "person", None)


def _roles_of(user) -> set:
    if user is None or not getattr(user, "is_authenticated", False):
        return set()
    return set(user.role_codes())


def class_groups_visible_to(user, *, for_write: bool = False):
    """
    Class groups a user may see (write endpoints additionally require a
    management role — enforced by permission classes, not here).

      elevated → all; teacher → groups they teach; student → groups they are
      enrolled in; parent → groups their children are enrolled in.
    """
    qs = ClassGroup.objects.select_related("term", "teacher")
    roles = _roles_of(user)
    if roles & ELEVATED_ROLES:
        return qs
    person = _person_of(user)
    if person is None:
        return qs.none()

    condition = Q(teacher=person) if "teacher" in roles else Q()
    if "student" in roles:
        condition |= Q(
            enrollments__student=person,
            enrollments__is_active=True,
            enrollments__is_deleted=False,
        )
    if not condition:
        return qs.none()
    return qs.filter(condition).distinct()


def enrollments_visible_to(user):
    """
    Enrollment rows a user may see: elevated → all; teacher → enrollments of
    groups they teach; student → own enrollments.
    """
    qs = ClassEnrollment.objects.select_related("class_group", "student")
    roles = _roles_of(user)
    if roles & ELEVATED_ROLES:
        return qs
    person = _person_of(user)
    if person is None:
        return qs.none()

    condition = Q()
    if "teacher" in roles:
        condition |= Q(class_group__teacher=person)
    if "student" in roles:
        condition |= Q(student=person)
    if not condition:
        return qs.none()
    return qs.filter(condition).distinct()


def education_sessions_visible_to(user):
    """
    Real sessions (education.ClassSession) a user may see: elevated → all;
    teacher → sessions they teach OR groups they own; student →
    sessions of their groups.
    """
    from apps.education.models import ClassSession

    qs = ClassSession.objects.select_related("offering", "class_group", "teacher", "location")
    roles = _roles_of(user)
    if roles & ELEVATED_ROLES:
        return qs
    person = _person_of(user)
    if person is None:
        return qs.none()

    condition = Q(teacher=person) if "teacher" in roles else Q()
    if "student" in roles:
        condition |= Q(
            class_group__enrollments__student=person,
            class_group__enrollments__is_active=True,
            class_group__enrollments__is_deleted=False,
        )
    if not condition:
        return qs.none()
    return qs.filter(condition).distinct()


def education_sessions_for_teacher(user):
    """Strict variant used by attendance writes: ONLY sessions this user teaches."""
    person = _person_of(user)
    if person is None:
        from apps.education.models import ClassSession
        return ClassSession.objects.none()
    from apps.education.models import ClassSession
    return ClassSession.objects.filter(teacher=person, is_deleted=False)


def person_scoped_or_none(user, person_id) -> Optional[object]:
    """Resolve a Person for a user or None if outside their scope (detail views)."""
    from apps.persons.services import persons_visible_to

    return persons_visible_to(user).filter(pk=person_id).first()
