"""
Internal messaging API (session auth, staff-only).

  GET    /api/messaging/                 → my inbox (threads + unread badges)
  GET    /api/messaging/unread-count/    → {count} for the notification badge
  GET    /api/messaging/directory/       → staff I can message
  POST   /api/messaging/threads/         → start a thread {recipients,subject,body}
  GET    /api/messaging/threads/{id}/    → thread detail + messages (marks read)
  POST   /api/messaging/threads/{id}/reply/ → {body}
  POST   /api/messaging/threads/{id}/read/  → mark read
  POST   /api/messaging/threads/{id}/hide/  → hide from my inbox
"""
from __future__ import annotations

from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsActiveUser
from apps.messaging import services
from apps.messaging.models import Thread
from apps.messaging.serializers import (
    DirectorySerializer,
    MessageSerializer,
    ParticipantSerializer,
    ThreadSerializer,
)


class StaffOnlyMixin:
    """Messaging is a staff workspace — students/parents get 403.

    Raised from initial() (inside DRF's dispatch try/except) so the engine
    renders a proper 403 Response; returning a bare Response from dispatch()
    skips content negotiation (.accepted_renderer unset → 500 at render).
    """

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        roles = set(request.user.role_codes()) if hasattr(request.user, "role_codes") else set()
        if not roles & services.STAFF_ROLES:
            raise PermissionDenied("پیام‌رسانی درون‌سازمانی فقط برای کارکنان فعال است.")


class InboxView(StaffOnlyMixin, ListAPIView):
    permission_classes = (IsActiveUser,)
    serializer_class = ThreadSerializer

    def get_queryset(self):
        return services.my_threads(self.request.user)


class UnreadCountView(StaffOnlyMixin, APIView):
    permission_classes = (IsActiveUser,)

    def get(self, request):
        return Response({"count": services.total_unread(request.user)})


class DirectoryView(StaffOnlyMixin, APIView):
    permission_classes = (IsActiveUser,)

    def get(self, request):
        users = services.staff_directory().exclude(pk=request.user.pk)
        data = [
            {
                "id": str(u.pk),
                "name": u.get_full_name() or u.username,
                "username": u.username,
                "job_title": u.job_title or "",
            }
            for u in users
        ]
        return Response(DirectorySerializer(data, many=True).data)


class ThreadCreateView(StaffOnlyMixin, APIView):
    permission_classes = (IsActiveUser,)

    def post(self, request):
        payload = request.data or {}
        recipients = payload.get("recipients") or []
        if isinstance(recipients, str):
            recipients = [recipients]
        try:
            thread = services.start_thread(
                sender=request.user,
                recipient_ids=recipients,
                subject=str(payload.get("subject") or ""),
                body=str(payload.get("body") or ""),
            )
        except services.MessagingError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {"id": str(thread.pk), "subject": thread.subject},
            status=status.HTTP_201_CREATED,
        )


class ThreadDetailView(StaffOnlyMixin, APIView):
    permission_classes = (IsActiveUser,)

    def get(self, request, pk):
        thread = Thread.objects.filter(pk=pk).first()
        if thread is None or not thread.participants.filter(user=request.user).exists():
            # 404 (not 403): don't leak thread existence to non-participants
            return Response({"detail": "یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        services.mark_thread_read(user=request.user, thread_id=thread.pk)
        messages = thread.messages.select_related("sender").all()
        return Response({
            "id": str(thread.pk),
            "subject": thread.subject,
            "participants": ParticipantSerializer(
                thread.participants.select_related("user"), many=True
            ).data,
            "messages": MessageSerializer(
                messages, many=True, context={"request": request}
            ).data,
        })


class ThreadReplyView(StaffOnlyMixin, APIView):
    permission_classes = (IsActiveUser,)

    def post(self, request, pk):
        try:
            services.reply(
                sender=request.user,
                thread_id=pk,
                body=str((request.data or {}).get("body") or ""),
            )
        except services.MessagingError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"ok": True})


class ThreadReadView(StaffOnlyMixin, APIView):
    permission_classes = (IsActiveUser,)

    def post(self, request, pk):
        services.mark_thread_read(user=request.user, thread_id=pk)
        return Response({"ok": True})


class ThreadHideView(StaffOnlyMixin, APIView):
    permission_classes = (IsActiveUser,)

    def post(self, request, pk):
        services.hide_thread(user=request.user, thread_id=pk)
        return Response({"ok": True})
