"""
Notification inbox API — the user-facing side of the outbox (B6 closure).

  GET  /api/notifications/            — my in-app messages (newest first)
  GET  /api/notifications/?unread=1   — only unread
  POST /api/notifications/{id}/read/  — mark one as read (owner only)
  POST /api/notifications/read-all/   — mark everything as read (bulk)

Rows become *visible* here only after flush_notifications flips them to
`sent` (an unsent row is an artifact of delivery, not a message). Marking
read never touches `status` — delivery state and read receipt are separate.
"""
from __future__ import annotations

from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView

from apps.core.permissions import IsActiveUser
from apps.workflow.models import NotificationOutbox


class NotificationSerializer(serializers.ModelSerializer):
    recipient_username = serializers.SlugRelatedField(
        source="recipient", slug_field="username", read_only=True
    )
    instance_title = serializers.CharField(
        source="instance.title", read_only=True
    )
    created_at_jalali = serializers.CharField(read_only=True)

    class Meta:
        model = NotificationOutbox
        fields = (
            "id",
            "instance",
            "instance_title",
            "recipient_username",
            "channel",
            "template",
            "payload",
            "status",
            "is_read",
            "read_at",
            "sent_at",
            "created_at",
            "created_at_jalali",
        )
        read_only_fields = fields


class NotificationInboxView(ListAPIView):
    """GET /api/notifications/ — my in-app inbox (optionally unread only)."""

    permission_classes = (IsActiveUser,)
    serializer_class = NotificationSerializer

    def get_queryset(self):
        qs = (
            NotificationOutbox.objects.filter(
                recipient=self.request.user,
                channel=NotificationOutbox.Channel.IN_APP,
                status=NotificationOutbox.Status.SENT,
            )
            .select_related("instance", "recipient")
        )
        if self.request.query_params.get("unread") in ("1", "true"):
            qs = qs.filter(is_read=False)
        return qs.order_by("-created_at")


class NotificationReadView(APIView):
    """POST /api/notifications/{id}/read/ — owner marks one message read."""

    permission_classes = (IsActiveUser,)

    def post(self, request, pk):
        from django.shortcuts import get_object_or_404
        from django.utils import timezone

        row = get_object_or_404(
            NotificationOutbox,
            pk=pk,
            recipient=request.user,
            channel=NotificationOutbox.Channel.IN_APP,
        )
        if not row.is_read:
            row.is_read = True
            row.read_at = timezone.now()
            row.save(update_fields=["is_read", "read_at", "updated_at"])
        return Response(NotificationSerializer(row).data)


class NotificationReadAllView(APIView):
    """POST /api/notifications/read-all/ — bulk mark-read (one UPDATE)."""

    permission_classes = (IsActiveUser,)

    def post(self, request):
        from django.utils import timezone

        updated = (
            NotificationOutbox.objects.filter(
                recipient=request.user,
                channel=NotificationOutbox.Channel.IN_APP,
                status=NotificationOutbox.Status.SENT,
                is_read=False,
            )
            .update(is_read=True, read_at=timezone.now(), updated_at=timezone.now())
        )
        return Response({"marked_read": updated}, status=status.HTTP_200_OK)
