"""Service-layer behaviors not covered by API tests: sanitization-on-write,
visibility derivation, sensitive logging, checks."""
from __future__ import annotations

from unittest.mock import patch

from django.test import TestCase, override_settings

from apps.forms.models import FormSubmission
from apps.forms.services import (
    FormServiceError,
    FormSubmissionService,
    derive_visibility,
    log_sensitive_access,
)
from apps.forms.tests.factories import (
    UserFactory,
    make_class_group,
    make_enrollment,
    make_person,
    make_schema,
)

service = FormSubmissionService()


class SanitizationOnWriteTests(TestCase):
    @override_settings(FORMS_ALLOW_SECURITY_FALLBACKS=False)
    def test_rich_text_sanitized_before_persist(self):
        import apps.forms.sanitizers as sanitizers

        if not sanitizers.HAS_BLEACH:
            self.skipTest("bleach not installed")
        user = UserFactory(username="san-user", roles=["employee"])
        schema = make_schema(
            slug="san-form",
            fields=[
                {"key": "bio", "type": "rich_text", "order": 1},
                {"key": "name", "type": "text", "order": 2},
            ],
        )
        submission = service.create_submission(
            schema=schema,
            user=user,
            data={"bio": '<b>سلام</b><script>alert(1)</script>', "name": "علی\x00"},
        )
        self.assertNotIn("<script>", submission.data["bio"])
        self.assertIn("<b>سلام</b>", submission.data["bio"])
        self.assertNotIn("\x00", submission.data["name"])

    @override_settings(FORMS_ALLOW_SECURITY_FALLBACKS=False)
    def test_rich_text_fails_closed_without_bleach(self):
        import apps.forms.sanitizers as sanitizers

        user = UserFactory(username="san-user2", roles=["employee"])
        schema = make_schema(
            slug="san-form2",
            fields=[{"key": "bio", "type": "rich_text", "order": 1}],
        )
        with patch.object(sanitizers, "HAS_BLEACH", False):
            with self.assertRaises(FormServiceError):
                service.create_submission(
                    schema=schema, user=user, data={"bio": "<b>x</b>"}
                )


class VisibilityDerivationTests(TestCase):
    def test_class_group_and_person_extracted(self):
        schema = make_schema(
            slug="dv-form",
            metadata={"subject_field": "student"},
            fields=[
                {"key": "class_group", "type": "relation", "order": 1,
                 "relation": {"registry_key": "academic.class_group"}},
                {"key": "student", "type": "relation", "order": 2,
                 "relation": {"registry_key": "persons.person"}},
            ],
        )
        group = make_class_group()
        person = make_person(None, "student")
        visibility = derive_visibility(schema, {
            "class_group": str(group.pk), "student": str(person.pk),
        })
        self.assertEqual(visibility["class_group_id"], str(group.pk))
        self.assertEqual(visibility["subject_person_id"], str(person.pk))

    def test_subject_person_requires_explicit_metadata(self):
        """Without metadata.subject_field, a person relation is NOT treated as
        the subject — multi-row forms must not leak via one arbitrary row."""
        schema = make_schema(
            slug="dv-form2",
            fields=[
                {"key": "student", "type": "relation", "order": 1,
                 "relation": {"registry_key": "persons.person"}},
            ],
        )
        person = make_person(None, "student")
        visibility = derive_visibility(schema, {"student": str(person.pk)})
        self.assertIsNone(visibility["subject_person_id"])


class SensitiveAccessLoggingTests(TestCase):
    def test_sensitive_read_is_logged_with_actor_and_ip(self):
        from types import SimpleNamespace

        user = UserFactory(username="log-user", roles=["manager"])
        schema = make_schema(slug="grade-report")
        submission = service.create_submission(schema=schema, user=user, data={})

        request = SimpleNamespace(META={"REMOTE_ADDR": "10.1.2.3"}, user=user)

        with self.assertLogs("apps.forms.services", level="INFO") as captured:
            log_sensitive_access(request, submission, allowed=True)
        line = " ".join(captured.output)
        self.assertIn("log-user", line)
        self.assertIn("10.1.2.3", line)
        self.assertIn("grade-report", line)
        self.assertIn(str(submission.pk), line)
        self.assertIn("allowed=True", line)


class DraftImmutabilityServiceTests(TestCase):
    def test_update_rejected_after_submit(self):
        user = UserFactory(username="im-user", roles=["employee"])
        schema = make_schema(
            slug="im-form",
            fields=[{"key": "note", "type": "text", "order": 1, "max_length": 50}],
        )
        submission = service.create_submission(schema=schema, user=user, data={})
        service.submit_submission(submission=submission, user=user)
        with self.assertRaises(FormServiceError):
            service.update_submission(
                submission=submission, user=user, data={}
            )

    def test_only_submitter_can_submit(self):
        owner = UserFactory(username="im-owner", roles=["employee"])
        stranger = UserFactory(username="im-stranger", roles=["employee"])
        schema = make_schema(
            slug="im-form2",
            fields=[{"key": "note", "type": "text", "order": 1, "max_length": 50}],
        )
        submission = service.create_submission(schema=schema, user=owner, data={})
        with self.assertRaises(FormServiceError):
            service.submit_submission(submission=submission, user=stranger)


class SystemCheckTests(TestCase):
    @override_settings(FORMS_ALLOW_SECURITY_FALLBACKS=False)
    def test_missing_dependencies_raise_errors(self):
        import apps.forms.checks as checks_module

        with patch.object(checks_module, "HAS_BLEACH", False), \
             patch.object(checks_module, "HAS_MAGIC", False):
            errors = checks_module.check_forms_security_dependencies(None)
        ids = {e.id for e in errors}
        self.assertIn("forms.E001", ids)
        self.assertIn("forms.E002", ids)

    @override_settings(FORMS_ALLOW_SECURITY_FALLBACKS=True)
    def test_fallback_flag_downgrades_to_warnings(self):
        import apps.forms.checks as checks_module

        with patch.object(checks_module, "HAS_BLEACH", False), \
             patch.object(checks_module, "HAS_MAGIC", False):
            results = checks_module.check_forms_security_dependencies(None)
        ids = {w.id for w in results}
        self.assertIn("forms.W001", ids)
        self.assertIn("forms.W002", ids)
        self.assertNotIn("forms.E001", ids)

    def test_installed_dependencies_pass(self):
        import apps.forms.checks as checks_module

        if not checks_module.HAS_BLEACH or not checks_module.HAS_MAGIC:
            self.skipTest("security libs not installed in this environment")
        results = checks_module.check_forms_security_dependencies(None)
        self.assertEqual(
            [r for r in results if r.id in {"forms.E001", "forms.E002"}], []
        )


class TeacherEnrollmentScopeTests(TestCase):
    def test_teacher_visibility_uses_enrolled_students_group(self):
        teacher = UserFactory(username="sc-teacher", roles=["teacher"])
        teacher_person = make_person(teacher, "teacher")
        group = make_class_group(teacher=teacher_person)
        student = UserFactory(username="sc-student", roles=["student"])
        student_person = make_person(student, "student")
        make_enrollment(group, student_person)

        schema = make_schema(slug="sc-form")
        submission = service.create_submission(
            schema=schema, user=UserFactory(username="sc-any", roles=["employee"]), data={},
        )
        submission.class_group = group
        submission.save(update_fields=["class_group"])

        from apps.forms.permissions import visible_submissions_for

        self.assertTrue(visible_submissions_for(teacher).filter(pk=submission.pk).exists())
        self.assertTrue(visible_submissions_for(student).filter(
            pk=FormSubmission.objects.get(pk=submission.pk).pk
        ).exists() is False)  # student sees only subject_person rows
