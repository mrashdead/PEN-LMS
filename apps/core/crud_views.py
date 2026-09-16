from __future__ import annotations

from rest_framework import generics, status
from rest_framework.response import Response

from apps.core.crud import restore_object, soft_delete_object
from apps.core.permissions import IsActiveUser, ResourceCRUDPermission


class SoftDeleteView(generics.GenericAPIView):
    """POST-only soft delete endpoint; physical DELETE is never required by UI."""

    permission_classes = (IsActiveUser, ResourceCRUDPermission)
    soft_delete_action = True
    resource_key = None

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        self.check_object_permissions(request, obj)
        soft_delete_object(obj, actor=request.user, request=request, resource=self.resource_key)
        return Response({"detail": "رکورد با موفقیت غیرفعال شد.", "id": str(obj.pk)})


class SoftRestoreView(generics.GenericAPIView):
    permission_classes = (IsActiveUser, ResourceCRUDPermission)
    restore_action = True
    resource_key = None

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        self.check_object_permissions(request, obj)
        restore_object(obj, actor=request.user, request=request, resource=self.resource_key)
        return Response({"detail": "رکورد بازیابی شد.", "id": str(obj.pk)})
