from __future__ import annotations

from uuid import UUID

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.shortcuts import get_object_or_404

from rest_framework import generics, permissions, status, views
from rest_framework.response import Response

from apps.core.permissions import (
    CanManageWorkflow,
    IsActiveUser,
    IsWorkflowParticipant,
)
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

engine = WorkflowEngineService()


class InstanceListCreateView(generics.ListCreateAPIView):
    """List requests visible to actor; create a request for actor."""

    permission_classes = (IsActiveUser,)

    def get_serializer_class(self):
        return CreateInstanceSerializer if self.request.method == "POST" else InstanceListSerializer

    def get_queryset(self):
        user = self.request.user
        roles = user.role_codes()
        if roles & {"manager", "workflow_admin", "hr"}:
            qs = Instance.objects.all()
        else:
            qs = Instance.objects.filter(
                models.Q(requester=user) | models.Q(tasks__assignee=user)
            )

        workflow_code = self.request.query_params.get("workflow_code")
        if workflow_code:
            qs = qs.filter(workflow_definition__code=workflow_code)
        state = self.request.query_params.get("state")
        if state:
            qs = qs.filter(current_state__code=state)
        instance_status = self.request.query_params.get("status")
        if instance_status:
            qs = qs.filter(status=instance_status)
        requester = self.request.query_params.get("requester")
        if requester and roles & {"manager", "workflow_admin", "hr"}:
            qs = qs.filter(requester_id=requester)
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(models.Q(title__icontains=search) | models.Q(description__icontains=search))

        return (
            qs.select_related("workflow_definition", "current_state", "requester")
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
    permission_classes = (IsActiveUser, IsWorkflowParticipant)
    serializer_class = InstanceDetailSerializer
    lookup_url_kwarg = "instance_id"

    def get_queryset(self):
        user = self.request.user
        roles = user.role_codes()
        if roles & {"manager", "workflow_admin", "hr"}:
            qs = Instance.objects.all()
        else:
            qs = Instance.objects.filter(
                models.Q(requester=user) | models.Q(tasks__assignee=user)
            )
        return qs.select_related("workflow_definition", "current_state", "requester").distinct()


class AvailableTransitionsView(views.APIView):
    permission_classes = (IsActiveUser, IsWorkflowParticipant)

    def get(self, request, instance_id: UUID):
        user = request.user
        if user.role_codes() & {"manager", "workflow_admin", "hr"}:
            qs = Instance.objects.all()
        else:
            qs = Instance.objects.filter(models.Q(requester=user) | models.Q(tasks__assignee=user))
        instance = get_object_or_404(qs.distinct(), pk=instance_id)
        transitions = engine.get_available_transitions(instance, request.user)
        return Response(TransitionSerializer(transitions, many=True, context={"request": request}).data)


class ExecuteTransitionView(views.APIView):
    permission_classes = (IsActiveUser, IsWorkflowParticipant)

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
    permission_classes = (IsActiveUser, IsWorkflowParticipant)

    def post(self, request, instance_id: UUID):
        # Service performs the authoritative owner/workflow_admin check under lock.
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
    permission_classes = (IsActiveUser, IsWorkflowParticipant)

    def post(self, request, instance_id: UUID):
        serializer = LinkEntitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        elevated = bool(user.role_codes() & {"manager", "workflow_admin", "hr"})
        instance_qs = Instance.objects.all() if elevated else Instance.objects.filter(
            models.Q(requester=user) | models.Q(tasks__assignee=user)
        )
        instance = get_object_or_404(instance_qs.distinct(), pk=instance_id)

        entity_type_str = serializer.validated_data["entity_type"]
        entity_id = serializer.validated_data["entity_id"]
        try:
            app_label, model_name = entity_type_str.strip().lower().split(".", 1)
            ct = ContentType.objects.get(app_label=app_label, model=model_name)
        except (ValueError, ContentType.DoesNotExist):
            return Response({"error": f"نوع موجودیت نامعتبر: '{entity_type_str}'."}, status=status.HTTP_400_BAD_REQUEST)

        model_class = ct.model_class()
        if model_class is None:
            return Response({"error": "مدل موجودیت یافت نشد."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            entity = model_class._default_manager.get(pk=entity_id)
        except model_class.DoesNotExist:
            return Response({"error": f"موجودیت '{entity_type_str}' یافت نشد."}, status=status.HTTP_404_NOT_FOUND)

        try:
            link = engine.link_entity(instance_id=instance.id, entity=entity)
        except WorkflowEngineError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(EntityWorkflowSerializer(link, context={"request": request}).data, status=status.HTTP_201_CREATED)


class ActionLogListView(generics.ListAPIView):
    permission_classes = (IsActiveUser,)
    serializer_class = ActionLogSerializer

    def get_queryset(self):
        user = self.request.user
        roles = user.role_codes()
        instance_qs = Instance.objects.all() if roles & {"manager", "workflow_admin", "hr"} else Instance.objects.filter(
            models.Q(requester=user) | models.Q(tasks__assignee=user)
        )
        return ActionLog.objects.filter(
            instance_id__in=instance_qs.values("id"),
            instance_id=self.kwargs["instance_id"],
        ).select_related("from_state", "to_state", "actor").order_by("-created_at")
