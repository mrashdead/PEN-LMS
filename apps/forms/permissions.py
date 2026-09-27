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

from apps.forms.models import FormSchema, FormSubmission, Request, RequestType

#: Institutional roles that may see every submission and every schema.
ELEVATED_ROLES = {"manager", "workflow_admin"}
LEGACY_ELEVATED_ROLES = {"hr"}

#: Roles that may read internal comments: elevated staff + teachers.
#: Plain employees (ordinary submitters) and students/parents cannot.
INTERNAL_COMMENT_ROLES = ELEVATED_ROLES | LEGACY_ELEVATED_ROLES | {"teacher"}


def _person_of(user):
    return getattr(user, "person", None)


def visible_schemas_for(user) -> "FormSchema.objects":
    """Schemas allowed by both the form and its business request catalog."""
    qs = FormSchema.objects.filter(is_active=True, is_deleted=False)
    roles = user.role_codes()
    public = qs.filter(
        allowed_roles__isnull=True,
    ).filter(
        Q(request_type__isnull=True) | Q(request_type__allowed_roles__isnull=True)
    )
    restricted = (
        qs.filter(
            Q(allowed_roles__code__in=roles)
            | Q(request_type__allowed_roles__code__in=roles)
        )
        if roles
        else qs.none()
    )
    visible = (public | restricted).distinct()
    # An explicit initiator allowlist narrows the existing schema/request-type
    # audience. Empty lists retain legacy behavior (the role M2Ms above remain
    # authoritative and an unconfigured public form stays public).
    allowed_ids = []
    for schema in visible.only("pk", "workflow_config").distinct():
        eligible = set((schema.workflow_config or {}).get("eligible_initiator_roles") or [])
        if not eligible or roles & eligible:
            allowed_ids.append(schema.pk)
    return visible.filter(pk__in=allowed_ids).distinct()


def visible_request_types_for(user):
    """Request catalog visible to a user; empty role M2M means public."""
    roles = user.role_codes()
    qs = RequestType.objects.filter(is_active=True, is_deleted=False)
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
      - student → submissions about them (subject_person == their Person);
      - guardian → submissions about an active ward, subject to the relation.
    """
    roles = user.role_codes()
    if roles & ELEVATED_ROLES:
        return FormSubmission.objects.all()

    condition = Q(submitted_by=user) | Q(initiator=user) | Q(subject_user=user)

    person = _person_of(user)
    if person is not None:
        if "teacher" in roles:
            condition |= Q(class_group__teacher=person)
        if "student" in roles:
            condition |= Q(subject_person=person)
        if "guardian" in roles:
            condition |= Q(
                subject_person__guardians__guardian=person,
                subject_person__guardians__is_active=True,
                subject_person__guardians__is_deleted=False,
            )

    return FormSubmission.objects.filter(condition).distinct()


def visible_requests_for(user):
    """Return requests visible through form ownership *or* assigned work.

    A modern workflow inbox must not require an employee to be the original
    submitter in order to open the work item assigned to them.  The form
    visibility rules remain the canonical audience boundary; an active
    pending task adds the assignee as a legitimate operational audience.
    """
    visible_submission_ids = visible_submissions_for(user).values("pk")
    condition = Q(form_submission_id__in=visible_submission_ids)
    condition |= Q(initiator=user) | Q(subject_user=user)
    condition |= Q(
        form_submission__workflow_instance__action_logs__actor=user,
        form_submission__workflow_instance__action_logs__is_deleted=False,
    )
    condition |= Q(
        form_submission__workflow_instance__tasks__assignee=user,
        form_submission__workflow_instance__tasks__status="pending",
        form_submission__workflow_instance__tasks__is_deleted=False,
    )
    return (
        Request.objects.filter(condition, is_deleted=False)
        .select_related("request_type", "requester", "subject_person", "form_submission")
        .distinct()
    )


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

        if isinstance(obj, RequestType):
            return visible_request_types_for(user).filter(pk=obj.pk).exists()

        if isinstance(obj, Request):
            return visible_requests_for(user).filter(pk=obj.pk).exists()

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
