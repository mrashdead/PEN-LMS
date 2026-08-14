from __future__ import annotations

from uuid import UUID

from django.db import models

from rest_framework import generics, permissions, status, views
from rest_framework.response import Response

from apps.workflow.models import ActionLog, Instance
from apps.workflow.serializers import (
    ActionLogSerializer,
    CancelInstanceSerializer,
    CreateInstanceSerializer,
    ExecuteTransitionSerializer,
    InstanceDetailSerializer,
    InstanceListSerializer,
    TransitionSerializer,
)
from apps.workflow.services import WorkflowEngineService, WorkflowEngineError

engine = WorkflowEngineService()


class InstanceListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/workflow/instances/   — list user's instances
    POST /api/workflow/instances/   — create a new instance
    """

    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateInstanceSerializer
        return InstanceListSerializer

    def get_queryset(self):
        user = self.request.user
        # User sees their own instances + instances where they have tasks
        return (
            Instance.objects.filter(
                models.Q(requester=user)
                | models.Q(tasks__assignee=user)
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
    GET /api/workflow/instances/{id}/ — detail of an instance
    """

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = InstanceDetailSerializer

    def get_queryset(self):
        user = self.request.user
        return Instance.objects.filter(
            models.Q(requester=user) | models.Q(tasks__assignee=user)
        ).select_related("workflow_definition", "current_state", "requester")


class AvailableTransitionsView(views.APIView):
    """
    GET /api/workflow/instances/{id}/available-transitions/
    """

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, instance_id: UUID):
        try:
            instance = Instance.objects.get(pk=instance_id)
        except Instance.DoesNotExist:
            return Response({"error": "Instance not found."}, status=status.HTTP_404_NOT_FOUND)

        transitions = engine.get_available_transitions(instance, request.user)
        serializer = TransitionSerializer(transitions, many=True, context={"request": request})
        return Response(serializer.data)


class ExecuteTransitionView(views.APIView):
    """
    POST /api/workflow/instances/{id}/execute-transition/
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
    POST /api/workflow/instances/{id}/cancel/
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


class ActionLogListView(generics.ListAPIView):
    """
    GET /api/workflow/instances/{id}/logs/ — action history for an instance
    """

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ActionLogSerializer

    def get_queryset(self):
        return ActionLog.objects.filter(
            instance_id=self.kwargs["instance_id"]
        ).select_related("from_state", "to_state", "actor").order_by("-created_at")
