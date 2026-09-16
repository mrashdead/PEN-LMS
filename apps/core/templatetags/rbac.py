from __future__ import annotations

from django import template

from apps.core.crud import can_create_resource, crud_actions

register = template.Library()


@register.simple_tag(takes_context=True)
def can_crud(context, action: str, resource: str, obj=None) -> bool:
    user = context.get("request").user if context.get("request") else None
    if action == "create":
        return can_create_resource(user, resource)
    return bool(crud_actions(user, obj, resource).get(action)) if obj is not None else False


@register.filter
def crud_action(obj, action: str) -> bool:
    user = getattr(obj, "_crud_user", None)
    return bool(crud_actions(user, obj).get(action)) if user else False
