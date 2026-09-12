"""DRF serializers for internal messaging."""
from __future__ import annotations

from rest_framework import serializers

from apps.core.fields import PersianCharField
from apps.messaging.models import Message, Thread, ThreadParticipant


class ParticipantSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="user.get_full_name", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = ThreadParticipant
        fields = ("name", "username", "unread_count")


class ThreadSerializer(serializers.ModelSerializer):
    """Inbox row — one participant's view of a thread."""

    unread_count = serializers.IntegerField(read_only=True)
    created_by_name = serializers.CharField(
        source="thread.created_by.get_full_name", read_only=True
    )
    subject = serializers.CharField(source="thread.subject", read_only=True)
    thread_id = serializers.CharField(source="thread.id", read_only=True)
    updated_at = PersianCharField(source="thread.updated_at_jalali", read_only=True)

    class Meta:
        model = ThreadParticipant
        fields = (
            "thread_id",
            "subject",
            "unread_count",
            "created_by_name",
            "updated_at",
        )
        read_only_fields = fields


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.get_full_name", read_only=True)
    sender_username = serializers.CharField(source="sender.username", read_only=True)
    created_at = PersianCharField(source="created_at_jalali", read_only=True)
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = (
            "id",
            "sender",
            "sender_name",
            "sender_username",
            "body",
            "is_mine",
            "created_at",
        )
        read_only_fields = fields

    def get_is_mine(self, obj) -> bool:
        return obj.sender_id == self.context["request"].user.pk


class DirectorySerializer(serializers.Serializer):
    """Compose-directory entry (staff only)."""

    id = serializers.CharField()
    name = serializers.CharField()
    username = serializers.CharField()
    job_title = serializers.CharField()
