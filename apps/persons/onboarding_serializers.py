"""Serializers for the dynamic onboarding API (apps.persons.onboarding)."""
from __future__ import annotations

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from apps.persons import hierarchy
from apps.persons.onboarding import FIELD_SPECS


class OnboardingCreateSerializer(serializers.Serializer):
    """
    The whole wizard payload in one document: step 1 (target) + step 2 (fields
    + optional guardians[]). Field-level requirements are enforced by the
    service via FIELD_SPECS.validate_target_fields — the SAME contract the
    schema endpoint hands the UI — so this serializer only checks the envelope
    and leaves room for HTMX partial payloads to add new targets without a
    code change in two places.
    """

    target = serializers.CharField()
    data = serializers.JSONField()

    def validate_target(self, value: str) -> str:
        value = (value or "").strip().lower()
        if value not in FIELD_SPECS:
            raise serializers.ValidationError(f"نوع نامعتبر: {value}")
        return value

    def validate_data(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("قالب داده باید شیء JSON باشد.")
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        actor = getattr(request, "user", None)
        if actor is not None and getattr(actor, "is_authenticated", False):
            roles = set(actor.role_codes()) if hasattr(actor, "role_codes") else set()
            if not hierarchy.can_create(
                roles, attrs["target"], is_superuser=bool(actor.is_superuser)
            ):
                # 403, not 400: the payload is well-formed — the ACTOR is the
                # problem. Same status the service guard uses (double layer).
                raise PermissionDenied(
                    {"target": "شما مجاز به ایجاد کاربر با این نوع/نقش نیستید."}
                )
        return attrs
