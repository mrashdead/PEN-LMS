"""Messaging domain services — the only place business rules live."""
from __future__ import annotations

from typing import Iterable

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F, Sum
from django.utils import timezone

from apps.messaging.models import Message, Thread, ThreadParticipant

User = get_user_model()

STAFF_ROLES = {"manager", "workflow_admin", "hr", "employee", "teacher"}
MAX_BODY_LENGTH = 5000
MAX_RECIPIENTS = 20


class MessagingError(Exception):
    """User-facing error; views map it to 400."""


def staff_directory():
    """Active users holding at least one staff role — compose allowlist.

    role_codes() is a per-user query (time-bound validity), so we scan the
    active set once; at school scale (hundreds) this is trivial. A denormalized
    flag on User is the upgrade path if this ever shows up in profiles.
    """
    ids = set()
    for user in User.objects.filter(is_active=True, is_deleted=False).only("pk").iterator():
        if user.role_codes() & STAFF_ROLES:
            ids.add(user.pk)
    return User.objects.filter(pk__in=ids).order_by("first_name", "last_name", "username")


@transaction.atomic
def start_thread(*, sender, recipient_ids: Iterable, subject: str, body: str) -> Thread:
    """Create a thread + first message; recipients get unread_count=1."""
    subject = (subject or "").strip()
    body = (body or "").strip()
    if not subject:
        raise MessagingError("موضوع پیام الزامی است.")
    if len(subject) > 200:
        raise MessagingError("موضوع حداکثر ۲۰۰ نویسه است.")
    if not body:
        raise MessagingError("متن پیام الزامی است.")
    if len(body) > MAX_BODY_LENGTH:
        raise MessagingError(f"متن پیام حداکثر {MAX_BODY_LENGTH} نویسه است.")

    wanted = {str(pk) for pk in recipient_ids if str(pk)}
    wanted.discard(str(sender.pk))
    if not wanted:
        raise MessagingError("حداقل یک گیرنده انتخاب کنید.")
    if len(wanted) > MAX_RECIPIENTS:
        raise MessagingError(f"حداکثر {MAX_RECIPIENTS} گیرنده مجاز است.")

    allowed = {str(pk) for pk in staff_directory().values_list("pk", flat=True)}
    if wanted - allowed:
        raise MessagingError("گیرنده(های) نامعتبر یا خارج از سازمان.")

    thread = Thread.objects.create(created_by=sender, subject=subject)
    ThreadParticipant.objects.bulk_create(
        [
            ThreadParticipant(
                thread=thread,
                user_id=pk,
                unread_count=(0 if pk == str(sender.pk) else 1),
            )
            for pk in [str(sender.pk), *wanted]
        ],
        batch_size=100,
    )
    Message.objects.create(thread=thread, sender=sender, body=body)
    return thread


@transaction.atomic
def reply(*, sender, thread_id, body: str) -> Message:
    body = (body or "").strip()
    if not body:
        raise MessagingError("متن پیام الزامی است.")
    if len(body) > MAX_BODY_LENGTH:
        raise MessagingError(f"متن پیام حداکثر {MAX_BODY_LENGTH} نویسه است.")

    thread = Thread.objects.filter(pk=thread_id).first()
    if thread is None:
        raise MessagingError("گفتگو یافت نشد.")
    if not ThreadParticipant.objects.filter(thread=thread, user=sender).exists():
        raise MessagingError("شما عضو این گفتگو نیستید.")

    message = Message.objects.create(thread=thread, sender=sender, body=body)
    now = timezone.now()
    # Replying implies the sender has seen the thread — clear their own badge.
    ThreadParticipant.objects.filter(thread=thread, user=sender).update(
        unread_count=0, last_read_at=now, updated_at=now
    )
    # bump every other participant's unread counter in ONE UPDATE
    ThreadParticipant.objects.filter(thread=thread).exclude(user=sender).update(
        unread_count=F("unread_count") + 1, updated_at=now
    )
    # keep thread ordering fresh (auto_now touches updated_at)
    thread.save(update_fields=["updated_at"])
    return message


@transaction.atomic
def mark_thread_read(*, user, thread_id) -> None:
    """Zero the viewer's unread counter and stamp last_read_at."""
    ThreadParticipant.objects.filter(thread_id=thread_id, user=user).update(
        unread_count=0, last_read_at=timezone.now(), updated_at=timezone.now()
    )


def my_threads(user):
    """Inbox rows: my visible threads, newest activity first."""
    return (
        ThreadParticipant.objects.filter(user=user, is_hidden=False)
        .select_related("thread", "thread__created_by")
        .order_by("-thread__updated_at")
    )


def total_unread(user) -> int:
    total = (
        ThreadParticipant.objects.filter(user=user, is_hidden=False).aggregate(
            total=Sum("unread_count")
        )["total"]
        or 0
    )
    return int(total)


def hide_thread(*, user, thread_id) -> bool:
    """Viewer-only hide (soft delete from MY inbox)."""
    return bool(
        ThreadParticipant.objects.filter(thread_id=thread_id, user=user).update(
            is_hidden=True
        )
    )
