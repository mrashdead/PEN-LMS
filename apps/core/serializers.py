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

    def save(self, **kwargs):
        creating = self.instance is None
        instance = super().save(**kwargs)
        request = self.context.get("request")
        actor = getattr(request, "user", None)
        if actor is not None and not getattr(actor, "is_authenticated", False):
            actor = None
        if getattr(actor, "is_authenticated", False) and getattr(instance, "pk", None):
            from apps.core.models import AuditEvent

            action = "create" if creating else "update"
            resource = self.context.get("resource_key") or resource_for(instance)
            AuditEvent.record(
                kind=AuditEvent.Kind.FIELD_CHANGE,
                summary=f"{'ایجاد' if creating else 'ویرایش'} {resource}",
                actor=actor,
                obj=instance,
                request=request,
                metadata={"action": action, "resource": resource},
            )
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        user = getattr(request, "user", None)
        params = getattr(request, "query_params", {})
        roles = set(user.role_codes()) if user and hasattr(user, "role_codes") else set()
        if params.get("include_history") in {"1", "true", "yes"} and getattr(instance, "created_at", None) is not None:
            from apps.core.models import AuditEvent
            from django.contrib.contenttypes.models import ContentType
            from apps.core.utils import jalali_datetime_str, persian_numbers

            content_type = ContentType.objects.get_for_model(instance, for_concrete_model=False)
            events = list(AuditEvent.objects.filter(
                content_type=content_type, object_id=str(instance.pk)
            ).select_related("actor").order_by("created_at", "pk"))
            changes = [e for e in events if e.kind == AuditEvent.Kind.FIELD_CHANGE]

            def actor_name(event):
                if event is None:
                    return "ثبت نشده"
                if event.actor is None:
                    return "ثبت نشده"
                return event.actor.get_full_name().strip() or event.actor.get_username()

            creation = next((e for e in changes if (e.metadata or {}).get("action") == "create"), None)
            latest_change = changes[-1] if changes else None
            data["created_at_display"] = persian_numbers(jalali_datetime_str(instance.created_at))
            data["updated_at_display"] = persian_numbers(jalali_datetime_str(instance.updated_at))
            data["created_by_name"] = actor_name(creation)
            data["updated_by_name"] = actor_name(latest_change)
            if getattr(user, "is_superuser", False) or roles & {"manager", "workflow_admin"}:
                data["audit_trail"] = [
                    {
                        "id": str(event.pk),
                        "kind": event.kind,
                        "summary": event.summary,
                        "metadata": event.metadata,
                        "actor": actor_name(event),
                        "created_at": event.created_at_jalali,
                    }
                    for event in events[-20:]
                ]
        return data
