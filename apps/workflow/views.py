"""
Workflow API Views — نقطه ورود API برای گردش کار

تمامی Viewها:
  - نیاز به احراز هویت (IsAuthenticated)
  - خطاهای Business را با HTTP 400 برمی‌گردانند
  - از WorkflowEngineService برای منطق کسب‌وکار استفاده می‌کنند
"""
from __future__ import annotations

from uuid import UUID

from django.contrib.contenttypes.models import ContentType
from django.db import models

from rest_framework import generics, permissions, status, views
from rest_framework.response import Response

from apps.workflow.models import ActionLog, Instance
from apps.workflow.serializers import (
    ActionLogSerializer,
    CancelInstanceSerializer,
    CreateInstanceSerializer,
    EntityWorkflowSerializer,
    ExecuteTransitionSerializer,
    InstanceDetailSerializer,
    InstanceListSerializer,
    LinkEntitySerializer,
    TransitionSerializer,
)
from apps.workflow.services import WorkflowEngineService, WorkflowEngineError

# نمونه واحد از سرویس — برای استفاده در تمام Viewها
engine = WorkflowEngineService()


class InstanceListCreateView(generics.ListCreateAPIView):
    """
    GET    /api/workflow/instances/          — لیست درخواست‌های من
    POST   /api/workflow/instances/          — ایجاد درخواست جدید

    برای کاربر، Instanceهایی که خودش ایجاد کرده یا در آنها تسک دارد نمایش داده می‌شود.
    """

    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self):
        return (
            CreateInstanceSerializer if self.request.method == "POST"
            else InstanceListSerializer
        )

    def get_queryset(self):
        user = self.request.user
        return (
            Instance.objects.filter(
                models.Q(requester=user) | models.Q(tasks__assignee=user)
            )
            .select_related("workflow_definition", "current_state", "requester")
            .distinct()
            .order_by("-created_at")
        )

    def create(self, request, *args, **kwargs):
        serializer = CreateInstanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            instance = engine.create_instance(
                workflow_code=serializer.validated_data["workflow_code"],
                requester=request.user,
                title=serializer.validated_data["title"],
                description=serializer.validated_data.get("description", ""),
            )
        except WorkflowEngineError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        output = InstanceDetailSerializer(instance, context={"request": request})
        return Response(output.data, status=status.HTTP_201_CREATED)


class InstanceDetailView(generics.RetrieveAPIView):
    """
    GET /api/workflow/instances/{instance_id}/ — جزئیات یک درخواست
    """

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = InstanceDetailSerializer
    lookup_url_kwarg = "instance_id"  # مطابق با <uuid:instance_id> در URL

    def get_queryset(self):
        user = self.request.user
        return Instance.objects.filter(
            models.Q(requester=user) | models.Q(tasks__assignee=user)
        ).select_related("workflow_definition", "current_state", "requester")


class AvailableTransitionsView(views.APIView):
    """
    GET /api/workflow/instances/{instance_id}/available-transitions/
    — اقدامات مجاز فعلی برای کاربر در این درخواست
    """

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, instance_id: UUID):
        try:
            instance = Instance.objects.get(pk=instance_id)
        except Instance.DoesNotExist:
            return Response(
                {"error": "درخواست یافت نشد."},
                status=status.HTTP_404_NOT_FOUND,
            )

        transitions = engine.get_available_transitions(instance, request.user)
        serializer = TransitionSerializer(transitions, many=True, context={"request": request})
        return Response(serializer.data)


class ExecuteTransitionView(views.APIView):
    """
    POST /api/workflow/instances/{instance_id}/execute-transition/
    — اجرای یک اقدام (submit, approve, reject, ...)
    """

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, instance_id: UUID):
        serializer = ExecuteTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            instance = engine.execute_transition(
                instance_id=instance_id,
                transition_id=serializer.validated_data["transition_id"],
                actor=request.user,
                comment=serializer.validated_data.get("comment", ""),
                metadata=serializer.validated_data.get("metadata", {}),
            )
        except WorkflowEngineError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        output = InstanceDetailSerializer(instance, context={"request": request})
        return Response(output.data)


class CancelInstanceView(views.APIView):
    """
    POST /api/workflow/instances/{instance_id}/cancel/
    — لغو یک درخواست (فقط درخواست‌دهنده یا workflow_admin)
    """

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, instance_id: UUID):
        serializer = CancelInstanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            instance = engine.cancel_instance(
                instance_id=instance_id,
                actor=request.user,
                reason=serializer.validated_data.get("reason", ""),
            )
        except WorkflowEngineError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        output = InstanceDetailSerializer(instance, context={"request": request})
        return Response(output.data)


class LinkEntityView(views.APIView):
    """
    POST /api/workflow/instances/{instance_id}/link-entity/
    — اتصال یک موجودیت دامنه (CourseOffering, Lead, ...) به این Instance

    Body: {"entity_type": "education.courseoffering", "entity_id": "uuid"}
    """

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, instance_id: UUID):
        serializer = LinkEntitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        entity_type_str = serializer.validated_data["entity_type"]
        entity_id = serializer.validated_data["entity_id"]

        # تبدیل رشته به ContentType
        try:
            app_label, model_name = entity_type_str.strip().lower().split(".")
            ct = ContentType.objects.get(app_label=app_label, model=model_name)
        except (ValueError, ContentType.DoesNotExist):
            return Response(
                {"error": f"نوع موجودیت نامعتبر: '{entity_type_str}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # یافتن موجودیت
        try:
            entity = ct.get_object_for_this_type(pk=entity_id)
        except ct.model_class().DoesNotExist:  # type: ignore[union-attr]
            return Response(
                {"error": f"موجودیت '{entity_type_str}' با شناسه '{entity_id}' یافت نشد."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # اتصال از طریق سرویس
        try:
            link = engine.link_entity(instance_id=instance_id, entity=entity)
        except WorkflowEngineError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        output = EntityWorkflowSerializer(link, context={"request": request})
        return Response(output.data, status=status.HTTP_201_CREATED)


class ActionLogListView(generics.ListAPIView):
    """
    GET /api/workflow/instances/{instance_id}/logs/
    — تاریخچه اقدامات یک درخواست
    """

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ActionLogSerializer

    def get_queryset(self):
        return ActionLog.objects.filter(
            instance_id=self.kwargs["instance_id"]
        ).select_related("from_state", "to_state", "actor").order_by("-created_at")