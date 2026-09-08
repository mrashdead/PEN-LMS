"""Dynamic data validation: scalars, relations, tables, conditions, files."""
from __future__ import annotations

from unittest.mock import patch

from django.test import TestCase, override_settings

from apps.forms import relations
from apps.forms.relations import MissingRequiredRelation, UnknownRelationKey
from apps.forms.sanitizers import (
    RichTextSanitizerUnavailable,
    sanitize_rich_text,
    sanitize_text,
)
from apps.forms.schema_validation import (
    SchemaDefinitionError,
    evaluate_condition,
    validate_form_fields,
)
from apps.forms.tests.factories import (
    UserFactory,
    make_class_group,
    make_enrollment,
    make_person,
)
from apps.forms.validation import FormDataValidator


def _v(fields, data, user=None):
    return FormDataValidator(fields, data, user=user, schema_slug="t").run()


class ScalarValidationTests(TestCase):
    def test_required_missing(self):
        errors = _v(
            [{"key": "a", "type": "text", "order": 1, "required": True}], {},
        ).as_dict()
        self.assertIn("a", errors)

    def test_number_bounds_and_coercion(self):
        fields = [{"key": "n", "type": "number", "order": 1, "min": 1, "max": 10}]
        self.assertTrue(_v(fields, {"n": 5}).ok)
        # Persian digits coerce safely.
        self.assertTrue(_v(fields, {"n": "۷"}).ok)
        self.assertIn("n", _v(fields, {"n": 50}).as_dict())
        self.assertIn("n", _v(fields, {"n": "abc"}).as_dict())

    def test_integer_rejects_fraction(self):
        fields = [{"key": "n", "type": "integer", "order": 1}]
        self.assertIn("n", _v(fields, {"n": 1.5}).as_dict())

    def test_decimal_precision(self):
        fields = [{"key": "n", "type": "decimal", "order": 1, "decimals": 2}]
        self.assertIn("n", _v(fields, {"n": "1.234"}).as_dict())
        self.assertTrue(_v(fields, {"n": "1.23"}).ok)

    def test_string_length_and_regex(self):
        fields = [{"key": "s", "type": "text", "order": 1, "min_length": 3,
                   "max_length": 5, "pattern": "^[0-9]+$"}]
        self.assertIn("s", _v(fields, {"s": "12"}).as_dict())
        self.assertIn("s", _v(fields, {"s": "123456"}).as_dict())
        self.assertIn("s", _v(fields, {"s": "ab1"}).as_dict())
        self.assertTrue(_v(fields, {"s": "123"}).ok)

    def test_select_membership(self):
        fields = [{"key": "s", "type": "select", "order": 1,
                   "options": [{"value": "x"}, {"value": "y"}]}]
        self.assertTrue(_v(fields, {"s": "x"}).ok)
        self.assertIn("s", _v(fields, {"s": "z"}).as_dict())

    def test_multi_select_membership_and_duplicates(self):
        fields = [{"key": "m", "type": "multi_select", "order": 1,
                   "options": [{"value": "x"}, {"value": "y"}]}]
        self.assertTrue(_v(fields, {"m": ["x", "y"]}).ok)
        self.assertIn("m", _v(fields, {"m": ["x", "z"]}).as_dict())
        self.assertIn("m", _v(fields, {"m": ["x", "x"]}).as_dict())

    def test_date_datetime_time_formats(self):
        self.assertTrue(_v([{"key": "d", "type": "date", "order": 1}], {"d": "2026-05-01"}).ok)
        self.assertIn("d", _v([{"key": "d", "type": "date", "order": 1}], {"d": "not-a-date"}).as_dict())
        self.assertIn("t", _v([{"key": "t", "type": "time", "order": 1}], {"t": "25:00"}).as_dict())
        self.assertTrue(_v([{"key": "t", "type": "time", "order": 1}], {"t": "08:00"}).ok)
        self.assertIn("dt", _v([{"key": "dt", "type": "datetime", "order": 1}], {"dt": "2026-13-99 10:00"}).as_dict())

    def test_time_after_cross_field(self):
        fields = [
            {"key": "start", "type": "time", "order": 1},
            {"key": "end", "type": "time", "order": 2, "after": "start"},
        ]
        self.assertTrue(_v(fields, {"start": "08:00", "end": "09:30"}).ok)
        self.assertIn("end", _v(fields, {"start": "10:00", "end": "09:00"}).as_dict())

    def test_boolean_strict(self):
        fields = [{"key": "b", "type": "boolean", "order": 1}]
        self.assertTrue(_v(fields, {"b": True}).ok)
        self.assertIn("b", _v(fields, {"b": "yes"}).as_dict())

    def test_unknown_keys_rejected(self):
        errors = _v([{"key": "a", "type": "text", "order": 1}], {"a": "x", "evil": 1}).as_dict()
        self.assertIn("evil", errors)

    def test_hidden_conditional_field_must_be_empty(self):
        fields = [
            {"key": "kind", "type": "select", "order": 1, "options": [{"value": "a"}, {"value": "b"}]},
            {"key": "extra", "type": "text", "order": 2,
             "conditional": {"field": "kind", "operator": "eq", "value": "b"}},
        ]
        self.assertTrue(_v(fields, {"kind": "a"}).ok)
        self.assertIn("extra", _v(fields, {"kind": "a", "extra": "sneak"}).as_dict())

    def test_conditional_requirement_only_when_visible(self):
        fields = [
            {"key": "kind", "type": "select", "order": 1, "options": [{"value": "a"}, {"value": "b"}]},
            {"key": "extra", "type": "text", "order": 2, "required": True,
             "conditional": {"field": "kind", "operator": "eq", "value": "b"}},
        ]
        self.assertTrue(_v(fields, {"kind": "a"}).ok)
        self.assertIn("extra", _v(fields, {"kind": "b"}).as_dict())
        self.assertTrue(_v(fields, {"kind": "b", "extra": "ok"}).ok)

    def test_evaluate_condition_operators(self):
        data = {"a": "x", "b": ["1", "2"], "c": None}
        self.assertTrue(evaluate_condition({"field": "a", "operator": "eq", "value": "x"}, data))
        self.assertFalse(evaluate_condition({"field": "a", "operator": "neq", "value": "x"}, data))
        self.assertTrue(evaluate_condition({"field": "a", "operator": "in", "value": ["x", "y"]}, data))
        self.assertTrue(evaluate_condition({"field": "a", "operator": "not_in", "value": ["z"]}, data))
        self.assertFalse(evaluate_condition({"field": "c", "operator": "exists"}, data))
        self.assertTrue(evaluate_condition({"field": "b", "operator": "exists"}, data))
        # Unknown operator fails closed.
        self.assertFalse(evaluate_condition({"field": "a", "operator": "gt", "value": 1}, data))


class RelationValidationTests(TestCase):
    def setUp(self):
        self.teacher_user = UserFactory(username="rel-teacher", roles=["teacher"])
        self.teacher_person = make_person(self.teacher_user, "teacher")
        self.student_user = UserFactory(username="rel-student", roles=["student"])
        self.student_person = make_person(self.student_user, "student")
        self.group = make_class_group(teacher=self.teacher_person)
        self.other_group = make_class_group()  # no teacher
        self.fields = [{"key": "g", "type": "relation", "order": 1,
                        "relation": {"registry_key": "academic.class_group"}}]

    def test_arbitrary_model_label_never_resolved(self):
        with self.assertRaises(UnknownRelationKey):
            relations.resolve("django.contrib.auth.models.User")
        with self.assertRaises(UnknownRelationKey):
            relations.resolve("academics.ClassGroup")  # not a registry key
        with self.assertRaises(UnknownRelationKey):
            relations.resolve("")

    def test_teacher_can_reference_own_group(self):
        data = {"g": str(self.group.pk)}
        self.assertTrue(_v(self.fields, data, user=self.teacher_user).ok)

    def test_teacher_cannot_reference_other_groups(self):
        data = {"g": str(self.other_group.pk)}
        errors = _v(self.fields, data, user=self.teacher_user).as_dict()
        self.assertIn("g", errors)
        # Error must not leak existence vs access distinction.
        self.assertNotIn(str(self.other_group.pk), errors["g"][0])

    def test_invalid_relation_uuid_rejected(self):
        data = {"g": "not-a-uuid"}
        self.assertIn("g", _v(self.fields, data, user=self.teacher_user).as_dict())

    def test_missing_required_relation_surfaces_actionable_field_error(self):
        fields = [{"key": "l", "type": "relation", "order": 1,
                   "relation": {"registry_key": "academic.lesson"}}]
        errors = _v(fields, {"l": "11111111-1111-1111-1111-111111111111"},
                    user=self.teacher_user).as_dict()
        self.assertIn("l", errors)
        # Reports the expected model — never silently coerced to text.
        self.assertIn("education.Lesson", errors["l"][0])

    def test_ensure_available_raises_for_missing_required(self):
        spec = relations.resolve("academic.lesson")
        self.assertFalse(spec.is_available())
        with self.assertRaises(MissingRequiredRelation) as ctx:
            relations.ensure_available(spec, ["lesson"])
        self.assertIn("academic.lesson", ctx.exception.key)
        self.assertEqual(ctx.exception.schema_slugs, ["lesson"])

    def test_optional_relation_fallback_accepts_text(self):
        spec = relations.resolve("academic.venue")
        self.assertFalse(spec.is_available())
        self.assertTrue(spec.optional)
        fields = [{"key": "v", "type": "relation", "order": 1,
                   "relation": {"registry_key": "academic.venue"}}]
        result = _v(fields, {"v": "سالن اجتماعات"}, user=self.teacher_user)
        self.assertTrue(result.ok)

    def test_relation_queryset_is_filtered_not_materialized(self):
        qs = relations.resolve("academic.class_group").queryset_for_user(self.teacher_user)
        self.assertIn(str(self.group.pk), str(qs.filter(pk=self.group.pk).values_list("pk", flat=True)))
        self.assertFalse(qs.filter(pk=self.other_group.pk).exists())


class TableValidationTests(TestCase):
    def setUp(self):
        self.teacher_user = UserFactory(username="tbl-teacher", roles=["teacher"])
        self.teacher_person = make_person(self.teacher_user, "teacher")
        self.group = make_class_group(teacher=self.teacher_person)
        self.student_a = make_person(None, "student", first_name="A")
        self.student_b = make_person(None, "student", first_name="B")
        make_enrollment(self.group, self.student_a)
        # student_b is NOT enrolled in self.group.

    def _attendance_fields(self):
        return [
            {"key": "class_group", "type": "relation", "order": 1,
             "relation": {"registry_key": "academic.class_group"}},
            {"key": "attendance_list", "type": "attendance_table", "order": 2, "required": True},
        ]

    def test_attendance_valid_rows(self):
        data = {
            "class_group": str(self.group.pk),
            "attendance_list": [
                {"student_id": str(self.student_a.pk), "status": "present"},
            ],
        }
        self.assertTrue(_v(self._attendance_fields(), data, user=self.teacher_user).ok)

    def test_attendance_duplicate_student_rejected(self):
        data = {
            "class_group": str(self.group.pk),
            "attendance_list": [
                {"student_id": str(self.student_a.pk), "status": "present"},
                {"student_id": str(self.student_a.pk), "status": "absent"},
            ],
        }
        self.assertIn("attendance_list",
                      _v(self._attendance_fields(), data, user=self.teacher_user).as_dict())

    def test_attendance_student_must_belong_to_class_group(self):
        data = {
            "class_group": str(self.group.pk),
            "attendance_list": [
                {"student_id": str(self.student_b.pk), "status": "present"},
            ],
        }
        errors = _v(self._attendance_fields(), data, user=self.teacher_user).as_dict()
        self.assertIn("attendance_list", errors)
        self.assertTrue(any("class group" in e for e in errors["attendance_list"]))

    def test_attendance_status_membership(self):
        data = {
            "class_group": str(self.group.pk),
            "attendance_list": [
                {"student_id": str(self.student_a.pk), "status": "sleeping"},
            ],
        }
        self.assertIn("attendance_list",
                      _v(self._attendance_fields(), data, user=self.teacher_user).as_dict())

    def _grade_fields(self):
        return [
            {"key": "class_group", "type": "relation", "order": 1,
             "relation": {"registry_key": "academic.class_group"}},
            {"key": "grade_list", "type": "grade_table", "order": 2, "required": True},
        ]

    def test_grade_valid_descriptive_row(self):
        data = {
            "class_group": str(self.group.pk),
            "grade_list": [
                {"student_id": str(self.student_a.pk), "result": "passed",
                 "teacher_note": "عالی پیشرفت کرد"},
            ],
        }
        self.assertTrue(_v(self._grade_fields(), data, user=self.teacher_user).ok)

    def test_grade_numeric_score_rejected(self):
        data = {
            "class_group": str(self.group.pk),
            "grade_list": [
                {"student_id": str(self.student_a.pk), "result": "passed",
                 "teacher_note": "x", "score": 18.5},
            ],
        }
        errors = _v(self._grade_fields(), data, user=self.teacher_user).as_dict()
        self.assertIn("grade_list", errors)
        self.assertTrue(any("numeric" in e for e in errors["grade_list"]))

    def test_grade_requires_teacher_note(self):
        data = {
            "class_group": str(self.group.pk),
            "grade_list": [
                {"student_id": str(self.student_a.pk), "result": "passed"},
            ],
        }
        self.assertIn("grade_list",
                      _v(self._grade_fields(), data, user=self.teacher_user).as_dict())

    def test_grade_result_membership(self):
        data = {
            "class_group": str(self.group.pk),
            "grade_list": [
                {"student_id": str(self.student_a.pk), "result": "maybe",
                 "teacher_note": "x"},
            ],
        }
        self.assertIn("grade_list",
                      _v(self._grade_fields(), data, user=self.teacher_user).as_dict())


class SchemaStructureTests(TestCase):
    def test_valid_catalog_style_definition(self):
        fields = validate_form_fields([
            {"key": "lesson_title", "type": "text", "order": 1, "label": "عنوان",
             "required": True,
             "validators": {"min_length": 3, "max_length": 200}},
            {"key": "age", "type": "number", "order": 2,
             "validators": {"min_value": 3, "max_value": 100}},
        ])
        self.assertEqual(fields[0]["key"], "lesson_title")

    def test_duplicate_orders_rejected(self):
        with self.assertRaises(SchemaDefinitionError):
            validate_form_fields([
                {"key": "a", "type": "text", "order": 1},
                {"key": "b", "type": "text", "order": 1},
            ])

    def test_unsafe_regex_rejected(self):
        with self.assertRaises(SchemaDefinitionError):
            validate_form_fields([
                {"key": "a", "type": "text", "order": 1,
                 "pattern": "(?=x)abc"},  # lookahead unsupported
            ])

    def test_conditional_requires_value(self):
        with self.assertRaises(SchemaDefinitionError):
            validate_form_fields([
                {"key": "a", "type": "text", "order": 1},
                {"key": "b", "type": "text", "order": 2,
                 "conditional": {"field": "a", "operator": "eq"}},
            ])


class SanitizerTests(TestCase):
    def test_plain_text_control_chars_stripped(self):
        self.assertEqual(sanitize_text("hi\x00 the\x07re"), "hi there")

    @override_settings(FORMS_ALLOW_SECURITY_FALLBACKS=False)
    def test_rich_text_strips_scripts_with_bleach(self):
        import apps.forms.sanitizers as sanitizers
        if not sanitizers.HAS_BLEACH:
            self.skipTest("bleach not installed in this environment")
        dirty = '<p onclick="evil()">ok</p><script>bad()</script><a href="javascript:evil()">x</a>'
        clean = sanitize_rich_text(dirty)
        self.assertNotIn("<script>", clean)
        self.assertNotIn("onclick", clean)
        self.assertNotIn("javascript:", clean)
        self.assertIn("<p>ok</p>", clean)

    @override_settings(FORMS_ALLOW_SECURITY_FALLBACKS=False)
    def test_missing_bleach_fails_closed(self):
        import apps.forms.sanitizers as sanitizers
        with patch.object(sanitizers, "HAS_BLEACH", False):
            with self.assertRaises(RichTextSanitizerUnavailable):
                sanitize_rich_text("<b>x</b>")

    @override_settings(FORMS_ALLOW_SECURITY_FALLBACKS=True)
    def test_explicit_fallback_enabled(self):
        import apps.forms.sanitizers as sanitizers
        with patch.object(sanitizers, "HAS_BLEACH", False):
            clean = sanitize_rich_text('<p onclick="x()">hi</p><script>bad()</script>')
            self.assertNotIn("onclick", clean)
            self.assertNotIn("<script>", clean)
            self.assertIn("hi", clean)

    def test_fallback_never_derived_from_debug(self):
        # DEBUG=True must NOT enable the fallback on its own.
        import apps.forms.sanitizers as sanitizers
        with self.settings(DEBUG=True, FORMS_ALLOW_SECURITY_FALLBACKS=False):
            self.assertFalse(sanitizers._fallback_allowed())


class SpecAdapterTests(TestCase):
    """The spec-shaped entry point: FormDataValidator(schema, user).validate."""

    def _adapter(self, schema, user=None):
        from apps.forms.validators import FormDataValidator

        return FormDataValidator(schema, user=user)

    def test_validate_returns_cleaned_data(self):
        from apps.forms.models import FormSchema

        schema = FormSchema(
            slug="adapter", title="t",
            fields=[{"key": "name", "type": "text", "order": 1, "required": True}],
        )
        cleaned = self._adapter(schema).validate({"name": "علی\x00  رضا"})
        self.assertEqual(cleaned["name"], "علی رضا")  # control char stripped, collapsed

    def test_validate_raises_drf_error_keyed_by_field(self):
        from apps.forms.models import FormSchema
        from rest_framework.exceptions import ValidationError as DRFValidationError

        schema = FormSchema(
            slug="adapter2", title="t",
            fields=[{"key": "name", "type": "text", "order": 1, "required": True},
                    {"key": "age", "type": "number", "order": 2, "min": 3, "max": 100}],
        )
        with self.assertRaises(DRFValidationError) as ctx:
            self._adapter(schema).validate({"age": 500})
        self.assertIn("name", ctx.exception.detail)
        self.assertIn("age", ctx.exception.detail)

    def test_validate_rejects_unknown_keys(self):
        from apps.forms.models import FormSchema
        from rest_framework.exceptions import ValidationError as DRFValidationError

        schema = FormSchema(
            slug="adapter3", title="t",
            fields=[{"key": "name", "type": "text", "order": 1}],
        )
        with self.assertRaises(DRFValidationError) as ctx:
            self._adapter(schema).validate({"name": "x", "hacker": "y"})
        self.assertIn("hacker", ctx.exception.detail)

    def test_validate_sanitizes_rich_text_with_bleach(self):
        import apps.forms.sanitizers as sanitizers
        from apps.forms.models import FormSchema

        if not sanitizers.HAS_BLEACH:
            self.skipTest("bleach not installed")
        schema = FormSchema(
            slug="adapter4", title="t",
            fields=[{"key": "bio", "type": "rich_text", "order": 1}],
        )
        cleaned = self._adapter(schema).validate({"bio": "<b>سلام</b><script>x()</script>"})
        self.assertNotIn("<script>", cleaned["bio"])
        self.assertIn("<b>سلام</b>", cleaned["bio"])

    def test_nested_validators_block_is_honored(self):
        errors = _v(
            [{"key": "phone", "type": "text", "order": 1,
              "validators": {"regex": "^09[0-9]{9}$"}}],
            {"phone": "12345"},
        ).as_dict()
        self.assertIn("phone", errors)
        self.assertTrue(_v(
            [{"key": "phone", "type": "text", "order": 1,
              "validators": {"regex": "^09[0-9]{9}$"}}],
            {"phone": "09123456789"},
        ).ok)
