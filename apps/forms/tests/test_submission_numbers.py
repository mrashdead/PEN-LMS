"""Concurrency-safe submission-number generation."""
from __future__ import annotations

from django.db import IntegrityError
from django.test import TestCase

from apps.forms.models import FormSubmission, SubmissionSequence
from apps.forms.services import (
    NUMBER_RETRY_LIMIT,
    FormServiceError,
    _create_with_unique_number,
    _generate_number,
    _is_submission_number_collision,
    next_submission_number,
)
from apps.forms.tests.factories import UserFactory, make_schema


class NumberGenerationTests(TestCase):
    def setUp(self):
        self.user = UserFactory(username="num-user", roles=["employee"])
        self.schema = make_schema(slug="num")

    def test_format_uses_gregorian_year(self):
        from django.utils import timezone

        number = next_submission_number(self.schema)
        year = timezone.now().year
        self.assertTrue(number.startswith(f"FORM-NUM-{year}-"), number)

    def test_sequence_increments(self):
        first = next_submission_number(self.schema)
        second = next_submission_number(self.schema)
        seq1 = int(first.rsplit("-", 1)[1])
        seq2 = int(second.rsplit("-", 1)[1])
        self.assertEqual(seq2, seq1 + 1)

    def test_sequences_are_scoped_by_slug(self):
        other = make_schema(slug="other-num")
        n1 = next_submission_number(self.schema)
        n2 = next_submission_number(other)
        self.assertTrue(n1.startswith("FORM-NUM-"), n1)
        self.assertTrue(n2.startswith("FORM-OTHER-NUM-"), n2)
        self.assertEqual(SubmissionSequence.objects.count(), 2)

    def test_collision_detector_is_narrow(self):
        self.assertTrue(_is_submission_number_collision(IntegrityError("UNIQUE constraint failed: forms_submission.submission_number")))
        self.assertFalse(_is_submission_number_collision(IntegrityError("UNIQUE constraint failed: forms_comment.id")))
        self.assertFalse(_is_submission_number_collision(IntegrityError("some other db error")))

    def test_retry_reallocates_on_collision(self):
        """A number consumed by a committed concurrent insert must be
        re-allocated on retry (fresh number, not the stale one)."""
        stale = next_submission_number(self.schema)
        FormSubmission.objects.create(
            form_schema=self.schema, submitted_by=self.user,
            data={}, submission_number=stale,
        )
        attempts = {"n": 0}

        def fill():
            attempts["n"] += 1
            number = stale if attempts["n"] == 1 else next_submission_number(self.schema)
            return {
                "form_schema": self.schema,
                "submitted_by": self.user,
                "data": {},
                "status": FormSubmission.Status.DRAFT,
                "submission_number": number,
            }

        with self.assertLogs("apps.forms.services", level="WARNING"):
            submission = _create_with_unique_number(fill)
        self.assertEqual(attempts["n"], 2)
        self.assertNotEqual(submission.submission_number, stale)
        self.assertTrue(submission.submission_number.startswith("FORM-NUM-"))

    def test_retry_gives_up_after_bound(self):
        def always_colliding(schema):
            number = next_submission_number(schema)
            FormSubmission.objects.create(
                form_schema=schema, submitted_by=self.user,
                data={}, submission_number=number,
            )
            return number

        with self.assertRaises(FormServiceError) as ctx:
            _create_with_unique_number(lambda: {
                "form_schema": self.schema,
                "submitted_by": self.user,
                "data": {},
                "submission_number": always_colliding(self.schema),
            })
        self.assertIn(str(NUMBER_RETRY_LIMIT), str(ctx.exception))

    def test_unrelated_integrity_error_propagates(self):
        # submitted_by=None violates NOT NULL → not a number collision → raise.
        with self.assertRaises(IntegrityError):
            _create_with_unique_number(lambda: {
                "form_schema": self.schema,
                "submitted_by": None,
                "data": {},
                "submission_number": "FORM-NUM-2026-999999",
            })

    def test_generate_number_padding(self):
        self.assertEqual(_generate_number("grade-report", 2026, 1), "FORM-GRADE-REPORT-2026-000001")
        self.assertEqual(_generate_number("attendance", 2026, 42), "FORM-ATTENDANCE-2026-000042")
