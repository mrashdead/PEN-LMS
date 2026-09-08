"""
Pure schema-structure validation (no DB, no model imports).

Shared by ``FormSchema.clean()`` (model boundary) and ``FormDataValidator``
(runtime). Keeping it dependency-free avoids circular imports between models
and validators.

Field-definition contract (dict):
    key            str   — ^[a-z][a-z0-9_]*$, unique in the schema
    type           str   — one of SUPPORTED_FIELD_TYPES
    label          str   — optional display label (Persian in practice)
    order          int   — positive, unique in the schema
    required       bool  — optional (default False)
    column_span    int   — optional, 1 or 2
    conditional    dict  — optional {field, operator, value}
    ...type-specific keys (options, relation, min, max, ...)

Conditional logic is a small declarative allowlist (eq/neq/in/not_in/exists).
Nothing here ever evaluates expressions — no eval/exec/arbitrary imports.
"""
from __future__ import annotations

import re

SUPPORTED_FIELD_TYPES = {
    "text", "textarea", "rich_text",
    "number", "integer", "decimal",
    "date", "datetime", "time",
    "select", "multi_select", "boolean",
    "relation", "multi_relation",
    "file", "table", "attendance_table", "grade_table",
}
RELATION_TYPES = {"relation", "multi_relation"}
SCALAR_TYPES = {
    "text", "textarea", "rich_text", "number", "integer", "decimal",
    "date", "datetime", "time", "select", "boolean",
}
TABLE_COLUMN_TYPES = {"text", "textarea", "number", "integer", "decimal",
                      "date", "time", "select", "boolean"}
CONDITIONAL_OPERATORS = {"eq", "neq", "in", "not_in", "exists"}
ATTENDANCE_STATUSES_DEFAULT = ["present", "absent", "late", "excused"]
COLUMN_SPANS = {1, 2}
KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")
# ReDoS heuristics for admin-authored regex patterns (patterns are trusted
# input from schema authors, never from clients — but we still bound them).
MAX_PATTERN_LENGTH = 200
_UNSAFE_PATTERN_RE = re.compile(r"\(\?|\\\d|\*\s*\*|\|\s*\|")

class SchemaDefinitionError(ValueError):
    """Raised when a FormSchema.fields definition is structurally invalid."""


def validate_form_fields(fields) -> list[dict]:
    """
    Validate a schema ``fields`` list. Returns the fields sorted by ``order``.

    Raises ``SchemaDefinitionError`` with a human-readable message on the first
    structural problem (fail fast — a schema is either fully valid or rejected).
    """
    if not isinstance(fields, list) or not fields:
        raise SchemaDefinitionError("fields must be a non-empty list.")

    seen_keys: set[str] = set()
    seen_orders: set[int] = set()
    for idx, field in enumerate(fields):
        if not isinstance(field, dict):
            raise SchemaDefinitionError(f"field #{idx} must be an object.")

        key = field.get("key")
        if not isinstance(key, str) or not KEY_RE.match(key):
            raise SchemaDefinitionError(
                f"field #{idx} has an invalid key {key!r}; must match ^[a-z][a-z0-9_]*$."
            )
        if key in seen_keys:
            raise SchemaDefinitionError(f"duplicate field key {key!r}.")
        seen_keys.add(key)

        ftype = field.get("type")
        if ftype not in SUPPORTED_FIELD_TYPES:
            raise SchemaDefinitionError(
                f"field {key!r} has unsupported type {ftype!r}."
            )

        order = field.get("order")
        if not isinstance(order, int) or isinstance(order, bool) or order < 1:
            raise SchemaDefinitionError(f"field {key!r} order must be a positive integer.")
        if order in seen_orders:
            raise SchemaDefinitionError(f"duplicate field order {order} (field {key!r}).")
        seen_orders.add(order)

        span = field.get("column_span", 1)
        if span not in COLUMN_SPANS:
            raise SchemaDefinitionError(f"field {key!r} column_span must be 1 or 2.")

        required = field.get("required", False)
        if not isinstance(required, bool):
            raise SchemaDefinitionError(f"field {key!r} required must be a boolean.")

        label = field.get("label")
        if label is not None and not isinstance(label, str):
            raise SchemaDefinitionError(f"field {key!r} label must be a string.")

        _validate_common_constraints(key, field)
        _validate_type_specific(key, field, ftype)

        conditional = field.get("conditional")
        if conditional is not None:
            _validate_conditional(key, conditional)

    # Second pass: conditional/after references may point to later-defined
    # fields, so validate references against the full key set.
    all_keys = {f.get("key") for f in fields}
    for field in fields:
        conditional = field.get("conditional")
        if conditional and conditional.get("field") not in all_keys:
            raise SchemaDefinitionError(
                f"field {field.get('key')!r} conditional references unknown field "
                f"{conditional.get('field')!r}."
            )
        after = field.get("after")
        if after is not None and after not in all_keys:
            raise SchemaDefinitionError(
                f"field {field.get('key')!r} after references unknown field {after!r}."
            )

    return sorted(fields, key=lambda f: f["order"])


def _validators_block(field: dict) -> dict:
    """
    Resolve the effective constraint map for a field definition.

    The catalog/spec format nests constraints under ``validators``
    (min_length, max_length, min_value, max_value, regex, allowed_extensions,
    max_file_size); the flat form keeps them at the top level. Both are
    accepted so existing definitions and spec-style definitions validate
    identically.
    """
    nested = field.get("validators")
    if not isinstance(nested, dict):
        return field
    merged = dict(field)
    mapping = {
        "min_length": "min_length", "max_length": "max_length",
        "min_value": "min", "max_value": "max", "regex": "pattern",
        "allowed_extensions": "accept", "max_file_size": "max_file_size",
        "allowed_mime_types": "mime_types",
    }
    for nested_key, flat_key in mapping.items():
        if flat_key not in merged and nested_key in nested:
            merged[flat_key] = nested[nested_key]
    # Accept both ".pdf" and "pdf" spellings; normalize to dotted form.
    accept = merged.get("accept")
    if isinstance(accept, list):
        normalized = []
        for ext in accept:
            text = str(ext).strip().lower()
            if text and not text.startswith("."):
                text = f".{text}"
            normalized.append(text)
        merged["accept"] = normalized
    return merged


def _validate_common_constraints(key: str, field: dict) -> None:
    """Constraints that apply across several scalar types."""
    field = _validators_block(field)
    for name in ("min_length", "max_length"):
        value = field.get(name)
        if value is not None and (
            not isinstance(value, int) or isinstance(value, bool) or value < 1
        ):
            raise SchemaDefinitionError(f"field {key!r} {name} must be a positive integer.")
    if (
        field.get("min_length") is not None
        and field.get("max_length") is not None
        and field["min_length"] > field["max_length"]
    ):
        raise SchemaDefinitionError(f"field {key!r} min_length exceeds max_length.")

    pattern = field.get("pattern")
    if pattern is not None:
        _validate_pattern(key, pattern)

    for name in ("min", "max"):
        value = field.get(name)
        if value is not None and (
            not isinstance(value, (int, float)) or isinstance(value, bool)
        ):
            raise SchemaDefinitionError(f"field {key!r} {name} must be numeric.")
    if field.get("min") is not None and field.get("max") is not None:
        if field["min"] > field["max"]:
            raise SchemaDefinitionError(f"field {key!r} min exceeds max.")

    decimals = field.get("decimals")
    if decimals is not None and (
        not isinstance(decimals, int) or isinstance(decimals, bool) or decimals < 0
    ):
        raise SchemaDefinitionError(f"field {key!r} decimals must be a non-negative integer.")

    null_ok = field.get("allow_null")
    if null_ok is not None and not isinstance(null_ok, bool):
        raise SchemaDefinitionError(f"field {key!r} allow_null must be a boolean.")

    if field.get("after") is not None and not isinstance(field.get("after"), str):
        raise SchemaDefinitionError(f"field {key!r} after must be a field-key string.")


def _validate_pattern(key: str, pattern) -> None:
    if not isinstance(pattern, str):
        raise SchemaDefinitionError(f"field {key!r} pattern must be a string.")
    if len(pattern) > MAX_PATTERN_LENGTH:
        raise SchemaDefinitionError(
            f"field {key!r} pattern exceeds {MAX_PATTERN_LENGTH} characters."
        )
    if _UNSAFE_PATTERN_RE.search(pattern):
        raise SchemaDefinitionError(
            f"field {key!r} pattern uses unsupported constructs "
            "(lookahead/lookbehind/backreferences are not allowed)."
        )
    try:
        re.compile(pattern)
    except re.error as exc:
        raise SchemaDefinitionError(f"field {key!r} pattern does not compile: {exc}.") from exc


def _validate_type_specific(key: str, field: dict, ftype: str) -> None:
    field = _validators_block(field)
    if ftype in {"select", "multi_select"}:
        options = field.get("options")
        if not isinstance(options, list) or not options:
            raise SchemaDefinitionError(f"field {key!r} requires non-empty options.")
        values = []
        for opt in options:
            if not isinstance(opt, dict) or "value" not in opt:
                raise SchemaDefinitionError(
                    f"field {key!r} options must be objects with a 'value' key."
                )
            values.append(str(opt["value"]))
        if len(values) != len(set(values)):
            raise SchemaDefinitionError(f"field {key!r} has duplicate option values.")

    if ftype in RELATION_TYPES:
        relation = field.get("relation")
        if not isinstance(relation, dict) or not relation.get("registry_key"):
            raise SchemaDefinitionError(
                f"field {key!r} of type {ftype!r} requires relation.registry_key."
            )
        lookup = relation.get("lookup", "id")
        if not isinstance(lookup, str):
            raise SchemaDefinitionError(f"field {key!r} relation.lookup must be a string.")
        rel_required = relation.get("required", True)
        if not isinstance(rel_required, bool):
            raise SchemaDefinitionError(
                f"field {key!r} relation.required must be a boolean."
            )
        fallback = relation.get("fallback")
        if fallback is not None:
            if not isinstance(fallback, dict) or not fallback.get("type"):
                raise SchemaDefinitionError(
                    f"field {key!r} relation.fallback must declare a 'type'."
                )
        # Schema-level filter is a fixed dict of equality conditions applied on
        # top of the registry's permission filter (never client-controlled).
        rel_filter = relation.get("filter")
        if rel_filter is not None and not isinstance(rel_filter, dict):
            raise SchemaDefinitionError(f"field {key!r} relation.filter must be an object.")
        multiple = relation.get("multiple")
        if multiple is not None and not isinstance(multiple, bool):
            raise SchemaDefinitionError(f"field {key!r} relation.multiple must be a boolean.")

    if ftype == "file":
        accept = field.get("accept")
        if accept is not None:
            if not isinstance(accept, list) or not all(
                isinstance(a, str) and re.match(r"^\.[A-Za-z0-9]{1,5}$", a) for a in accept
            ):
                raise SchemaDefinitionError(
                    f"field {key!r} accept must be a list of dotted extensions "
                    "like ['.pdf', '.jpg']."
                )
        mime_types = field.get("mime_types")
        if mime_types is not None and (
            not isinstance(mime_types, list)
            or not all(isinstance(m, str) and "/" in m for m in mime_types)
        ):
            raise SchemaDefinitionError(
                f"field {key!r} mime_types must be a list of 'type/subtype' strings."
            )
        max_file_size = field.get("max_file_size")
        if max_file_size is not None and (
            not isinstance(max_file_size, int)
            or isinstance(max_file_size, bool)
            or max_file_size < 1
        ):
            raise SchemaDefinitionError(f"field {key!r} max_file_size must be a positive integer.")

    if ftype == "table":
        columns = field.get("columns")
        if not isinstance(columns, list) or not columns:
            raise SchemaDefinitionError(f"field {key!r} requires non-empty columns.")
        col_keys = set()
        for col in columns:
            if not isinstance(col, dict):
                raise SchemaDefinitionError(f"field {key!r} columns must be objects.")
            ckey = col.get("key")
            if not isinstance(ckey, str) or not KEY_RE.match(ckey):
                raise SchemaDefinitionError(f"field {key!r} column key {ckey!r} invalid.")
            if ckey in col_keys:
                raise SchemaDefinitionError(f"field {key!r} duplicate column {ckey!r}.")
            col_keys.add(ckey)
            ctype = col.get("type", "text")
            if ctype not in TABLE_COLUMN_TYPES:
                raise SchemaDefinitionError(
                    f"field {key!r} column {ckey!r} has unsupported type {ctype!r}."
                )

    if ftype == "attendance_table":
        statuses = field.get("statuses", ATTENDANCE_STATUSES_DEFAULT)
        if not isinstance(statuses, list) or not statuses or not all(
            isinstance(s, str) and s for s in statuses
        ):
            raise SchemaDefinitionError(
                f"field {key!r} statuses must be a non-empty list of strings."
            )

    if ftype == "grade_table":
        # Descriptive grading: result ∈ results, teacher_note required.
        results = field.get("results")
        if results is not None and (
            not isinstance(results, list)
            or not results
            or not all(isinstance(r, str) and r for r in results)
        ):
            raise SchemaDefinitionError(
                f"field {key!r} results must be a non-empty list of strings."
            )
        class_group_field = field.get("class_group_field", "class_group")
        if not isinstance(class_group_field, str):
            raise SchemaDefinitionError(f"field {key!r} class_group_field must be a string.")


def _validate_conditional(key: str, conditional) -> None:
    if not isinstance(conditional, dict):
        raise SchemaDefinitionError(f"field {key!r} conditional must be an object.")
    ref = conditional.get("field")
    operator = conditional.get("operator")
    if not isinstance(ref, str) or not ref:
        raise SchemaDefinitionError(
            f"field {key!r} conditional requires a 'field' reference."
        )
    if ref == key:
        raise SchemaDefinitionError(f"field {key!r} conditional cannot reference itself.")
    if operator not in CONDITIONAL_OPERATORS:
        raise SchemaDefinitionError(
            f"field {key!r} conditional operator {operator!r} unsupported."
        )
    if operator != "exists" and "value" not in conditional:
        raise SchemaDefinitionError(
            f"field {key!r} conditional operator {operator!r} requires a 'value'."
        )
    if operator in {"in", "not_in"} and not isinstance(conditional.get("value"), list):
        raise SchemaDefinitionError(
            f"field {key!r} conditional operator {operator!r} requires a list value."
        )


def evaluate_condition(conditional: dict, data: dict) -> bool:
    """
    Evaluate a declarative condition against submitted data.

    Pure and allowlisted — never compiles or executes client input.
    """
    operator = conditional.get("operator")
    ref = conditional.get("field")
    expected = conditional.get("value")
    actual = data.get(ref)

    if operator == "exists":
        return actual not in (None, "", [], {})
    if operator == "eq":
        return actual == expected
    if operator == "neq":
        return actual != expected
    if operator == "in":
        return isinstance(expected, list) and actual in expected
    if operator == "not_in":
        return isinstance(expected, list) and actual not in expected
    # Unknown operator at runtime → field stays hidden (fail closed).
    return False
