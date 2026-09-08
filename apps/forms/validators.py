"""
Public validation entry point matching the project spec:

    FormDataValidator(schema, user=None, request=None).validate(data, files=None)

Thin adapter over the pure engine in ``apps.forms.validation``:

  - returns CLEANED data (plain text sanitized, rich text run through the
    bleach allowlist — fail-closed when bleach is missing and the explicit
    fallback flag is off),
  - raises ``rest_framework.exceptions.ValidationError`` with field-keyed
    errors and ``non_field_errors`` for payload-level problems,
  - resolves relation targets exclusively through the server-side registry
    with the requesting user's object-level access applied.
"""
from __future__ import annotations

from typing import Any, Optional

from rest_framework.exceptions import ValidationError

from apps.forms.models import FormSchema
from apps.forms.sanitizers import (
    RichTextSanitizerUnavailable,
    sanitize_rich_text,
    sanitize_text,
)
from apps.forms.validation import FormDataValidator as _CoreValidator


class FormDataValidator:
    """Schema-bound, user-aware validator with a cleaned-data return."""

    def __init__(
        self,
        schema: FormSchema,
        user=None,
        request=None,
        *,
        fields: Optional[list[dict]] = None,
        existing_attachment_keys: Optional[set[str]] = None,
    ):
        self.schema = schema
        self.user = user
        self.request = request
        # ``fields`` overrides the live schema definition — used to validate
        # against a submission's immutable snapshot.
        self.fields = fields if fields is not None else (schema.fields or [])
        self.existing_attachment_keys = existing_attachment_keys or set()

    def validate(self, data: Any, files: Any = None) -> dict:
        """
        Validate and clean ``data``. Raises DRF ValidationError on failure.

        ``files`` (multipart) is accepted for API compatibility; uploads are
        stored through the dedicated attachment endpoint, so payload values
        must reference existing attachment ids.
        """
        core = _CoreValidator(
            self.fields,
            data,
            user=self.user,
            request=self.request,
            schema_slug=getattr(self.schema, "slug", ""),
            existing_attachment_keys=self.existing_attachment_keys,
        )
        errors = core.run()
        if not errors.ok:
            payload = errors.as_dict()
            # Map the payload-level bucket to DRF's conventional key.
            general = payload.pop("__all__", None)
            if general:
                payload["non_field_errors"] = general
            raise ValidationError(payload)

        cleaned = self._sanitize(dict(core.data))
        return cleaned

    # ── cleaning ──────────────────────────────────────────────────────────

    def _sanitize(self, data: dict) -> dict:
        for definition in self.fields:
            if not isinstance(definition, dict):
                continue
            key = definition.get("key")
            ftype = definition.get("type")
            if not key or key not in data:
                continue
            value = data[key]
            try:
                if ftype in {"text", "textarea"} and isinstance(value, str):
                    data[key] = sanitize_text(value)
                elif ftype == "rich_text" and isinstance(value, str):
                    data[key] = sanitize_rich_text(value)
                elif ftype == "select" and isinstance(value, str):
                    data[key] = sanitize_text(value)
                elif ftype == "multi_select" and isinstance(value, list):
                    data[key] = [sanitize_text(v) if isinstance(v, str) else v for v in value]
                elif ftype in {"attendance_table", "grade_table", "table"} and isinstance(value, list):
                    data[key] = [self._sanitize_row(row) for row in value]
            except RichTextSanitizerUnavailable as exc:
                raise ValidationError({
                    key: [str(exc)],
                }) from exc
        return data

    @staticmethod
    def _sanitize_row(row: Any) -> Any:
        if not isinstance(row, dict):
            return row
        cleaned = {}
        for cell_key, cell in row.items():
            cleaned[cell_key] = sanitize_text(cell) if isinstance(cell, str) else cell
        return cleaned
