"""Domain actions executed after a workflow reaches a successful terminal step.

The workflow engine is intentionally generic: it changes state and records the
approval.  This module is the explicit bridge to business aggregates such as
education enrollment, so a workflow definition never imports an education
model directly and a form submission never silently mutates one.
"""
from __future__ import annotations

from typing import Any, Callable

from django.db import transaction


class DomainActionError(Exception):
    """A successful approval could not be applied to the target domain."""


def _payload(request) -> dict[str, Any]:
    submission = request.form_submission
    return dict(submission.data or {}) if submission is not None else {}


@transaction.atomic
def student_registration(*, business_request, actor, transition=None) -> dict[str, str]:
    """Create the financial registration and optionally final class membership.

    The action is idempotent through ``Request.metadata``.  A class group is
    optional because a student may be financially registered before the class
    is formed; when ``class_group`` is supplied, the same transaction creates
    the final ``ClassEnrollment`` and links both records.
    """
    from apps.education.models import CourseOffering, OfferingEnrollment
    from apps.education.services import (
        EducationServiceError,
        convert_offering_enrollment_to_class,
        create_offering_enrollment,
    )
    from apps.persons.models import Person
    from apps.academics.models import ClassGroup

    metadata = dict(business_request.metadata or {})
    previous = metadata.get("domain_action_result")
    if isinstance(previous, dict) and previous.get("action") == "student_registration":
        return previous

    data = _payload(business_request)
    offering_id = data.get("offering") or data.get("course_offering") or data.get("offering_id")
    student_id = data.get("student") or data.get("student_id") or business_request.subject_person_id
    class_group_id = data.get("class_group") or data.get("class_group_id")
    if not offering_id or not student_id:
        raise DomainActionError(
            "برای تکمیل ثبت‌نام، برگزاری دوره و دانش‌آموز باید در اطلاعات درخواست مشخص باشند."
        )

    offering = CourseOffering.objects.filter(pk=offering_id, is_deleted=False).first()
    student = Person.objects.filter(
        pk=student_id,
        person_type=Person.Type.STUDENT,
        is_active=True,
        is_deleted=False,
    ).first()
    if offering is None or student is None:
        raise DomainActionError("برگزاری دوره یا دانش‌آموز معتبر و فعال یافت نشد.")

    try:
        enrollment = create_offering_enrollment(
            offering=offering,
            student=student,
            actor=actor,
            course_amount=data.get("course_amount"),
            discount_type=data.get("discount_type", OfferingEnrollment.DiscountType.NONE),
            discount_value=data.get("discount_value", 0),
            payment_method=data.get("payment_method", OfferingEnrollment.PaymentMethod.CASH),
            cheque_count=data.get("cheque_count", 0),
            cheques=data.get("cheques") or [],
            reference=data.get("payment_reference") or data.get("reference") or "",
            lifecycle_status=OfferingEnrollment.LifecycleStatus.CONFIRMED,
        )
        membership = None
        if class_group_id:
            group = ClassGroup.objects.filter(pk=class_group_id, is_deleted=False).first()
            if group is None:
                raise DomainActionError("کلاس انتخاب‌شده برای عضویت یافت نشد.")
            membership = convert_offering_enrollment_to_class(
                enrollment=enrollment,
                class_group=group,
                actor=actor,
            )
    except EducationServiceError as exc:
        raise DomainActionError(str(exc)) from exc

    result = {
        "action": "student_registration",
        "offering_enrollment_id": str(enrollment.pk),
        "student_id": str(student.pk),
    }
    if membership is not None:
        result["class_enrollment_id"] = str(membership.pk)
    metadata["domain_action_result"] = result
    # Store a JSON-safe timestamp through the normal timezone utility rather
    # than keeping a model-level event table for this first domain action.
    from django.utils import timezone

    metadata["domain_action_executed_at"] = timezone.now().isoformat()
    business_request.metadata = metadata
    business_request.save(update_fields=["metadata", "updated_at"])
    return result


ACTION_REGISTRY: dict[str, Callable[..., dict[str, str]]] = {
    "student_registration": student_registration,
    "student-registration": student_registration,
}


def execute_domain_action(*, business_request, actor, transition=None) -> dict[str, str] | None:
    """Resolve and execute the action declared by the request type metadata."""
    metadata = business_request.request_type.metadata or {}
    action_code = metadata.get("domain_action")
    if not action_code and business_request.form_submission is not None:
        action_code = (business_request.form_submission.form_schema.metadata or {}).get("domain_action")
    if not action_code:
        return None
    handler = ACTION_REGISTRY.get(str(action_code).strip().lower())
    if handler is None:
        raise DomainActionError(f"عملیات دامنهٔ ناشناخته: {action_code}")
    return handler(business_request=business_request, actor=actor, transition=transition)
