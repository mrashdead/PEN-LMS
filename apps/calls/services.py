"""
Inbound-call service layer — business rules for logging and follow-up.

The record is append-mostly: a call's core fields (caller, phone, subject)
are immutable after creation (they are a factual log), while the FOLLOW-UP
state is a small state machine whose every change writes an append-only
``CallFollowUpLog`` row. This mirrors the workflow engine's
ActionLog/ApprovalRecord philosophy: the history is the audit trail.
"""
from __future__ import annotations

import datetime as dt
import logging
from typing import Optional

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.calls.models import CallFollowUpLog, CallResult, FollowUpStatus, InboundCall

logger = logging.getLogger(__name__)

#: Roles that may log and follow up calls (the operator floor). Managers and
#: HR keep access for reporting; end-user roles (student/guardian) do not.
CALL_OPERATOR_ROLES = {"employee", "teacher", "supervisor", "manager", "workflow_admin", "hr"}

_PHONE_RE = RegexValidator(r"^[0-9+\-\s()]{3,20}$", "شماره تلفن معتبر نیست.")


class CallServiceError(Exception):
    """Base error for the calls service (maps to HTTP 400 at the API edge)."""


class InvalidTransitionError(CallServiceError):
    """انتقال وضعیت پیگیری مجاز نیست."""


def is_call_operator(user) -> bool:
    if user is None or not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    return bool(set(user.role_codes()) & CALL_OPERATOR_ROLES)


def _normalize_phone(value: str) -> str:
    """Store digits only — display keeps the original input shape."""
    return "".join(ch for ch in str(value or "") if ch.isdigit() or ch == "+")


@transaction.atomic
def log_call(*, actor, caller_name: str, caller_phone: str, called_at,
             subject: str, description: str = "", result: str = CallResult.ANSWERED,
             direction: str = InboundCall.Direction.INBOUND,
             department: str = "", department_ref=None,
             person=None, assignee=None, next_follow_up_at=None,
             subject_ref=None, follow_up_status: Optional[str] = None) -> InboundCall:
    """
    ثبت یک تماس. ``person`` فقط در صورتی وصل می‌شود که یک Person زنده با این
    شماره/نام وجود داشته باشد — هویت تکراری ساخته نمی‌شود.
    """
    if not is_call_operator(actor):
        raise CallServiceError("شما مجاز به ثبت تماس نیستید.")
    if not (caller_phone or "").strip():
        raise CallServiceError("شماره تماس الزامی است.")
    if not (subject or "").strip():
        raise CallServiceError("موضوع تماس الزامی است.")
    if called_at is None:
        called_at = timezone.now()
    if called_at > timezone.now():
        raise CallServiceError("زمان تماس نمی‌تواند در آینده باشد.")

    phone = _normalize_phone(caller_phone)
    if len(phone) < 3:
        raise CallServiceError("شماره تماس معتبر نیست.")

    # Resolve the follow-up state from the result when not given explicitly:
    # a call that ended with "call back later" needs follow-up by definition.
    if follow_up_status is None:
        follow_up_status = (
            FollowUpStatus.PENDING if result == CallResult.FOLLOW_UP_AGREED
            else FollowUpStatus.NONE
        )
    if next_follow_up_at and follow_up_status not in {FollowUpStatus.PENDING, FollowUpStatus.IN_PROGRESS}:
        raise CallServiceError(
            "تاریخ پیگیری فقط برای پیگیری‌های باز قابل ثبت است."
        )

    call = InboundCall(
        caller_name=(caller_name or "").strip(),
        caller_phone=phone,
        person=person,
        receiver=actor,
        direction=direction,
        called_at=called_at,
        subject=subject.strip(),
        description=(description or "").strip(),
        result=result,
        follow_up_status=follow_up_status,
        assignee=assignee or actor,
        next_follow_up_at=next_follow_up_at,
        department=(department or "").strip(),
        department_ref=department_ref,
        subject_ref=subject_ref,
    )
    try:
        call.full_clean()
    except ValidationError as exc:
        raise CallServiceError(str(exc)) from exc
    try:
        call.save()
    except IntegrityError as exc:  # pragma: no cover - constraint backstop
        raise CallServiceError(str(exc)) from exc
    return call


@transaction.atomic
def update_follow_up(*, call_id, actor, new_status: str, note: str = "",
                     next_follow_up_at=None, assignee=None) -> InboundCall:
    """
    تغییر وضعیت پیگیری — هر تغییر یک ردیف append-only می‌نویسد.

    قانون: تنها دریافت‌کننده، مسئول پیگیری یا کاربر ارتقائی می‌تواند وضعیت
    پیگیری را تغییر دهد.
    """
    if new_status not in dict(FollowUpStatus.choices):
        raise CallServiceError("وضعیت پیگیری نامعتبر است.")

    call = (
        InboundCall.objects.select_for_update()
        .filter(pk=call_id, is_deleted=False).first()
    )
    if call is None:
        raise CallServiceError("تماس یافت نشد.")

    if not _can_follow_up(actor, call):
        raise CallServiceError("شما مجاز به پیگیری این تماس نیستید.")

    previous = call.follow_up_status
    if previous == new_status and not note and next_follow_up_at is None and assignee is None:
        return call  # idempotent no-op

    if next_follow_up_at and new_status not in {FollowUpStatus.PENDING, FollowUpStatus.IN_PROGRESS}:
        raise InvalidTransitionError(
            "تاریخ پیگیری فقط برای پیگیری‌های باز قابل ثبت است."
        )

    call.follow_up_status = new_status
    if next_follow_up_at is not None:
        call.next_follow_up_at = next_follow_up_at or None
    if new_status in {FollowUpStatus.DONE, FollowUpStatus.MISSED, FollowUpStatus.NONE}:
        call.next_follow_up_at = None
    if assignee is not None:
        call.assignee = assignee
    if note:
        call.follow_up_note = note
    call.save(update_fields=[
        "follow_up_status", "next_follow_up_at", "assignee",
        "follow_up_note", "updated_at",
    ])

    CallFollowUpLog.objects.create(
        call=call,
        actor=actor,
        previous_status=previous,
        new_status=new_status,
        note=(note or "").strip(),
        next_follow_up_at=call.next_follow_up_at,
    )
    return call


def _can_follow_up(actor, call) -> bool:
    if is_call_operator(actor) and _is_elevated(actor):
        return True
    if call.receiver_id == getattr(actor, "pk", None):
        return True
    if call.assignee_id == getattr(actor, "pk", None):
        return True
    return False


def _is_elevated(user) -> bool:
    if user is None or not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    return bool(set(user.role_codes()) & {"manager", "workflow_admin", "hr", "supervisor"})


def calls_visible_to(user):
    """
    DataScope for the call log — mirrors apps.academics.scoping:

      elevated (manager/workflow_admin/hr/supervisor) → all calls;
      other operators → calls they received or are assigned to follow up.
    """
    qs = InboundCall.objects.select_related(
        "receiver", "assignee", "person", "department_ref", "related_lead",
        "subject_ref",
    )
    if user is None or not getattr(user, "is_authenticated", False):
        return qs.none()
    if _is_elevated(user):
        return qs
    from django.db.models import Q

    return qs.filter(Q(receiver=user) | Q(assignee=user))


__all__ = [
    "CALL_OPERATOR_ROLES",
    "CallServiceError",
    "InvalidTransitionError",
    "calls_visible_to",
    "is_call_operator",
    "log_call",
    "update_follow_up",
]
