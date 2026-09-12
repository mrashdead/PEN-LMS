"""
Internal messaging between staff (manager / hr / workflow_admin / employee /
teacher) — direct threads and an inbox with unread badges.

Design notes:
  * Thread = conversation between ≥2 users; Message = one entry in it.
  * ``Thread.participants`` (M2M through ThreadParticipant) carries the
    unread counter (``unread_count``) so the inbox is a single query —
    no COUNT(*) per thread, no JOIN-to-messages for badges.
  * Only active staff (has a live role) may be recipients — resolved from
    ``accounts.User.role_codes()`` at compose time (server-side allowlist).
  * Soft delete per-participant: hiding a thread only flips the viewer's
    own row (``is_hidden``), never other participants'.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.models import DomainModel


class Thread(DomainModel):
    """A conversation between staff members."""

    subject = models.CharField(max_length=200)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="threads_started",
    )
    # Convenience link to the workflow entity this thread is about (optional).
    # Messages are free-form staff chatter; this only enables deep-linking.
    workflow_instance = models.ForeignKey(
        "workflow.Instance",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="message_threads",
    )

    class Meta:
        app_label = "messaging"
        db_table = "messaging_thread"
        verbose_name = "Thread"
        verbose_name_plural = "Threads"
        ordering = ("-updated_at",)
        indexes = [
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self) -> str:
        return self.subject


class ThreadParticipant(models.Model):
    """Membership row: per-viewer hidden flag + unread counter."""

    thread = models.ForeignKey(
        Thread, on_delete=models.CASCADE, related_name="participants"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="message_threads",
    )
    unread_count = models.PositiveIntegerField(default=0, db_index=True)
    is_hidden = models.BooleanField(default=False, db_index=True)
    last_read_at = models.DateTimeField(null=True, blank=True)
    # Denormalized copy of DomainModel timestamps so participant queries
    # (inbox ordering) never join Thread.
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "messaging"
        db_table = "messaging_thread_participant"
        verbose_name = "Thread Participant"
        verbose_name_plural = "Thread Participants"
        constraints = [
            models.UniqueConstraint(
                fields=["thread", "user"], name="uniq_messaging_participant"
            )
        ]
        indexes = [
            models.Index(fields=["user", "is_hidden", "unread_count"]),
            models.Index(fields=["user", "is_hidden", "updated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.user_id} in {self.thread_id}"


class Message(DomainModel):
    """One message inside a thread. Append-only (no edit API)."""

    thread = models.ForeignKey(
        Thread, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="messages_sent",
    )
    body = models.TextField()

    class Meta:
        app_label = "messaging"
        db_table = "messaging_message"
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        ordering = ("created_at",)
        indexes = [
            models.Index(fields=["thread", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.sender_id}: {self.body[:30]}…"
