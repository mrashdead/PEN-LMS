"""Model-level constraints and behavior for the forms app."""
from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.forms.models import FormComment, FormSchema, FormSubmission
from apps.forms.tests.factories import UserFactory, make_schema


class FormSchemaConstraintTests(TestCase):
    def test_slug_version_unique(self):
        make_schema(slug="dup", version=1)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                make_schema(slug="dup", version=1)

    def test_only_one_active_version_per_slug(self):
        make_schema(slug="act", version=1, is_active=True)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                make_schema(slug="act", version=2, is_active=True)

    def test_inactive_versions_can_coexist(self):
        make_schema(slug="multi", version=1, is_active=False)
        make_schema(slug="multi", version=2, is_active=False)
        self.assertEqual(FormSchema.objects.filter(slug="multi").count(), 2)

    def test_clean_rejects_duplicate_field_keys(self):
        schema = make_schema(
            slug="badkeys",
            fields=[
                {"key": "a", "type": "text", "order": 1},
                {"key": "a", "type": "text", "order": 2},
            ],
        )
        with self.assertRaises(ValidationError):
            schema.full_clean()

    def test_clean_rejects_unsupported_type(self):
        schema = make_schema(
            slug="badtype",
            fields=[{"key": "a", "type": "color_picker", "order": 1}],
        )
        with self.assertRaises(ValidationError):
            schema.full_clean()

    def test_clean_rejects_unknown_conditional_reference(self):
        schema = make_schema(
            slug="badcond",
            fields=[
                {"key": "a", "type": "text", "order": 1},
                {"key": "b", "type": "text", "order": 2,
                 "conditional": {"field": "ghost", "operator": "eq", "value": 1}},
            ],
        )
        with self.assertRaises(ValidationError):
            schema.full_clean()

    def test_active_schema_sets_published_at(self):
        schema = make_schema(slug="pub")
        self.assertIsNotNone(schema.published_at)


class FormSubmissionTests(TestCase):
    def setUp(self):
        self.user = UserFactory(username="sub-owner", roles=["employee"])
        self.schema = make_schema(slug="snap")

    def test_submission_number_unique(self):
        FormSubmission.objects.create(
            form_schema=self.schema, submitted_by=self.user,
            data={}, submission_number="FORM-SNAP-2026-000001",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                FormSubmission.objects.create(
                    form_schema=self.schema, submitted_by=self.user,
                    data={}, submission_number="FORM-SNAP-2026-000001",
                )

    def test_is_immutable_for_non_draft(self):
        submitted = FormSubmission.objects.create(
            form_schema=self.schema, submitted_by=self.user,
            data={}, status=FormSubmission.Status.SUBMITTED,
        )
        draft = FormSubmission.objects.create(
            form_schema=self.schema, submitted_by=self.user, data={},
        )
        self.assertTrue(submitted.is_immutable)
        self.assertFalse(draft.is_immutable)

    def test_effective_fields_prefers_snapshot(self):
        submission = FormSubmission.objects.create(
            form_schema=self.schema, submitted_by=self.user, data={},
            version_snapshot={"fields": [{"key": "only_in_snapshot", "type": "text", "order": 1}]},
        )
        fields = submission.effective_fields()
        self.assertEqual(fields[0]["key"], "only_in_snapshot")

    def test_historical_submission_survives_schema_edit(self):
        submission = FormSubmission.objects.create(
            form_schema=self.schema, submitted_by=self.user, data={},
            version_snapshot={"fields": self.schema.fields, "version": 1},
        )
        self.schema.fields = [{"key": "totally_new", "type": "text", "order": 1}]
        self.schema.save()
        submission.refresh_from_db()
        keys = {f["key"] for f in submission.effective_fields()}
        self.assertIn("title", keys)
        self.assertNotIn("totally_new", keys)


class FormCommentTests(TestCase):
    def setUp(self):
        self.user = UserFactory(username="commenter", roles=["employee"])
        self.schema = make_schema(slug="cmts")
        self.submission = FormSubmission.objects.create(
            form_schema=self.schema, submitted_by=self.user, data={},
        )

    def test_parent_must_belong_to_same_submission(self):
        other = FormSubmission.objects.create(
            form_schema=self.schema, submitted_by=self.user, data={},
        )
        parent = FormComment.objects.create(
            submission=other, author=self.user, body="x",
        )
        child = FormComment(
            submission=self.submission, author=self.user, body="y", parent=parent,
        )
        with self.assertRaises(ValidationError):
            child.full_clean()

    def test_self_parent_rejected(self):
        comment = FormComment.objects.create(
            submission=self.submission, author=self.user, body="x",
        )
        comment.parent_id = comment.pk
        with self.assertRaises(ValidationError):
            comment.full_clean()
