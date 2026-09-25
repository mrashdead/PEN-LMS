"""Unified Request API.

These endpoints expose the product-level pipeline without breaking the older
``/api/forms/submissions/`` endpoints:

    RequestType -> Request -> WorkflowInstance -> Task -> Transition

The request object is backed by ``FormSubmission`` and therefore shares the
existing validation, visibility and workflow engine implementation.
"""
from __future__ import annotations

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsActiveUser
from apps.forms.models import FormSchema, Request
from apps.forms.permissions import (
    CanAccessForms,
    visible_request_types_for,
    visible_requests_for,
    visible_schemas_for,
)
from apps.forms.serializers import (
    RequestCreateSerializer,
    RequestDetailSerializer,
    RequestListSerializer,
    RequestTransitionSerializer,
    RequestTypeSerializer,
    RequestUpdateSerializer,
)
from apps.forms.services import (
    FormDataInvalid,
    FormServiceError,
    RequestService,
)
from apps.forms.throttles import FormWriteThrottle
from apps.workflow.services import WorkflowEngineError


request_service = RequestService()


class RequestTypeListView(generics.ListAPIView):
    """GET /api/forms/request-types/ — catalog for the unified request UI."""

    permission_classes = (IsActiveUser, CanAccessForms)
    serializer_class = RequestTypeSerializer

    def get_queryset(self):
        return visible_request_types_for(self.request.user).order_by("title", "code")


class RequestListCreateView(generics.ListCreateAPIView):
    """List visible requests or create a draft through a form schema."""

    permission_classes = (IsActiveUser, CanAccessForms)
    throttle_classes = (FormWriteThrottle,)

    def get_queryset(self):
        qs = visible_requests_for(self.request.user)
        params = self.request.query_params
        status_param = str(params.get("status") or "").strip().lower()
        if status_param:
            if status_param in {"running", "active"}:
                qs = qs.filter(form_submission__workflow_instance__status="running")
            else:
                qs = qs.filter(status=status_param)
        workflow_status = str(params.get("workflow_status") or "").strip().lower()
        if workflow_status:
            qs = qs.filter(form_submission__workflow_instance__status=workflow_status)
        request_type = str(params.get("request_type") or "").strip().lower()
        if request_type:
            qs = qs.filter(request_type__code=request_type)
        workflow_instance = str(params.get("workflow_instance") or "").strip()
        if workflow_instance:
            qs = qs.filter(form_submission__workflow_instance_id=workflow_instance)
        if str(params.get("mine") or "").lower() in {"1", "true", "yes"}:
            qs = qs.filter(requester=self.request.user)
        search = str(params.get("search") or params.get("q") or "").strip()
        if search:
            qs = qs.filter(
                Q(request_number__icontains=search)
                | Q(request_type__code__icontains=search)
                | Q(request_type__title__icontains=search)
                | Q(requester__username__icontains=search)
            )
        return qs.distinct().order_by("-last_action_at", "-created_at")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return RequestCreateSerializer
        return RequestListSerializer

    def create(self, request, *args, **kwargs):
        serializer = RequestCreateSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        schema = get_object_or_404(
            visible_schemas_for(request.user),
            slug=serializer.validated_data["schema_slug"],
        )
        try:
            business_request = request_service.create_draft(
                schema=schema,
                requester=request.user,
                data=serializer.validated_data.get("data") or {},
                request=request,
                notes=serializer.validated_data.get("notes", ""),
                idempotency_key=request.headers.get("Idempotency-Key") or None,
            )
        except FormDataInvalid as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
        except FormServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            RequestDetailSerializer(business_request, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class RequestDetailView(generics.RetrieveAPIView):
    permission_classes = (IsActiveUser, CanAccessForms)
    serializer_class = RequestDetailSerializer
    lookup_url_kwarg = "request_id"

    def get_queryset(self):
        return visible_requests_for(self.request.user)


class RequestUpdateView(APIView):
    """Edit a draft or a request returned for correction."""

    permission_classes = (IsActiveUser, CanAccessForms)
    throttle_classes = (FormWriteThrottle,)

    def patch(self, request, request_id):
        business_request = get_object_or_404(
            visible_requests_for(request.user), pk=request_id,
        )
        serializer = RequestUpdateSerializer(data=request.data or {}, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            business_request = request_service.update_data(
                business_request,
                actor=request.user,
                data=serializer.validated_data.get("data"),
                notes=serializer.validated_data.get("notes"),
                request=request,
            )
        except FormDataInvalid as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
        except FormServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            RequestDetailSerializer(business_request, context={"request": request}).data
        )


class RequestSubmitView(APIView):
    permission_classes = (IsActiveUser, CanAccessForms)
    throttle_classes = (FormWriteThrottle,)

    def post(self, request, request_id):
        business_request = get_object_or_404(
            visible_requests_for(request.user), pk=request_id,
        )
        if business_request.requester_id != request.user.pk:
            return Response({"detail": "فقط درخواست‌کننده می‌تواند درخواست را ارسال کند."}, status=403)
        try:
            business_request = request_service.submit(
                business_request,
                actor=request.user,
                request=request,
            )
        except FormDataInvalid as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
        except FormServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            RequestDetailSerializer(business_request, context={"request": request}).data
        )


class RequestTransitionView(APIView):
    permission_classes = (IsActiveUser, CanAccessForms)
    throttle_classes = (FormWriteThrottle,)

    def post(self, request, request_id):
        business_request = get_object_or_404(
            visible_requests_for(request.user), pk=request_id,
        )
        serializer = RequestTransitionSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        idempotency_key = payload.get("idempotency_key") or request.headers.get("Idempotency-Key")
        try:
            business_request = request_service.transition(
                business_request,
                actor=request.user,
                transition_id=payload["transition_id"],
                comment=payload.get("comment", ""),
                metadata=payload.get("metadata") or {},
                idempotency_key=idempotency_key or None,
            )
        except FormServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except WorkflowEngineError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            RequestDetailSerializer(business_request, context={"request": request}).data
        )


class RequestCancelView(APIView):
    permission_classes = (IsActiveUser, CanAccessForms)
    throttle_classes = (FormWriteThrottle,)

    def post(self, request, request_id):
        business_request = get_object_or_404(
            visible_requests_for(request.user), pk=request_id,
        )
        reason = str((request.data or {}).get("reason") or "")[:2000]
        try:
            business_request = request_service.cancel(
                business_request,
                actor=request.user,
                reason=reason,
            )
        except FormServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except WorkflowEngineError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            RequestDetailSerializer(business_request, context={"request": request}).data
        )


class MyWorkView(APIView):
    """A small unified inbox for requests and assigned workflow tasks."""

    permission_classes = (IsActiveUser, CanAccessForms)

    def get(self, request):
        from apps.tasks.models import WorkflowTask
        from apps.tasks.serializers import WorkflowTaskListSerializer

        requests_qs = visible_requests_for(request.user).filter(
            requester=request.user,
        ).order_by("-last_action_at", "-created_at")[:100]
        tasks_qs = WorkflowTask.objects.filter(
            assignee=request.user,
            status=WorkflowTask.Status.PENDING,
            is_deleted=False,
        ).select_related("instance", "instance__workflow_definition", "state").order_by(
            "due_date", "-created_at",
        )[:50]
        task_rows = WorkflowTaskListSerializer(
            tasks_qs, many=True, context={"request": request}
        ).data
        instance_ids = [row.get("instance_id") for row in task_rows if row.get("instance_id")]
        request_by_instance = {
            str(instance_id): str(request_id)
            for instance_id, request_id in Request.objects.filter(
                form_submission__workflow_instance_id__in=instance_ids,
                is_deleted=False,
            ).values_list("form_submission__workflow_instance_id", "id")
        }
        for row in task_rows:
            row["request_id"] = request_by_instance.get(str(row.get("instance_id")))

        return Response({
            "requests": RequestListSerializer(
                requests_qs, many=True, context={"request": request}
            ).data,
            "tasks": task_rows,
        })
