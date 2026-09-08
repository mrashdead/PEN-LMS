"""
Dynamic submission-data validation.

``FormDataValidator`` is the single server-side authority for what a client may
put into ``FormSubmission.data``. It receives:

  - the effective field definitions (the submission's immutable snapshot),
  - the submitted payload,
  - the authenticated user (for relation object-level access),
  - an optional request (for audit context).

Design rules:
  - Errors are keyed by field key and are safe to show to the client.
    Authorization failures never reveal whether the target exists — they read
    as "not available to you".
  - Unknown keys are rejected (no silent extra data).
  - Conditional visibility/requirement uses the declarative allowlist in
    ``schema_validation.evaluate_condition`` — never eval/exec.
  - Relations resolve ONLY through the fixed registry in ``relations.py``.
"""
from __future__ import annotations

import datetime
import decimal
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from django.conf import settings
from django.core.exceptions import FieldError
from django.core.exceptions import ValidationError as DjangoValidationError

from apps.core.utils import english_numbers
from apps.forms import relations
from apps.forms.relations import (
    MissingRequiredRelation,
    UnknownRelationKey,
)
from apps.forms.schema_validation import (
    ATTENDANCE_STATUSES_DEFAULT,
    evaluate_condition,
)

#: Hard ceiling on payload size (bytes when serialized) — guards against
#: unbounded JSON blobs regardless of per-field limits.
MAX_PAYLOAD_BYTES = 1_000_000

_TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})(?::(\d{2}))?$")
_DATE_RE = re.compile(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}$")
_DATETIME_RE = re.compile(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}[T ]\d{1,2}:\d{2}(:\d{2})?(\.\d+)?")

#: Extension → acceptable detected MIME types (content must agree with name).
EXTENSION_MIME_CONTRACT: dict[str, set[str]] = {
    ".pdf": {"application/pdf"},
    ".png": {"image/png"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".gif": {"image/gif"},
    ".webp": {"image/webp"},
    ".txt": {"text/plain"},
    ".csv": {"text/csv", "text/plain", "application/csv"},
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",
    },
    ".xlsx": {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/zip",
    },
    ".pptx": {
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/zip",
    },
    ".zip": {"application/zip", "application/x-zip-compressed"},
}

#: Never accepted regardless of configuration.
FORBIDDEN_MIME_TYPES = {
    "application/x-executable",
    "application/x-dosexec",
    "application/x-msdownload",
    "application/x-sh",
    "application/x-bash",
    "application/x-elf",
    "application/x-sharedlib",
    "application/x-python-code",
    "text/x-python",
    "application/x-php",
    "inode/x-empty",
}

DEFAULT_ALLOWED_EXTENSIONS = set(EXTENSION_MIME_CONTRACT)


@dataclass
class FieldErrors:
    """Accumulates per-field-key error messages."""

    errors: dict[str, list[str]] = field(default_factory=dict)

    def add(self, key: str, message: str) -> None:
        self.errors.setdefault(key, []).append(message)

    @property
    def ok(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, list[str]]:
        # Payload-level problems surface under DRF's conventional key.
        out = dict(self.errors)
        general = out.pop("__all__", None)
        if general:
            out["non_field_errors"] = general
        return out


class FormDataInvalid(DjangoValidationError):
    """Raised by services when dynamic data fails validation."""

    def __init__(self, errors: dict[str, list[str]]):
        self.detail = errors
        super().__init__(errors)


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip()) or value == []


def _as_number(value: Any) -> Optional[decimal.Decimal]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, decimal.Decimal, float)):
        try:
            return decimal.Decimal(str(value))
        except decimal.InvalidOperation:
            return None
    if isinstance(value, str):
        text = english_numbers(value).strip().replace(",", "")
        try:
            return decimal.Decimal(text)
        except decimal.InvalidOperation:
            return None
    return None


def _parse_date(value: Any) -> Optional[datetime.date]:
    """Accept ISO Gregorian or Jalali YYYY/MM/DD (project convention)."""
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    if not isinstance(value, str):
        return None
    text = english_numbers(value).strip()
    if not _DATE_RE.match(text):
        return None
    normalized = text.replace("/", "-")
    try:
        return datetime.date.fromisoformat(normalized)
    except ValueError:
        return None


def _parse_datetime(value: Any) -> Optional[datetime.datetime]:
    if isinstance(value, datetime.datetime):
        return value
    if not isinstance(value, str):
        return None
    text = english_numbers(value).strip()
    if not _DATETIME_RE.match(text):
        return None
    candidate = text.replace("/", "-")
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        return datetime.datetime.fromisoformat(candidate)
    except ValueError:
        # Fall back to a space-separated form.
        try:
            return datetime.datetime.fromisoformat(candidate.replace(" ", "T"))
        except ValueError:
            return None


def _parse_time(value: Any) -> Optional[datetime.time]:
    if isinstance(value, datetime.time):
        return value
    if not isinstance(value, str):
        return None
    match = _TIME_RE.match(english_numbers(value).strip())
    if not match:
        return None
    hour, minute, second = match.group(1), match.group(2), match.group(3) or "0"
    try:
        return datetime.time(int(hour), int(minute), int(second))
    except ValueError:
        return None


class FormDataValidator:
    """
    Validate ``data`` against a list of field definitions.

    Usage::

        result = FormDataValidator(fields, data, user=user).run()
        if not result.ok:
            raise FormDataInvalid(result.errors)
    """

    def __init__(
        self,
        fields: list[dict],
        data: Any,
        user=None,
        request=None,
        *,
        schema_slug: str = "",
        existing_attachment_keys: Optional[set[str]] = None,
    ):
        self.fields = fields or []
        self.data = data if isinstance(data, dict) else {}
        self.user = user
        self.request = request
        self.schema_slug = schema_slug
        self.existing_attachment_keys = existing_attachment_keys or set()
        self.errors = FieldErrors()

    # ── public API ────────────────────────────────────────────────────────

    @staticmethod
    def _validators_of(definition: dict) -> dict:
        """Merge the spec's nested ``validators`` block into the definition."""
        nested = definition.get("validators")
        if not isinstance(nested, dict):
            return definition
        merged = dict(definition)
        if "min_length" not in merged and "min_length" in nested:
            merged["min_length"] = nested["min_length"]
        if "max_length" not in merged and "max_length" in nested:
            merged["max_length"] = nested["max_length"]
        if "min" not in merged and "min_value" in nested:
            merged["min"] = nested["min_value"]
        if "max" not in merged and "max_value" in nested:
            merged["max"] = nested["max_value"]
        if "pattern" not in merged and "regex" in nested:
            merged["pattern"] = nested["regex"]
        if "accept" not in merged and "allowed_extensions" in nested:
            merged["accept"] = [
                ext if str(ext).startswith(".") else f".{ext}"
                for ext in nested["allowed_extensions"]
            ]
        if "mime_types" not in merged and "allowed_mime_types" in nested:
            merged["mime_types"] = nested["allowed_mime_types"]
        return merged

    def run(self, require_all: bool = True) -> FieldErrors:
        """
        Validate the payload.

        ``require_all=False`` (draft mode) enforces structure/type/permission
        rules but allows empty required fields — a draft may be incomplete.
        ``require_all=True`` (submit mode) additionally enforces every
        required field. Hidden-by-condition fields must stay empty either way.
        """
        if not isinstance(self.data, dict):
            self.errors.add("__all__", "payload must be a JSON object.")
            return self.errors

        import json

        try:
            size = len(json.dumps(self.data, ensure_ascii=False).encode("utf-8"))
        except (TypeError, ValueError):
            self.errors.add("__all__", "payload is not valid JSON.")
            return self.errors
        if size > MAX_PAYLOAD_BYTES:
            self.errors.add(
                "__all__",
                f"payload exceeds the {MAX_PAYLOAD_BYTES // 1000} KB limit.",
            )
            return self.errors

        known = {f.get("key") for f in self.fields if isinstance(f, dict)}
        for key in self.data:
            if key not in known:
                self.errors.add(str(key), "unknown field.")

        for definition in self.fields:
            if not isinstance(definition, dict):
                continue
            key = definition.get("key")
            if not key:
                continue
            definition = self._validators_of(definition)
            visible = self._is_visible(definition)
            raw = self.data.get(key, None)

            if not visible:
                # Hidden fields must not carry data (prevents bypassing UI).
                if raw is not None and not _is_blank(raw):
                    self.errors.add(key, "this field is not applicable and must be empty.")
                continue

            if not require_all:
                # Draft mode: structure/type/permission rules still apply,
                # but empty required fields are allowed.
                definition = {**definition, "required": False}

            if self._check_required(key, definition, raw):
                continue

            try:
                self._dispatch(key, definition, raw)
            except MissingRequiredRelation as exc:
                # A required relation target vanished after seeding: surface a
                # field-level error, never a stack trace to the client.
                self.errors.add(key, str(exc))
            except UnknownRelationKey:
                self.errors.add(key, "unsupported field configuration.")

        return self.errors

    # ── visibility / requirement ──────────────────────────────────────────

    def _is_visible(self, definition: dict) -> bool:
        conditional = definition.get("conditional")
        if not conditional:
            return True
        try:
            return evaluate_condition(conditional, self.data)
        except Exception:  # pragma: no cover - defensive; conditions are validated
            return False

    def _check_required(self, key: str, definition: dict, raw: Any) -> bool:
        """Return True when the field was handled (no further validation needed)."""
        # Visibility already decided by the caller: a conditionally-required
        # field is required only while visible.
        if bool(definition.get("required", False)) and _is_blank(raw):
            self.errors.add(key, "این فیلد الزامی است.")
            return True
        if _is_blank(raw):
            # Optional and empty → nothing further to validate.
            return True
        return False

    # ── dispatch ──────────────────────────────────────────────────────────

    def _dispatch(self, key: str, definition: dict, raw: Any) -> None:
        ftype = definition.get("type")
        handler = getattr(self, f"_validate_{ftype}", None)
        if handler is None:  # unsupported type at runtime → fail closed
            self.errors.add(key, "unsupported field type.")
            return
        handler(key, definition, raw)

    # ── scalars ───────────────────────────────────────────────────────────

    def _validate_text(self, key, definition, raw):
        self._validate_string(key, definition, raw)

    def _validate_textarea(self, key, definition, raw):
        self._validate_string(key, definition, raw, multiline=True)

    def _validate_string(self, key, definition, raw, multiline: bool = False):
        if not isinstance(raw, str):
            self.errors.add(key, "must be text.")
            return
        length = len(raw)
        min_length = definition.get("min_length")
        max_length = definition.get("max_length", 5000 if not multiline else 20000)
        if min_length is not None and length < min_length:
            self.errors.add(key, f"must be at least {min_length} characters.")
        if max_length is not None and length > max_length:
            self.errors.add(key, f"must be at most {max_length} characters.")
        pattern = definition.get("pattern")
        if pattern:
            try:
                if not re.search(pattern, raw):
                    self.errors.add(key, "value does not match the required format.")
            except re.error:  # pragma: no cover - schema validation blocks this
                self.errors.add(key, "value could not be checked against the format.")

    def _validate_rich_text(self, key, definition, raw):
        if not isinstance(raw, str):
            self.errors.add(key, "must be text.")
            return
        max_length = definition.get("max_length", 50000)
        if len(raw) > max_length:
            self.errors.add(key, f"must be at most {max_length} characters.")
        # Sanitization happens on write (services); here we only bound the size.

    def _validate_number(self, key, definition, raw):
        self._validate_numeric(key, definition, raw, integer=False)

    def _validate_integer(self, key, definition, raw):
        self._validate_numeric(key, definition, raw, integer=True)

    def _validate_decimal(self, key, definition, raw):
        self._validate_numeric(key, definition, raw, integer=False)

    def _validate_numeric(self, key, definition, raw, integer: bool):
        number = _as_number(raw)
        if number is None:
            self.errors.add(key, "must be a number.")
            return
        if integer and number != number.to_integral_value():
            self.errors.add(key, "must be a whole number.")
            return
        minimum = definition.get("min")
        maximum = definition.get("max")
        if minimum is not None and number < decimal.Decimal(str(minimum)):
            self.errors.add(key, f"must be at least {minimum}.")
        if maximum is not None and number > decimal.Decimal(str(maximum)):
            self.errors.add(key, f"must be at most {maximum}.")
        decimals = definition.get("decimals")
        if decimals is not None and -number.as_tuple().exponent > decimals:
            self.errors.add(key, f"may have at most {decimals} decimal places.")

    def _validate_boolean(self, key, definition, raw):
        if not isinstance(raw, bool):
            self.errors.add(key, "must be true or false.")

    def _validate_date(self, key, definition, raw):
        parsed = _parse_date(raw)
        if parsed is None:
            self.errors.add(key, "invalid date (use YYYY/MM/DD).")
            return
        self._check_date_bounds(key, definition, parsed)
        self._validate_date_cross(key, definition, raw)

    def _validate_datetime(self, key, definition, raw):
        parsed = _parse_datetime(raw)
        if parsed is None:
            self.errors.add(key, "invalid date and time (use YYYY/MM/DD HH:MM).")
            return
        self._check_date_bounds(key, definition, parsed.date())
        self._validate_date_cross(key, definition, raw)

    def _check_date_bounds(self, key, definition, day: datetime.date) -> None:
        min_raw, max_raw = definition.get("min"), definition.get("max")
        minimum = _parse_date(min_raw) if min_raw is not None else None
        maximum = _parse_date(max_raw) if max_raw is not None else None
        if minimum and day < minimum:
            self.errors.add(key, f"date must be on or after {minimum.isoformat()}.")
        if maximum and day > maximum:
            self.errors.add(key, f"date must be on or before {maximum.isoformat()}.")

    def _validate_time(self, key, definition, raw):
        parsed = _parse_time(raw)
        if parsed is None:
            self.errors.add(key, "invalid time (use HH:MM).")
            return
        # Declarative cross-field rule: this time must be after another time field.
        after_key = definition.get("after")
        if after_key:
            earlier = _parse_time(self.data.get(after_key))
            if earlier is not None and parsed <= earlier:
                self.errors.add(key, "time must be later than the referenced field.")

    def _validate_date_cross(self, key, definition, raw):
        after_key = definition.get("after")
        if not after_key:
            return
        earlier = _parse_date(self.data.get(after_key))
        day = _parse_date(raw)
        if earlier and day and day < earlier:
            self.errors.add(key, "date must be on or after the referenced field.")

    def _validate_select(self, key, definition, raw):
        allowed = {str(o.get("value")) for o in definition.get("options", []) if isinstance(o, dict)}
        if str(raw) not in allowed:
            self.errors.add(key, "value is not one of the allowed options.")

    def _validate_multi_select(self, key, definition, raw):
        if not isinstance(raw, list):
            self.errors.add(key, "must be a list.")
            return
        allowed = {str(o.get("value")) for o in definition.get("options", []) if isinstance(o, dict)}
        bad = [str(v) for v in raw if str(v) not in allowed]
        if bad:
            self.errors.add(key, "contains values that are not allowed options.")
        if len({str(v) for v in raw}) != len(raw):
            self.errors.add(key, "contains duplicate values.")

    # ── relations ─────────────────────────────────────────────────────────

    def _validate_relation(self, key, definition, raw):
        self._relation(key, definition, raw, multiple=False)

    def _validate_multi_relation(self, key, definition, raw):
        self._relation(key, definition, raw, multiple=True)

    def _relation(self, key, definition, raw, multiple: bool):
        relation = definition.get("relation") or {}
        registry_key = relation.get("registry_key")
        spec = relations.resolve(registry_key)  # raises UnknownRelationKey

        if not spec.is_available():
            if spec.optional and spec.fallback:
                # Declared fallback: accept the raw value as its fallback type,
                # and never pretend relation validation ran.
                self._relation_fallback(key, spec, raw)
                return
            raise MissingRequiredRelation(
                spec.key, spec.model_label, [self.schema_slug] if self.schema_slug else []
            )

        values = raw if multiple else [raw]
        if multiple and not isinstance(raw, list):
            self.errors.add(key, "must be a list.")
            return
        if multiple and not values and definition.get("required"):
            self.errors.add(key, "این فیلد الزامی است.")
            return

        lookup = relation.get("lookup", "id")
        if lookup not in spec.allowed_lookup_fields:
            self.errors.add(key, "unsupported lookup for this relation.")
            return

        collected: list[Any] = []
        for value in values:
            if _is_blank(value):
                self.errors.add(key, "contains an empty entry.")
                continue
            if lookup == "id":
                text = english_numbers(str(value)).strip()
                if not _looks_like_uuid(text):
                    self.errors.add(key, "invalid reference.")
                    continue
                collected.append(text)
            else:
                collected.append(text)

        if not collected:
            return

        # One queryset, permission-filtered, no per-item DB round-trips and no
        # materialization of the whole table. Schema-level filters are fixed
        # equality conditions from the trusted schema — combined with (never
        # replacing) the registry's user-level permission filter.
        try:
            qs = spec.queryset_for_user(self.user)
            schema_filter = relation.get("filter")
            if isinstance(schema_filter, dict) and schema_filter:
                qs = qs.filter(**schema_filter)
        except (DjangoValidationError, ValueError, TypeError, FieldError):
            self.errors.add(key, "reference is not available to you.")
            return

        if lookup == "id":
            found = set(str(pk) for pk in qs.filter(pk__in=collected).values_list("pk", flat=True))
        else:
            found = set(
                str(v) for v in qs.filter(**{f"{lookup}__in": collected}).values_list(lookup, flat=True)
            )

        missing = [v for v in collected if str(v) not in found]
        if missing:
            # Deliberately vague: existence and access are indistinguishable.
            self.errors.add(key, "reference is not available to you.")

    def _relation_fallback(self, key, spec, raw):
        fallback_type = spec.fallback.get("type", "text")
        if fallback_type == "text":
            if isinstance(raw, list):
                for item in raw:
                    if not isinstance(item, str):
                        self.errors.add(key, "must be text.")
                        return
            elif not isinstance(raw, str):
                self.errors.add(key, "must be text.")
        else:  # pragma: no cover - only text fallbacks are declared
            self.errors.add(key, "unsupported fallback type.")

    # ── files ─────────────────────────────────────────────────────────────

    def _validate_file(self, key, definition, raw):
        """
        ``file`` fields carry attachment ids created through the upload
        endpoint, or a list of ids for multi-file use. The payload value is
        validated against already-stored attachments — never against a
        client-supplied path, filename, MIME type or checksum.
        """
        values = raw if isinstance(raw, list) else [raw]
        for value in values:
            text = english_numbers(str(value)).strip()
            if not _looks_like_uuid(text):
                self.errors.add(key, "invalid attachment reference.")
            elif text not in self.existing_attachment_keys:
                self.errors.add(key, "attachment not found for this submission.")

    # ── tables ────────────────────────────────────────────────────────────

    def _validate_table(self, key, definition, raw):
        if not isinstance(raw, list):
            self.errors.add(key, "must be a list of rows.")
            return
        max_rows = definition.get("max_rows", 500)
        if len(raw) > max_rows:
            self.errors.add(key, f"may contain at most {max_rows} rows.")
            return
        columns = {
            c["key"]: c
            for c in definition.get("columns", [])
            if isinstance(c, dict) and c.get("key")
        }
        for index, row in enumerate(raw):
            if not isinstance(row, dict):
                self.errors.add(key, f"row {index + 1} must be an object.")
                continue
            for col_key in row:
                if col_key not in columns:
                    self.errors.add(key, f"row {index + 1} has an unknown column {col_key!r}.")
            for col_key, col_def in columns.items():
                cell = row.get(col_key)
                if col_def.get("required") and _is_blank(cell):
                    self.errors.add(key, f"row {index + 1}: {col_key} is required.")
                    continue
                if _is_blank(cell):
                    continue
                sub = FormDataValidator(
                    [{"key": "cell", "type": col_def.get("type", "text"),
                      "order": 1, **{k: v for k, v in col_def.items()
                                     if k not in {"key", "type", "order"}}}],
                    {"cell": cell},
                    user=self.user,
                )
                sub_errors = sub.run().as_dict().get("cell")
                if sub_errors:
                    self.errors.add(key, f"row {index + 1}: {sub_errors[0]}")

    def _validate_attendance_table(self, key, definition, raw):
        """
        Row contract: {student_id, status, note?} — per the project spec.
        Students must belong to the class group chosen elsewhere in the payload.
        """
        if not isinstance(raw, list):
            self.errors.add(key, "must be a list of attendance rows.")
            return
        statuses = set(definition.get("statuses") or ATTENDANCE_STATUSES_DEFAULT)
        max_rows = definition.get("max_rows", 500)
        if len(raw) > max_rows:
            self.errors.add(key, f"may contain at most {max_rows} rows.")
            return
        group_field = definition.get("class_group_field", "class_group")
        group_id = self.data.get(group_field)
        allowed_students = self._class_group_students(group_id)
        seen_students: set[str] = set()
        for index, row in enumerate(raw):
            if not isinstance(row, dict):
                self.errors.add(key, f"row {index + 1} must be an object.")
                continue
            for extra in row:
                if extra not in {"student_id", "status", "note"}:
                    self.errors.add(key, f"row {index + 1} has an unknown key {extra!r}.")
            student = row.get("student_id")
            status = row.get("status")
            if _is_blank(student):
                self.errors.add(key, f"row {index + 1}: student_id is required.")
            else:
                marker = english_numbers(str(student)).strip()
                if marker in seen_students:
                    self.errors.add(key, f"row {index + 1}: duplicate student_id.")
                seen_students.add(marker)
                if allowed_students is not None and marker not in allowed_students:
                    self.errors.add(
                        key, f"row {index + 1}: student does not belong to the selected class group."
                    )
            if status not in statuses:
                self.errors.add(key, f"row {index + 1}: status must be one of {sorted(statuses)}.")
            note = row.get("note")
            if note is not None and (not isinstance(note, str) or len(note) > 500):
                self.errors.add(key, f"row {index + 1}: note must be text up to 500 characters.")

    def _validate_grade_table(self, key, definition, raw):
        """
        Descriptive (qualitative) grade rows: {student_id, result, teacher_note}.
        Numeric scores are rejected by design — this school issues pass/fail
        with a mandatory teacher note.
        """
        if not isinstance(raw, list):
            self.errors.add(key, "must be a list of grade rows.")
            return
        max_rows = definition.get("max_rows", 500)
        if len(raw) > max_rows:
            self.errors.add(key, f"may contain at most {max_rows} rows.")
            return
        allowed_results = set(definition.get("results") or {"passed", "failed"})
        group_field = definition.get("class_group_field", "class_group")
        group_id = self.data.get(group_field)
        allowed_students = self._class_group_students(group_id)
        seen_students: set[str] = set()
        for index, row in enumerate(raw):
            if not isinstance(row, dict):
                self.errors.add(key, f"row {index + 1} must be an object.")
                continue
            for extra in row:
                if extra not in {"student_id", "result", "teacher_note", "note"}:
                    self.errors.add(key, f"row {index + 1} has an unknown key {extra!r}.")
            student = row.get("student_id")
            if _is_blank(student):
                self.errors.add(key, f"row {index + 1}: student_id is required.")
            else:
                marker = english_numbers(str(student)).strip()
                if marker in seen_students:
                    self.errors.add(key, f"row {index + 1}: duplicate student_id.")
                seen_students.add(marker)
                if allowed_students is not None and marker not in allowed_students:
                    self.errors.add(
                        key, f"row {index + 1}: student does not belong to the selected class group."
                    )
            result = row.get("result")
            if result not in allowed_results:
                self.errors.add(key, f"row {index + 1}: result must be one of {sorted(allowed_results)}.")
            if "score" in row:
                # Qualitative grading only — reject numeric payloads explicitly.
                self.errors.add(key, f"row {index + 1}: numeric scores are not accepted.")
            note = row.get("teacher_note")
            if not isinstance(note, str) or not note.strip():
                self.errors.add(key, f"row {index + 1}: teacher_note is required.")
            elif len(note) > 1000:
                self.errors.add(key, f"row {index + 1}: teacher_note must be at most 1000 characters.")
            legacy_note = row.get("note")
            if legacy_note is not None and (not isinstance(legacy_note, str) or len(legacy_note) > 500):
                self.errors.add(key, f"row {index + 1}: note must be text up to 500 characters.")

    def _class_group_students(self, group_id) -> Optional[set[str]]:
        """
        Student ids enrolled in the selected class group (None when the group
        itself is absent/invalid — the group's own field error covers that).
        """
        if _is_blank(group_id) or not _looks_like_uuid(english_numbers(str(group_id)).strip()):
            return None
        try:
            spec = relations.resolve("academic.class_group")
            if not spec.is_available():
                return None
        except relations.UnknownRelationKey:  # pragma: no cover - static registry
            return None
        if not hasattr(self.user, "role_codes") or not getattr(self.user, "is_authenticated", False):
            return None
        group = spec.queryset_for_user(self.user).filter(
            pk=english_numbers(str(group_id)).strip()
        ).first()
        if group is None:
            return None
        return set(
            str(pk) for pk in group.enrollments.filter(
                is_active=True, is_deleted=False
            ).values_list("student_id", flat=True)
        )


def _looks_like_uuid(value: str) -> bool:
    import uuid

    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def attachment_limits() -> tuple[set[str], set[str], int]:
    """Return (allowed extensions, allowed MIME types, max bytes) from settings."""
    extensions = set(
        getattr(settings, "FORMS_ALLOWED_EXTENSIONS", DEFAULT_ALLOWED_EXTENSIONS)
    )
    mime_types = set(
        getattr(
            settings,
            "FORMS_ALLOWED_MIME_TYPES",
            {
                "application/pdf", "image/png", "image/jpeg", "image/gif",
                "image/webp", "text/plain", "text/csv", "application/zip",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            },
        )
    )
    max_bytes = int(getattr(settings, "FORMS_MAX_UPLOAD_SIZE", 10 * 1024 * 1024))
    return extensions, mime_types, max_bytes
