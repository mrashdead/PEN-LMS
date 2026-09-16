"""
Creation hierarchy — who may create which kind of person/role.

Single source of truth for the "create person" gate, shared by the API
(PersonCreateSerializer, onboarding service) and the UI (so the form only
offers what the server will accept). A "target" is either a Person.Type
(student/teacher/employee/guardian) or a leadership role code
(supervisor/manager) assigned on top of an employee.

    مدیر سیستم (workflow_admin) → manager, supervisor, employee, teacher, student, guardian
    مدیریت      (manager)       → supervisor, employee, teacher, student, guardian
    سرپرست      (supervisor)    → teacher, student, guardian
    کارمند عادی (employee)      → student, guardian

``guardian`` sits beside ``student`` in every tier on purpose: a student
intake that collects father/mother data MUST be able to create those
guardian rows, otherwise the atomic onboarding transaction (see
apps.persons.onboarding) would always be one 403 away from failing.

Roles are checked with the actor's *effective* role_codes(); the highest
matching tier wins. Superusers may create anything.
"""
from __future__ import annotations

# Ordered most→least privileged; a holder may create any target in their set.
CREATE_MATRIX: dict[str, set[str]] = {
    "workflow_admin": {"manager", "supervisor", "employee", "teacher", "student", "guardian"},
    "manager": {"supervisor", "employee", "teacher", "student", "guardian"},
    "supervisor": {"teacher", "student", "guardian"},
    "employee": {"student", "guardian"},
}

#: Every creatable target, in the order the step-1 picker should show them.
ALL_TARGETS = ("manager", "supervisor", "employee", "teacher", "student", "guardian")

# target → the role it implies (person types map 1:1; leadership roles are
# themselves role codes).
TYPE_TO_ROLE = {
    "student": "student",
    "teacher": "teacher",
    "employee": "employee",
    "guardian": "guardian",
    "supervisor": "supervisor",
    "manager": "manager",
}


def allowed_targets(roles: set[str], *, is_superuser: bool = False) -> set[str]:
    """Union of creation targets the given roles permit (superuser → all)."""
    if is_superuser:
        return set(ALL_TARGETS)
    allowed: set[str] = set()
    for role in roles:
        allowed |= CREATE_MATRIX.get(role, set())
    return allowed


def allowed_targets_ordered(roles: set[str], *, is_superuser: bool = False) -> list[str]:
    """``allowed_targets`` in stable ALL_TARGETS order — for UI dropdowns."""
    allowed = allowed_targets(roles, is_superuser=is_superuser)
    return [t for t in ALL_TARGETS if t in allowed]


def can_create(roles: set[str], target: str, *, is_superuser: bool = False) -> bool:
    return target in allowed_targets(roles, is_superuser=is_superuser)



# Leadership roles that can be granted at creation (person_type stays
# "employee"; the role elevates them). Only the tiers above may grant them.
GRANTABLE_ROLES = {"supervisor", "manager"}
GRANT_RIGHTS: dict[str, set[str]] = {
    "workflow_admin": {"supervisor", "manager"},
    "manager": {"supervisor"},
}


def can_grant_role(roles: set[str], role: str, *, is_superuser: bool = False) -> bool:
    if not role:
        return True
    if is_superuser:
        return True
    allowed: set[str] = set()
    for r in roles:
        allowed |= GRANT_RIGHTS.get(r, set())
    return role in allowed
