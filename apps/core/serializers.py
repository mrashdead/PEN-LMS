from __future__ import annotations

from rest_framework import serializers

from apps.core.crud import crud_actions, resource_for


class CRUDActionsMixin:
    """Expose server-authoritative row actions to every list/detail client."""

    actions = serializers.SerializerMethodField()

    def get_actions(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        return crud_actions(user, obj, self.context.get("resource_key") or resource_for(obj))

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        user = getattr(request, "user", None)
        params = getattr(request, "query_params", {})
        roles = set(user.role_codes()) if user and hasattr(user, "role_codes") else set()
        if params.get("include_history") in {"1", "true", "yes"} and (
            getattr(user, "is_superuser", False) or roles & {"manager", "workflow_admin"}
        ):
            from apps.core.models import AuditEvent
            from django.contrib.contenttypes.models import ContentType

            content_type = ContentType.objects.get_for_model(instance, for_concrete_model=False)
            data["audit_trail"] = [
                {
                    "id": str(event.pk),
                    "kind": event.kind,
                    "summary": event.summary,
                    "metadata": event.metadata,
                    "actor": getattr(event.actor, "username", None),
                    "created_at": event.created_at_jalali,
                }
                for event in AuditEvent.objects.filter(
                    content_type=content_type, object_id=str(instance.pk)
                ).select_related("actor")[:20]
            ]
        return data
