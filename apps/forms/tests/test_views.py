"""REST API tests: auth, isolation, immutability, files, throttling, seeding."""
from __future__ import annotations

import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.forms.services import FormSubmissionService
from apps.forms.tests.factories import (
    UserFactory,
    make_schema,
)

service = FormSubmissionService()

# Test settings: allow the fallback sniffers so file tests run without
# libmagic, and tighten the upload size for the size-limit test.
FILE_SETTINGS = {
    "FORMS_ALLOW_SECURITY_FALLBACKS": True,
    "FORMS_MAX_UPLOAD_SIZE": 1024,
}


def _png_bytes() -> bytes:
    # A real, CRC-valid 1×1 PNG — installed libmagic sniffs content, so a
    # header-only fake would be classified as octet-stream and rejected.
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0bIDATx\xdac`\x00"
        b"\x02\x00\x00\x05\x00\x01\xe9\xfa\xdc\xd8\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def _pdf_bytes() -> bytes:
    return b"%PDF-1.4 fake pdf body" + b"\x00" * 50


class AuthenticatedAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def _login(self, user):
        # Grant the forms model permissions so the group-permission layer
        # (HasGroupPermission) is satisfied; these tests exercise ROLE and
        # OBJECT-level authorization, not Django model perms.
        grant_forms_model_perms(user)
        self.client.force_authenticate(user=user)


def grant_forms_model_perms(user):
    """Assign every forms model permission to ``user``."""
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    from apps.forms import models as forms_models

    perms = []
    for model in (forms_models.FormSchema, forms_models.FormSubmission,
                  forms_models.FormAttachment, forms_models.FormComment):
        perms += Permission.objects.filter(content_type=ContentType.objects.get_for_model(model))
    user.user_permissions.set(perms)
    # Related-manager caches live on the instance; grant before first check.
    for attr in ("_user_perm_cache", "_group_perm_cache", "_perm_cache"):
        if hasattr(user, attr):
            delattr(user, attr)


class SchemaAPITests(AuthenticatedAPITestCase):
    def test_schemas_list_requires_authentication(self):
        response = self.client.get("/api/forms/schemas/")
        self.assertIn(response.status_code, (401, 403))

    def test_schema_detail_by_slug(self):
        user = UserFactory(username="sa-user", roles=["employee"])
        schema = make_schema(slug="detail-form")
        self._login(user)
        response = self.client.get(f"/api/forms/schemas/{schema.slug}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["slug"], "detail-form")

    def test_schema_admin_requires_elevated_role(self):
        employee = UserFactory(username="sa-emp", roles=["employee"])
        manager = UserFactory(username="sa-mgr", roles=["manager"])
        fields = [{"key": "a", "type": "text", "order": 1}]
        self._login(employee)
        response = self.client.post(
            "/api/forms/admin/schemas/",
            {"slug": "new-form", "title": "فرم", "fields": fields}, format="json",
        )
        self.assertEqual(response.status_code, 403)
        self._login(manager)
        response = self.client.post(
            "/api/forms/admin/schemas/",
            {"slug": "new-form", "title": "فرم", "fields": fields}, format="json",
        )
        self.assertEqual(response.status_code, 201)


class SubmissionAPITests(AuthenticatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory(username="api-user", roles=["employee"])
        self.schema = make_schema(
            slug="api-form",
            fields=[
                {"key": "title", "type": "text", "order": 1, "required": True, "max_length": 100},
                {"key": "count", "type": "number", "order": 2, "min": 0, "max": 10},
            ],
        )

    def test_create_returns_field_keyed_errors(self):
        # Draft mode: invalid VALUES are rejected (count out of range), but a
        # missing required field is allowed — requiredness is enforced at submit.
        self._login(self.user)
        response = self.client.post(
            "/api/forms/submissions/",
            {"schema_slug": "api-form", "data": {"count": 99}}, format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("count", response.data)

    def test_missing_required_allowed_in_draft_rejected_at_submit(self):
        self._login(self.user)
        response = self.client.post(
            "/api/forms/submissions/",
            {"schema_slug": "api-form", "data": {"count": 3}}, format="json",
        )
        self.assertEqual(response.status_code, 201)  # draft: title missing is OK
        submit = self.client.post(
            f"/api/forms/submissions/{response.data['id']}/submit/", format="json",
        )
        self.assertEqual(submit.status_code, 400)
        self.assertIn("title", submit.data)

    def test_create_draft_with_valid_data(self):
        self._login(self.user)
        response = self.client.post(
            "/api/forms/submissions/",
            {"schema_slug": "api-form", "data": {"title": "عنوان", "count": 3}},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "draft")
        self.assertTrue(response.data["submission_number"].startswith("FORM-API-FORM-"))

    def test_submitter_is_never_client_controlled(self):
        other = UserFactory(username="api-other", roles=["employee"])
        self._login(self.user)
        response = self.client.post(
            "/api/forms/submissions/",
            {"schema_slug": "api-form", "data": {"title": "x"},
             "submitted_by": str(other.pk)},
            format="json",
        )
        # The serializer has no submitted_by field at all — the value is
        # ignored and the draft belongs to the authenticated user.
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["submitter_username"], self.user.username)

    def test_submission_list_is_scoped_to_submitter(self):
        mine = service.create_submission(schema=self.schema, user=self.user, data={"title": "من"})
        other_user = UserFactory(username="api-stranger", roles=["employee"])
        theirs = service.create_submission(schema=self.schema, user=other_user, data={"title": "او"})
        self._login(self.user)
        response = self.client.get("/api/forms/submissions/")
        ids = [row["id"] for row in response.data["results"]] if isinstance(
            response.data, dict
        ) else [row["id"] for row in response.data]
        self.assertIn(str(mine.pk), ids)
        self.assertNotIn(str(theirs.pk), ids)

    def test_patch_on_submitted_is_409(self):
        submission = service.create_submission(
            schema=self.schema, user=self.user, data={"title": "پیش‌نویس"}
        )
        submission = service.submit_submission(submission=submission, user=self.user)
        self._login(self.user)
        response = self.client.patch(
            f"/api/forms/submissions/{submission.pk}/",
            {"data": {"title": "تغییر"}}, format="json",
        )
        self.assertEqual(response.status_code, 409)

    def test_patch_draft_revalidates(self):
        submission = service.create_submission(
            schema=self.schema, user=self.user, data={"title": "پیش‌نویس"}
        )
        self._login(self.user)
        # Draft mode allows empty required fields, so invalid VALUES must fail:
        # title exceeds max_length(100) and count exceeds max(10).
        response = self.client.patch(
            f"/api/forms/submissions/{submission.pk}/",
            {"data": {"title": "ل" * 200, "count": 500}}, format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("title", response.data)
        self.assertIn("count", response.data)

    def test_other_user_cannot_patch_my_draft(self):
        mine = service.create_submission(schema=self.schema, user=self.user, data={"title": "من"})
        stranger = UserFactory(username="api-thief", roles=["employee"])
        self._login(stranger)
        response = self.client.patch(
            f"/api/forms/submissions/{mine.pk}/", {"data": {"title": "دزدی"}}, format="json",
        )
        self.assertIn(response.status_code, (403, 404))

    def test_other_user_cannot_submit_my_draft(self):
        mine = service.create_submission(schema=self.schema, user=self.user, data={"title": "من"})
        stranger = UserFactory(username="api-thief2", roles=["employee"])
        self._login(stranger)
        response = self.client.post(f"/api/forms/submissions/{mine.pk}/submit/", {})
        self.assertEqual(response.status_code, 404)

    def test_submit_twice_conflicts(self):
        submission = service.create_submission(
            schema=self.schema, user=self.user, data={"title": "اول"}
        )
        self._login(self.user)
        first = self.client.post(f"/api/forms/submissions/{submission.pk}/submit/", {})
        self.assertEqual(first.status_code, 200)
        second = self.client.post(f"/api/forms/submissions/{submission.pk}/submit/", {})
        self.assertEqual(second.status_code, 409)

    def test_idempotency_key_prevents_duplicate_create(self):
        self._login(self.user)
        payload = {"schema_slug": "api-form", "data": {"title": "تکراری"}}
        headers = {"HTTP_IDEMPOTENCY_KEY": "same-key-123"}
        first = self.client.post("/api/forms/submissions/", payload, format="json", **headers)
        self.assertEqual(first.status_code, 201)
        second = self.client.post("/api/forms/submissions/", payload, format="json", **headers)
        self.assertEqual(second.status_code, 409)

    def test_inactive_schema_cannot_receive_submissions(self):
        make_schema(slug="closed-form", is_active=False)
        self._login(self.user)
        response = self.client.post(
            "/api/forms/submissions/",
            {"schema_slug": "closed-form", "data": {}}, format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_status_field_never_client_controlled(self):
        self._login(self.user)
        response = self.client.post(
            "/api/forms/submissions/",
            {"schema_slug": "api-form", "data": {"title": "x"}, "status": "approved"},
            format="json",
        )
        self.assertIn(response.status_code, (201, 400))
        if response.status_code == 201:
            self.assertEqual(response.data["status"], "draft")


class CommentAPITests(AuthenticatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.schema = make_schema(slug="cmt-api")
        self.author = UserFactory(username="cmt-author", roles=["employee"])
        self.submission = service.create_submission(
            schema=self.schema, user=self.author, data={}
        )
        self.manager = UserFactory(username="cmt-manager", roles=["manager"])
        self.student = UserFactory(username="cmt-student", roles=["student"])

    def test_any_visible_viewer_can_comment(self):
        self._login(self.manager)
        response = self.client.post(
            f"/api/forms/submissions/{self.submission.pk}/comments/",
            {"body": "بررسی شد"}, format="json",
        )
        self.assertEqual(response.status_code, 201)

    def test_student_cannot_see_unrelated_submission_comments(self):
        self._login(self.student)
        response = self.client.get(
            f"/api/forms/submissions/{self.submission.pk}/comments/",
        )
        self.assertEqual(response.status_code, 404)

    def test_internal_comment_hidden_from_non_staff(self):
        service.add_comment(
            submission=self.submission, author=self.manager,
            body="یادداشت داخلی", is_internal=True,
        )
        service.add_comment(
            submission=self.submission, author=self.manager, body="عمومی",
        )
        self._login(self.author)  # plain employee, not staff-side
        response = self.client.get(
            f"/api/forms/submissions/{self.submission.pk}/comments/",
        )
        bodies = [c["body"] for c in response.data["results"]] if isinstance(
            response.data, dict
        ) else [c["body"] for c in response.data]
        self.assertIn("عمومی", bodies)
        self.assertNotIn("یادداشت داخلی", bodies)
        # Manager sees both.
        self._login(self.manager)
        response = self.client.get(
            f"/api/forms/submissions/{self.submission.pk}/comments/",
        )
        bodies = [c["body"] for c in response.data["results"]] if isinstance(
            response.data, dict
        ) else [c["body"] for c in response.data]
        self.assertIn("یادداشت داخلی", bodies)

    def test_non_staff_cannot_flag_internal(self):
        self._login(self.author)
        response = self.client.post(
            f"/api/forms/submissions/{self.submission.pk}/comments/",
            {"body": "تلاش داخلی", "is_internal": True}, format="json",
        )
        self.assertEqual(response.status_code, 403)


class AttachmentAPITests(AuthenticatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory(username="file-user", roles=["employee"])
        self.other = UserFactory(username="file-other", roles=["employee"])
        self.schema = make_schema(
            slug="file-form",
            fields=[{"key": "doc", "type": "file", "order": 1}],
        )
        self.submission = service.create_submission(schema=self.schema, user=self.user, data={})

    def _upload(self, user, content, name="doc.png", submission=None):
        submission = submission or self.submission
        self._login(user)
        upload = SimpleUploadedFile(name, content, content_type="image/png")
        return self.client.post(
            f"/api/forms/submissions/{submission.pk}/attachments/",
            {"field_key": "doc", "file": upload}, format="multipart",
        )

    @override_settings(**FILE_SETTINGS)
    def test_upload_valid_png(self):
        response = self._upload(self.user, _png_bytes())
        self.assertEqual(response.status_code, 201)
        self.assertNotIn("file", response.data)  # storage path never exposed
        self.assertTrue(response.data["checksum"].startswith("sha256:"))

    @override_settings(**FILE_SETTINGS)
    def test_mime_spoofing_rejected(self):
        # PNG extension + PDF content → rejected by consistency check.
        response = self._upload(self.user, _pdf_bytes(), name="doc.png")
        self.assertEqual(response.status_code, 400)

    @override_settings(**FILE_SETTINGS)
    def test_extension_allowlist(self):
        response = self._upload(self.user, _png_bytes(), name="evil.exe")
        self.assertEqual(response.status_code, 400)

    @override_settings(**FILE_SETTINGS)
    def test_size_limit(self):
        response = self._upload(self.user, b"x" * 2048, name="big.png")
        self.assertEqual(response.status_code, 400)

    def test_upload_requires_field_on_schema(self):
        self._login(self.user)
        upload = SimpleUploadedFile("x.png", _png_bytes(), content_type="image/png")
        response = self.client.post(
            f"/api/forms/submissions/{self.submission.pk}/attachments/",
            {"field_key": "not_a_field", "file": upload}, format="multipart",
        )
        self.assertEqual(response.status_code, 400)

    @override_settings(**FILE_SETTINGS)
    def test_download_requires_visibility(self):
        attachment = self._upload(self.user, _png_bytes()).data
        self._login(self.other)
        response = self.client.get(
            f"/api/forms/attachments/{attachment['id']}/download/",
        )
        self.assertEqual(response.status_code, 404)

    @override_settings(**FILE_SETTINGS)
    def test_download_streams_content_disposition(self):
        attachment = self._upload(self.user, _png_bytes()).data
        self._login(self.user)
        response = self.client.get(
            f"/api/forms/attachments/{attachment['id']}/download/",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertNotIn("/", response["Content-Disposition"].split('"')[1])

    def test_file_reference_validated_against_submission(self):
        # Data referencing a non-existent attachment id must fail validation.
        self._login(self.user)
        response = self.client.patch(
            f"/api/forms/submissions/{self.submission.pk}/",
            {"data": {"doc": "11111111-1111-1111-1111-111111111111"}}, format="json",
        )
        self.assertEqual(response.status_code, 400)


class ThrottleTests(AuthenticatedAPITestCase):
    def test_form_write_throttle_enforced(self):
        # Patch the class-level ``rate`` (read by SimpleRateThrottle.__init__)
        # rather than THROTTLE_RATES: depending on DRF version, get_rate() may
        # read api_settings.DEFAULT_THROTTLE_RATES directly and ignore a
        # class-attribute patch.
        from unittest.mock import patch

        from django.core.cache import cache

        import apps.forms.throttles as throttles_module

        cache.clear()
        user = UserFactory(username="thr-user", roles=["employee"])
        make_schema(
            slug="thr-form",
            fields=[{"key": "note", "type": "text", "order": 1, "max_length": 50}],
        )
        self._login(user)
        # Patch get_rate() (called by SimpleRateThrottle.__init__) so the
        # effective limit is 3/min regardless of how DRF resolves the scope.
        with patch.object(throttles_module.FormWriteThrottle, "get_rate",
                          lambda self: "3/minute"):
            codes = []
            for _ in range(5):
                response = self.client.post(
                    "/api/forms/submissions/",
                    {"schema_slug": "thr-form", "data": {}}, format="json",
                )
                codes.append(response.status_code)
        self.assertEqual(codes[:3], [201, 201, 201], codes)
        self.assertEqual(codes.count(429), 2, codes)  # first 3 pass, then throttled

    def test_get_is_not_throttled_by_form_write(self):
        user = UserFactory(username="thr-user2", roles=["employee"])
        make_schema(slug="thr-read")
        self._login(user)
        for _ in range(10):
            response = self.client.get("/api/forms/submissions/")
            self.assertEqual(response.status_code, 200)


class SeedCommandTests(TestCase):
    def _call(self, *args):
        from django.core.management import call_command
        from django.core.management.base import CommandError
        import io

        out = io.StringIO()
        try:
            call_command("seed_form_schemas", *args, stdout=out)
            return out.getvalue(), None
        except CommandError as exc:
            return out.getvalue(), exc

    def _seed_roles(self, *codes):
        from apps.accounts.models import Role

        for code in codes:
            Role.objects.get_or_create(code=code, defaults={"name": code})

    def _seed_workflows(self):
        # seed_form_workflows itself requires the role codes its blueprints
        # reference — seed roles first.
        from django.core.management import call_command
        import io

        self._seed_roles("employee", "hr", "manager", "workflow_admin", "teacher")
        call_command("seed_form_workflows", stdout=io.StringIO())

    def test_unavailable_required_relations_abort_before_writing(self):
        # attendance is fully seedable; lesson needs education.Lesson (planned
        # app). The all-or-nothing contract must abort the WHOLE run because
        # ONE schema has an unavailable required relation — and write nothing.
        from apps.forms.models import FormSchema

        before = FormSchema.objects.count()
        _, error = self._call("attendance", "lesson")
        self.assertIsNotNone(error)
        self.assertIn("education.Lesson", str(error))
        self.assertIn("lesson", str(error))
        # Zero database changes: the valid `attendance` schema must NOT be
        # partially committed alongside the failed one.
        self.assertEqual(FormSchema.objects.count(), before)

    def test_attendance_and_grade_report_seed(self):
        from apps.forms.models import FormSchema

        self._seed_workflows()
        out, error = self._call("attendance", "grade-report")
        self.assertIsNone(error)
        self.assertTrue(FormSchema.objects.filter(slug="attendance").exists())
        self.assertTrue(FormSchema.objects.filter(slug="grade-report").exists())
        # Workflow definitions are wired to the schemas.
        self.assertIsNotNone(
            FormSchema.objects.get(slug="attendance").workflow_definition
        )
        self.assertEqual(
            FormSchema.objects.get(slug="grade-report").workflow_definition.code,
            "form-review",
        )

    def test_seeding_is_idempotent(self):
        from apps.forms.models import FormSchema

        self._seed_workflows()
        self._call("attendance")
        self._call("attendance")
        self.assertEqual(FormSchema.objects.filter(slug="attendance", version=1).count(), 1)

    def test_dry_run_writes_nothing(self):
        from apps.forms.models import FormSchema

        self._seed_workflows()
        out, error = self._call("--dry-run", "attendance")
        self.assertIsNone(error)
        self.assertIn("dry-run", out)
        self.assertEqual(FormSchema.objects.count(), 0)

    def test_unknown_slug_rejected(self):
        _, error = self._call("nope")
        self.assertIsNotNone(error)
        self.assertIn("nope", str(error))

    def test_missing_roles_abort(self):
        # No roles seeded at all → the roles check fires first.
        _, error = self._call("attendance")
        self.assertIsNotNone(error)
        self.assertIn("seed_roles", str(error))

    def test_missing_workflow_definitions_abort(self):
        from apps.forms.models import FormSchema

        self._seed_roles("teacher", "manager")
        before = FormSchema.objects.count()
        _, error = self._call("attendance")
        self.assertIsNotNone(error)
        self.assertIn("seed_form_workflows", str(error))
        self.assertEqual(FormSchema.objects.count(), before)


class WorkflowSeedCommandTests(TestCase):
    def test_workflows_seed_and_are_idempotent(self):
        from apps.accounts.models import Role
        from django.core.management import call_command
        from apps.workflow.models import Transition, WorkflowDefinition

        for code in ("employee", "hr", "manager", "workflow_admin", "teacher"):
            Role.objects.get_or_create(code=code, defaults={"name": code})
        call_command("seed_form_workflows", stdout=io.StringIO())
        call_command("seed_form_workflows", stdout=io.StringIO())

        self.assertEqual(WorkflowDefinition.objects.filter(code="lead-assessment").count(), 1)
        definition = WorkflowDefinition.objects.get(code="lead-assessment")
        self.assertEqual(
            set(definition.states.values_list("code", flat=True)),
            {"new", "assessed", "enrolled", "closed"},
        )
        # Exactly the spec transitions: new→assessed, assessed→enrolled/closed.
        self.assertEqual(Transition.objects.filter(workflow_definition=definition).count(), 3)

    def test_workflows_dry_run_writes_nothing(self):
        from apps.accounts.models import Role
        from django.core.management import call_command
        from apps.workflow.models import WorkflowDefinition

        for code in ("employee", "manager", "teacher", "hr", "workflow_admin"):
            Role.objects.get_or_create(code=code, defaults={"name": code})
        call_command("seed_form_workflows", "--dry-run", stdout=io.StringIO())
        self.assertEqual(WorkflowDefinition.objects.count(), 0)

    def test_workflows_missing_roles_abort(self):
        from django.core.management import call_command
        from django.core.management.base import CommandError
        from apps.workflow.models import WorkflowDefinition

        with self.assertRaises(CommandError) as ctx:
            call_command("seed_form_workflows", stdout=io.StringIO())
        self.assertIn("seed_roles", str(ctx.exception))
        self.assertEqual(WorkflowDefinition.objects.count(), 0)
