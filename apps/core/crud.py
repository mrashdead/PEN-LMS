"""Shared, object-aware CRUD authorization for the Pen domain.

The UI consumes the same capability decision as the API.  Queryset scoping
still hides objects a user cannot see; this module is the final object-level
guard for update/delete and the source of truth for row actions.
"""
from __future__ import annotations

from typing import Any

from django.core.exceptions import PermissionDenied

from apps.core.access_enforcer import acl_strict
from apps.core.models import AuditEvent


# Maps `resource_for()` short key → (app_label, model_name) for ACL model entries.
_MODEL_SHORT_TO_KEY: dict[str, str] = {
    "persons": "persons.person",
    "departments": "education.department",
    "locations": "education.location",
    "lessons": "education.lesson",
    "courses": "education.course",
    "offerings": "education.courseoffering",
    "sessions": "education.classsession",
    "enrollments": "academics.classenrollment",
    "holidays": "education.academicholiday",
    "terms": "academics.academicterm",
    "class-groups": "academics.classgroup",
    "submissions": "forms.formsubmission",
    "requests": "workflow.instance",
}
# Verb for each can_* function — used for the ACL layer.
_VERB_FOR_CREATE = "add"
_VERB_FOR_VIEW = "view"
_VERB_FOR_CHANGE = "change"
_VERB_FOR_DELETE = "delete"
_VERB_FOR_RESTORE = "change"  # restore uses change-level permission


def _acl_model_key(resource: str) -> str | None:
    """Convert resource short-key to app_label.model_name, or return None."""
    return _MODEL_SHORT_TO_KEY.get(resource)


RESOURCE_MANAGER_ROLES = {"manager", "workflow_admin"}
HR_ROLES = {"manager", "workflow_admin", "hr"}
SUPERVISOR_ROLES = {"supervisor"}
ACADEMIC_RESOURCES = {
    "departments", "locations", "lessons", "courses", "offerings", "sessions",
    "enrollments", "holidays", "terms", "class-groups",
}


def roles_for(user) -> set[str]:
    if not user or not getattr(user, "is_authenticated", False):
        return set()
    return set(user.role_codes()) if hasattr(user, "role_codes") else set()


def is_superadmin(user) -> bool:
    return bool(user and getattr(user, "is_superuser", False))


def is_elevated(user) -> bool:
    return is_superadmin(user) or bool(roles_for(user) & RESOURCE_MANAGER_ROLES)


def resource_for(obj: Any) -> str:
    model = getattr(obj, "_meta", None)
    key = f"{getattr(model, 'app_label', '')}.{getattr(model, 'model_name', '')}"
    return {
        "persons.person": "persons",
        "education.department": "departments",
        "education.location": "locations",
        "education.lesson": "lessons",
        "education.course": "courses",
        "education.courseoffering": "offerings",
        "education.classsession": "sessions",
        "education.offeringenrollment": "enrollments",
        "education.academicholiday": "holidays",
        "academics.academicterm": "terms",
        "academics.classgroup": "class-groups",
        "academics.classenrollment": "enrollments",
        "forms.formsubmission": "submissions",
        "workflow.instance": "requests",
    }.get(key, key.rsplit(".", 1)[-1])


def _person_id(user):
    return getattr(user, "person_id", None)


def is_owner(user, obj: Any) -> bool:
    user_id = getattr(user, "pk", None)
    person_id = _person_id(user)
    for field in ("user_id", "created_by_id", "registered_by_id", "submitted_by_id", "requester_id"):
        if user_id and getattr(obj, field, None) == user_id:
            return True
    for field in ("instructor_id", "teacher_id", "student_id", "subject_person_id"):
        value = getattr(obj, field, None)
        if person_id and value == person_id:
            return True
    return False


def is_draft(obj: Any) -> bool:
    status = str(getattr(obj, "status", "") or "").lower()
    return status in {"draft", "pending", "new", "running"} or not status


def can_view_resource(user, obj: Any, resource: str | None = None) -> bool:
    resource = resource or resource_for(obj)
    roles = roles_for(user)
    if resource == "persons":
        baseline = bool(roles & {"employee", "teacher", "student", "guardian", "supervisor"}) or is_owner(user, obj)
    elif resource in ACADEMIC_RESOURCES:
        baseline = bool(roles & {"teacher", "employee", "supervisor", "student", "guardian"}) or is_owner(user, obj)
    elif resource == "submissions":
        baseline = is_owner(user, obj) or bool(roles & {"teacher", "employee", "student", "guardian"})
    elif resource == "requests":
        baseline = is_owner(user, obj) or bool(roles & {"teacher", "employee", "student", "guardian"})
    else:
        baseline = is_owner(user, obj)
    return acl_strict(user, "model", _acl_model_key(resource) or resource, _VERB_FOR_VIEW, baseline)


def can_create_resource(user, resource: str) -> bool:
    roles = roles_for(user)
    if is_superadmin(user) or roles & RESOURCE_MANAGER_ROLES:
        baseline = True
    elif "supervisor" in roles and resource in {"persons", "lessons", "courses", "offerings", "sessions"}:
        baseline = True
    else:
        baseline = False
    return acl_strict(user, "model", _acl_model_key(resource) or resource, _VERB_FOR_CREATE, baseline)


def can_edit_resource(user, obj: Any, resource: str | None = None) -> bool:
    resource = resource or resource_for(obj)
    roles = roles_for(user)
    if is_superadmin(user):
        baseline = True
    elif roles & RESOURCE_MANAGER_ROLES:
        baseline = True
    elif "hr" in roles and resource in {"persons", "submissions", "requests"}:
        baseline = True
    else:
        baseline = bool(roles & SUPERVISOR_ROLES and is_owner(user, obj) and is_draft(obj))
    return acl_strict(user, "model", _acl_model_key(resource) or resource, _VERB_FOR_CHANGE, baseline)


def can_delete_resource(user, obj: Any, resource: str | None = None) -> bool:
    resource = resource or resource_for(obj)
    roles = roles_for(user)
    if is_superadmin(user):
        baseline = True
    elif roles & RESOURCE_MANAGER_ROLES:
        baseline = True
    elif "hr" in roles and resource in {"persons", "submissions", "requests"}:
        baseline = True
    else:
        baseline = bool(roles & SUPERVISOR_ROLES and is_owner(user, obj) and is_draft(obj))
    return acl_strict(user, "model", _acl_model_key(resource) or resource, _VERB_FOR_DELETE, baseline)


def can_restore_resource(user, obj: Any) -> bool:
    baseline = is_superadmin(user) or "workflow_admin" in roles_for(user)
    return acl_strict(user, "model", _acl_model_key(resource_for(obj)) or "", _VERB_FOR_RESTORE, baseline)


def crud_actions(user, obj: Any, resource: str | None = None) -> dict[str, bool]:
    resource = resource or resource_for(obj)
    return {
        "view": can_view_resource(user, obj, resource),
        "edit": can_edit_resource(user, obj, resource),
        "delete": can_delete_resource(user, obj, resource),
    }


def require_crud(user, obj: Any, action: str, resource: str | None = None) -> None:
    allowed = {
        "view": can_view_resource,
        "edit": can_edit_resource,
        "delete": can_delete_resource,
    }.get(action)
    if allowed is None or not allowed(user, obj, resource):
        raise PermissionDenied("شما مجوز این عملیات روی این رکورد را ندارید.")


def soft_delete_object(obj: Any, *, actor, request=None, resource: str | None = None) -> None:
    require_crud(actor, obj, "delete", resource)
    if not hasattr(obj, "soft_delete"):
        raise PermissionDenied("این موجودیت از حذف نرم پشتیبانی نمی‌کند.")
    obj.soft_delete()
    AuditEvent.record(
        kind=AuditEvent.Kind.FIELD_CHANGE,
        summary=f"حذف نرم {resource or resource_for(obj)}",
        actor=actor,
        obj=obj,
        request=request,
        metadata={"action": "soft_delete", "resource": resource or resource_for(obj)},
    )


def restore_object(obj: Any, *, actor, request=None, resource: str | None = None) -> None:
    if not can_restore_resource(actor, obj):
        raise PermissionDenied("فقط مدیر سیستم می‌تواند رکورد حذف‌شده را بازیابی کند.")
    obj.restore()
    AuditEvent.record(
        kind=AuditEvent.Kind.FIELD_CHANGE,
        summary=f"بازیابی {resource or resource_for(obj)}",
        actor=actor,
        obj=obj,
        request=request,
        metadata={"action": "restore", "resource": resource or resource_for(obj)},
    )
