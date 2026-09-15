"""
Creation hierarchy — who may create which kind of person/role.

Single source of truth for the "create person" gate, shared by the API
(PersonCreateSerializer) and the UI (so the form only offers what the server
will accept). A "target" is either a Person.Type (student/teacher/employee)
or a role code (supervisor/manager) assigned after creation.

    مدیر سیستم (workflow_admin) → manager, supervisor, employee, teacher, student
    مدیریت      (manager)       → supervisor, employee, teacher, student
    سرپرست      (supervisor)    → teacher, student
    کارمند عادی (employee)      → student

Roles are checked with the actor's *effective* role_codes(); the highest
matching tier wins. Superusers may create anything.
"""
from __future__ import annotations

# Ordered most→least privileged; a holder may create any target in their set.
CREATE_MATRIX: dict[str, set[str]] = {
    "workflow_admin": {"manager", "supervisor", "employee", "teacher", "student"},
    "manager": {"supervisor", "employee", "teacher", "student"},
    "supervisor": {"teacher", "student"},
    "employee": {"student"},
}

# person_type → the role it implies (for targets that are person types).
TYPE_TO_ROLE = {"student": "student", "teacher": "teacher", "employee": "employee"}


def allowed_targets(roles: set[str], *, is_superuser: bool = False) -> set[str]:
    """Union of creation targets the given roles permit (superuser → all)."""
    if is_superuser:
        return {"manager", "supervisor", "employee", "teacher", "student"}
    allowed: set[str] = set()
    for role in roles:
        allowed |= CREATE_MATRIX.get(role, set())
    return allowed


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
