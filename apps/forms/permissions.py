"""
Role- and object-level authorization for the forms API.

Two layers, mirroring the rest of the project:

  1. ``get_queryset()`` scoping — views call ``visible_submissions_for(user)``
     / ``visible_schemas_for(user)`` so unauthorized rows never appear in
     lists and detail lookups 404 instead of leaking existence.
  2. ``has_object_permission`` — defense in depth for detail/action routes.

Role codes come from ``User.role_codes()`` (verified: returns ``set[str]``)
and are the seeded ones: employee, manager, hr, workflow_admin, student,
teacher. No codes are invented here.

Teacher access is NOT granted by the role code alone: the user's linked
``persons.Person`` must own the class group via ``ClassGroup.teacher``.
"""
from __future__ import annotations

from typing import Any

from django.db.models import Q
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request
from rest_framework.views import View

from apps.forms.models import FormSchema, FormSubmission

#: Institutional roles that may see every submission and every schema.
ELEVATED_ROLES = {"manager", "workflow_admin", "hr"}

#: Roles that may read internal comments: elevated staff + teachers.
#: Plain employees (ordinary submitters) and students/parents cannot.
INTERNAL_COMMENT_ROLES = ELEVATED_ROLES | {"teacher"}


def _person_of(user):
    return getattr(user, "person", None)


def visible_schemas_for(user) -> "FormSchema.objects":
    """Schemas whose allowed_roles intersect the user's roles (empty = public)."""
    qs = FormSchema.objects.filter(is_active=True)
    roles = user.role_codes()
    public = qs.filter(allowed_roles__isnull=True)
    restricted = qs.filter(allowed_roles__code__in=roles) if roles else qs.none()
    return (public | restricted).distinct()


def visible_submissions_for(user):
    """
    Submissions the user may see:

      - elevated roles → everything;
      - the submitter → own submissions (any status);
      - teacher → submissions scoped to class groups THEY teach
        (ClassGroup.teacher == their Person — role code alone is insufficient);
      - student → submissions about them (subject_person == their Person).
    """
    roles = user.role_codes()
    if roles & ELEVATED_ROLES:
        return FormSubmission.objects.all()

    condition = Q(submitted_by=user)

    person = _person_of(user)
    if person is not None:
        if "teacher" in roles:
            condition |= Q(class_group__teacher=person)
        if "student" in roles:
            condition |= Q(subject_person=person)

    return FormSubmission.objects.filter(condition).distinct()


def can_view_internal_comments(user) -> bool:
    return bool(user.role_codes() & INTERNAL_COMMENT_ROLES)


class CanAccessForms(BasePermission):
    """
    Coarse gate for the forms API: any authenticated active user may reach
    the endpoints; row-level scoping happens in get_queryset()/has_object.
    """

    message = "شما مجوز دسترسی به فرم‌ها را ندارید."

    def has_permission(self, request: Request, view: View) -> bool:
        user = request.user
        return bool(user and user.is_authenticated)

    def has_object_permission(self, request: Request, view: View, obj: Any) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if isinstance(obj, FormSchema):
            return visible_schemas_for(user).filter(pk=obj.pk).exists()

        if isinstance(obj, FormSubmission):
            if not visible_submissions_for(user).filter(pk=obj.pk).exists():
                return False
            # Writes are limited to the submitter; immutability of non-draft
            # submissions is enforced by the view (409) and the service.
            if request.method not in SAFE_METHODS:
                return obj.submitted_by_id == user.pk

        from apps.forms.models import FormAttachment, FormComment

        if isinstance(obj, (FormAttachment, FormComment)):
            return visible_submissions_for(user).filter(pk=obj.submission_id).exists()

        return False


class CanManageFormSchemas(BasePermission):
    """Schema administration (create/edit) is restricted to elevated roles."""

    message = "فقط مدیر یا مدیر فرآیند می‌تواند تعریف فرم را مدیریت کند."

    def has_permission(self, request: Request, view: View) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return bool(user.role_codes() & ELEVATED_ROLES)


# ── Spec-named aliases (PART 6) ──────────────────────────────────────────────
# The implementation uses a visibility-first design (queryset scoping +
# one object gate); these aliases expose the same gates under the names the
# specification uses so view code and reviews can reference either.

#: Schema list/detail access = authenticated + role-allowed schema.
FormSchemaPermission = CanAccessForms

#: Submission retrieve/update = visibility + submitter-only writes.
FormSubmissionObjectPermission = CanAccessForms

#: Attachment upload/download inherits submission visibility.
FormAttachmentPermission = CanAccessForms

#: Comment read/write inherits submission visibility.
FormCommentPermission = CanAccessForms
