from __future__ import annotations

from uuid import UUID

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.shortcuts import get_object_or_404

from rest_framework import generics, serializers, status, views
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

from apps.core.group_permissions import HasGroupPermission, StrictDjangoModelPermissions
from apps.core.crud_views import SoftDeleteView, SoftRestoreView
from apps.core.permissions import IsActiveUser, IsWorkflowParticipant, ResourceCRUDPermission
from apps.reports.permissions import can_access_reports
from apps.reports.selectors.reports import ReportFilterError
from apps.reports.selectors.workflow import workflow_report_queryset
from apps.reports.serializers import WorkflowRequestReportSerializer
from apps.workflow.models import ActionLog, ApprovalRecord, Instance
from apps.workflow.serializers import (
    ActionLogSerializer,
    ApprovalRecordSerializer,
    CancelInstanceSerializer,
    CommentActionSerializer,
    CreateInstanceSerializer,
    DelegateSerializer,
    EntityWorkflowSerializer,
    ExecuteTransitionSerializer,
    InstanceDetailSerializer,
    InstanceListSerializer,
    LinkEntitySerializer,
    SendCopySerializer,
    TransitionSerializer,
)
from apps.workflow.services import (
    InvalidTransitionError,
    WorkflowEngineError,
    WorkflowEngineService,
)

engine = WorkflowEngineService()


def _visible_instances_for(user):
    roles = user.role_codes()
    if roles & {"manager", "workflow_admin", "hr"}:
        return Instance.objects.all()
    return Instance.objects.filter(
        models.Q(requester=user) | models.Q(tasks__assignee=user)
    )


class InstanceListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsActiveUser, StrictDjangoModelPermissions)

    def get_serializer_class(self):
        return CreateInstanceSerializer if self.request.method == "POST" else InstanceListSerializer

    def get_queryset(self):
        user = self.request.user
        roles = user.role_codes()
        qs = _visible_instances_for(user)
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
        return qs.select_related("workflow_definition", "current_state", "requester").distinct().order_by("-created_at")

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
        except WorkflowEngineError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        output = InstanceDetailSerializer(instance, context={"request": request})
        return Response(output.data, status=status.HTTP_201_CREATED)


class InstanceDetailView(generics.RetrieveAPIView):
    permission_classes = (IsActiveUser, IsWorkflowParticipant)
    serializer_class = InstanceDetailSerializer
    lookup_url_kwarg = "instance_id"

    def get_queryset(self):
        return _visible_instances_for(self.request.user).select_related(
            "workflow_definition", "current_state", "requester"
        ).distinct()


class InstanceSoftDeleteView(SoftDeleteView):
    resource_key = "requests"
    lookup_url_kwarg = "instance_id"

    def get_queryset(self):
        return _visible_instances_for(self.request.user).distinct()


class InstanceRestoreView(SoftRestoreView):
    queryset = Instance.all_objects.all()
    resource_key = "requests"
    lookup_url_kwarg = "instance_id"


class AvailableTransitionsView(views.APIView):
    permission_classes = (IsActiveUser, HasGroupPermission, IsWorkflowParticipant)
    required_permissions = {"GET": ["workflow.view_instance"]}

    def get(self, request, instance_id: UUID):
        instance = get_object_or_404(_visible_instances_for(request.user).distinct(), pk=instance_id)
        transitions = engine.get_available_transitions(instance, request.user)
        return Response(TransitionSerializer(transitions, many=True, context={"request": request}).data)


class ExecuteTransitionView(views.APIView):
    permission_classes = (IsActiveUser, HasGroupPermission, IsWorkflowParticipant)
    required_permissions = {"POST": ["workflow.change_instance"]}

    def post(self, request, instance_id: UUID):
        serializer = ExecuteTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not _visible_instances_for(request.user).filter(pk=instance_id).exists():
            return Response({"detail": "درخواست یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        try:
            instance = engine.execute_transition(
                instance_id=instance_id,
                transition_id=serializer.validated_data["transition_id"],
                actor=request.user,
                comment=serializer.validated_data.get("comment", ""),
                metadata=serializer.validated_data.get("metadata", {}),
                idempotency_key=serializer.validated_data.get("idempotency_key") or None,
            )
        except InvalidTransitionError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except WorkflowEngineError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(InstanceDetailSerializer(instance, context={"request": request}).data)


class CancelInstanceView(views.APIView):
    permission_classes = (IsActiveUser, HasGroupPermission, IsWorkflowParticipant)
    required_permissions = {"POST": ["workflow.change_instance"]}

    def post(self, request, instance_id: UUID):
        serializer = CancelInstanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not _visible_instances_for(request.user).filter(pk=instance_id).exists():
            return Response({"detail": "درخواست یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        try:
            instance = engine.cancel_instance(
                instance_id=instance_id,
                actor=request.user,
                reason=serializer.validated_data.get("reason", ""),
            )
        except WorkflowEngineError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(InstanceDetailSerializer(instance, context={"request": request}).data)


class LinkEntityView(views.APIView):
    permission_classes = (IsActiveUser, HasGroupPermission, IsWorkflowParticipant)
    required_permissions = {"POST": ["workflow.change_instance"]}

    def post(self, request, instance_id: UUID):
        serializer = LinkEntitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = get_object_or_404(_visible_instances_for(request.user).distinct(), pk=instance_id)
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
        except WorkflowEngineError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(EntityWorkflowSerializer(link, context={"request": request}).data, status=status.HTTP_201_CREATED)


class ActionLogListView(generics.ListAPIView):
    permission_classes = (IsActiveUser, HasGroupPermission)
    serializer_class = ActionLogSerializer
    required_permissions = {"GET": ["workflow.view_actionlog"]}

    def get_queryset(self):
        return ActionLog.objects.filter(
            instance_id__in=_visible_instances_for(self.request.user).values("id"),
            instance_id=self.kwargs["instance_id"],
        ).select_related("from_state", "to_state", "actor").order_by("-created_at")


class IsWorkflowReportViewer(BasePermission):
    message = "گزارش گردش‌کار فقط برای افراد مجاز در دسترس است."

    def has_permission(self, request, view):
        return can_access_reports(request.user)


class WorkflowReportView(generics.ListAPIView):
    """Paginated operational report over workflow instances and linked forms."""

    permission_classes = (IsActiveUser, IsWorkflowReportViewer)
    serializer_class = WorkflowRequestReportSerializer

    def get_queryset(self):
        try:
            return workflow_report_queryset(self.request.query_params, user=self.request.user)
        except ReportFilterError as exc:
            raise APIValidationError({"detail": str(exc)}) from exc


# ─────────────────────────────────────────────────────────────────────────────
# Semantic operations (B6) — named service paths over the engine; validation
# and authorization remain exclusively in the engine/validator layer.
# ─────────────────────────────────────────────────────────────────────────────

class _SemanticActionMixin:
    """Shared plumbing: visibility check + error mapping for named actions."""

    def _check_visible(self, request, instance_id) -> bool:
        return _visible_instances_for(request.user).filter(pk=instance_id).exists()

    def _run(self, request, instance_id, callable_):
        if not self._check_visible(request, instance_id):
            return Response({"detail": "درخواست یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        try:
            instance = callable_()
        except WorkflowEngineError as exc:
            # InvalidTransition covers permission-gaps; the rest are 400s.
            if isinstance(exc, InvalidTransitionError):
                return Response({"error": str(exc)}, status=status.HTTP_403_FORBIDDEN)
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            InstanceDetailSerializer(instance, context={"request": request}).data
        )


class ApproveInstanceView(_SemanticActionMixin, views.APIView):
    permission_classes = (IsActiveUser, HasGroupPermission, IsWorkflowParticipant)
    required_permissions = {"POST": ["workflow.change_instance"]}

    def post(self, request, instance_id: UUID):
        serializer = CommentActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._run(
            request, instance_id,
            lambda: engine.approve(
                instance_id, request.user,
                comment=serializer.validated_data.get("comment", ""),
                metadata=serializer.validated_data.get("metadata", {}),
    idempotency_key=serializer.validated_data.get("idempotency_key") or None,
            ),
        )


class RejectInstanceView(_SemanticActionMixin, views.APIView):
    permission_classes = (IsActiveUser, HasGroupPermission, IsWorkflowParticipant)
    required_permissions = {"POST": ["workflow.change_instance"]}

    def post(self, request, instance_id: UUID):
        serializer = CommentActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._run(
            request, instance_id,
            lambda: engine.reject(
                instance_id, request.user,
                comment=serializer.validated_data.get("comment", ""),
                metadata=serializer.validated_data.get("metadata", {}),
    idempotency_key=serializer.validated_data.get("idempotency_key") or None,
            ),
        )


class ReturnInstanceView(_SemanticActionMixin, views.APIView):
    permission_classes = (IsActiveUser, HasGroupPermission, IsWorkflowParticipant)
    required_permissions = {"POST": ["workflow.change_instance"]}

    def post(self, request, instance_id: UUID):
        serializer = CommentActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._run(
            request, instance_id,
            lambda: engine.return_to_previous(
                instance_id, request.user,
                comment=serializer.validated_data.get("comment", ""),
                metadata=serializer.validated_data.get("metadata", {}),
    idempotency_key=serializer.validated_data.get("idempotency_key") or None,
            ),
        )


class CompleteInstanceView(_SemanticActionMixin, views.APIView):
    permission_classes = (IsActiveUser, HasGroupPermission, IsWorkflowParticipant)
    required_permissions = {"POST": ["workflow.change_instance"]}

    def post(self, request, instance_id: UUID):
        serializer = CommentActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._run(
            request, instance_id,
            lambda: engine.complete(
                instance_id, request.user,
                comment=serializer.validated_data.get("comment", ""),
                metadata=serializer.validated_data.get("metadata", {}),
    idempotency_key=serializer.validated_data.get("idempotency_key") or None,
            ),
        )


class SendCopyView(_SemanticActionMixin, views.APIView):
    """POST — رونوشت برای کاربران دیگر (بدون ساختن تسک)."""

    permission_classes = (IsActiveUser, HasGroupPermission, IsWorkflowParticipant)
    required_permissions = {"POST": ["workflow.view_instance"]}

    def post(self, request, instance_id: UUID):
        serializer = SendCopySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not self._check_visible(request, instance_id):
            return Response({"detail": "درخواست یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        try:
            created = engine.send_copy(
                instance_id, request.user,
                recipient_ids=serializer.validated_data["recipient_ids"],
                note=serializer.validated_data.get("note", ""),
            )
        except WorkflowEngineError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"copies_created": created}, status=status.HTTP_200_OK)


class DelegateTaskView(_SemanticActionMixin, views.APIView):
    """POST — ارجاع تسک‌های فعلی کاربر به کاربر دیگر."""

    permission_classes = (IsActiveUser, HasGroupPermission, IsWorkflowParticipant)
    required_permissions = {"POST": ["workflow.change_instance"]}

    def post(self, request, instance_id: UUID):
        serializer = DelegateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not self._check_visible(request, instance_id):
            return Response({"detail": "درخواست یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        try:
            moved = engine.delegate(
                instance_id, request.user,
                serializer.validated_data["recipient"],
                comment=serializer.validated_data.get("comment", ""),
            )
        except InvalidTransitionError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except WorkflowEngineError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"tasks_delegated": moved}, status=status.HTTP_200_OK)


class ApprovalListView(generics.ListAPIView):
    """GET — رکوردهای تایید/رد یک Instance (مستقل از ActionLog)."""

    permission_classes = (IsActiveUser, HasGroupPermission)
    serializer_class = ApprovalRecordSerializer
    required_permissions = {"GET": ["workflow.view_instance"]}

    def get_queryset(self):
        return ApprovalRecord.objects.filter(
            instance_id__in=_visible_instances_for(self.request.user).values("id"),
            instance_id=self.kwargs["instance_id"],
        ).select_related("approver", "state", "transition").order_by("-created_at")
