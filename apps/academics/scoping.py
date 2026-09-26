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
# Staff roles with model-level read permission may use shared educational
# reference data. Teacher access remains scoped to the teacher's own classes.
REFERENCE_DATA_ROLES = ELEVATED_ROLES | {"employee", "supervisor"}

#: Role code for a guardian/parent account (provisioned by
#: ``PersonService._create_user_for_person`` when Person.type == guardian).
#: The code alone grants NOTHING — rows come only through an active
#: ``StudentGuardian`` link, optionally narrowed by the link's per-link flags.
GUARDIAN_ROLE = "guardian"


def _person_of(user):
    return getattr(user, "person", None)


def _roles_of(user) -> set:
    if user is None or not getattr(user, "is_authenticated", False):
        return set()
    return set(user.role_codes())


def _ward_ids_of(person):
    """
    Student PKs this Person is an ACTIVE guardian of (persons.StudentGuardian).

    Materialized as a list, not a subquery: the link table lives in another
    app (import at call time keeps apps decoupled) and the list is tiny
    (1-2 wards per guardian). Empty list → callers add nothing to their OR.
    """
    if person is None:
        return []
    from apps.persons.models import StudentGuardian

    return list(
        StudentGuardian.objects.filter(
            guardian=person, is_active=True, is_deleted=False,
        ).values_list("student_id", flat=True)
    )


def ward_student_ids_for(user):
    """Public helper (e.g. persons_visible_to, calendars): wards of this user."""
    if user is None or not getattr(user, "is_authenticated", False):
        return []
    return _ward_ids_of(_person_of(user))


def class_groups_visible_to(user, *, for_write: bool = False):
    """
    Class groups a user may see (write endpoints additionally require a
    management role — enforced by permission classes, not here).

      elevated → all; teacher → groups they teach; student → groups they are
      enrolled in; parent → groups their children are enrolled in.
    """
    qs = ClassGroup.objects.select_related("term", "teacher")
    roles = _roles_of(user)
    if roles & REFERENCE_DATA_ROLES:
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
    if GUARDIAN_ROLE in roles:
        wards = _ward_ids_of(person)
        if wards:
            condition |= Q(
                enrollments__student_id__in=wards,
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
    if roles & REFERENCE_DATA_ROLES:
        return qs
    person = _person_of(user)
    if person is None:
        return qs.none()

    condition = Q()
    if "teacher" in roles:
        condition |= Q(class_group__teacher=person)
    if "student" in roles:
        condition |= Q(student=person)
    if GUARDIAN_ROLE in roles:
        wards = _ward_ids_of(person)
        if wards:
            condition |= Q(student_id__in=wards)
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

    qs = ClassSession.objects.select_related(
        "offering", "offering__course", "class_group", "teacher", "location",
        "lesson",
    )
    roles = _roles_of(user)
    if roles & REFERENCE_DATA_ROLES:
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
        # offering-keyed sessions (course-run world): only ENROLLED students.
        condition |= Q(
            offering__enrollments__student=person,
            offering__enrollments__is_active=True,
            offering__enrollments__is_deleted=False,
        )
    if GUARDIAN_ROLE in roles:
        wards = _ward_ids_of(person)
        if wards:
            condition |= Q(
                class_group__enrollments__student_id__in=wards,
                class_group__enrollments__is_active=True,
                class_group__enrollments__is_deleted=False,
            )
            condition |= Q(
                offering__enrollments__student_id__in=wards,
                offering__enrollments__is_active=True,
                offering__enrollments__is_deleted=False,
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


def education_offerings_visible_to(user):
    """Shared offerings for staff; teachers only see offerings they teach."""
    from apps.education.models import CourseOffering

    qs = CourseOffering.objects.select_related("course", "location", "instructor")
    roles = _roles_of(user)
    if roles & REFERENCE_DATA_ROLES:
        return qs

    person = _person_of(user)
    if person is None or "teacher" not in roles:
        return qs.none()

    return qs.filter(
        Q(instructor=person)
        | Q(class_groups__teacher=person, class_groups__is_deleted=False)
        | Q(sessions__teacher=person, sessions__is_deleted=False)
    ).distinct()


def education_courses_visible_to(user):
    """Courses available to staff, or courses behind a teacher's own offerings."""
    from apps.education.models import Course

    qs = Course.objects.select_related("department")
    roles = _roles_of(user)
    if roles & REFERENCE_DATA_ROLES:
        return qs
    if "teacher" not in roles:
        return qs.none()

    return qs.filter(offerings__in=education_offerings_visible_to(user)).distinct()


def person_scoped_or_none(user, person_id) -> Optional[object]:
    """Resolve a Person for a user or None if outside their scope (detail views)."""
    from apps.persons.services import persons_visible_to

    return persons_visible_to(user).filter(pk=person_id).first()
