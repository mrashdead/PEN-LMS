"""Five-level test pyramid over the workflow engine + dynamic forms.

Run everything:

    python manage.py test apps.core.tests_pyramid

Levels (one TestCase class per level):

  L1  UnitTests          — tiny pieces, no HTTP: validator, guard, model rules.
  L2  IntegrationTests   — several components wired: service↔engine↔tasks↔outbox,
                           form submit↔workflow instance, DB guards.
  L3  FunctionalTests    — one FEATURE through its public API: draft a seeded
                           form → submit → advance → approve; schema versioning.
  L4  EndToEndTests      — a full USER PATH through session pages + REST API
                           exactly as the browser drives them.
  L5  RegressionTests    — invariants that must never break again (double
                           submit, double approve, replay keys, projection
                           idempotency, PII masking, role isolation).

Real contracts these tests honor (verified against the engine):
  - form workflows are 3-state: new → pending-manager → done. Forms "submit"
    creates the instance in `new`; the `submit` TRANSITION must then be
    executed before `approve` is offered.
  - notifications are enqueued ONLY by transitions (never by create_instance).
  - approve/reject are terminal in the seeded blueprints (both go to `done`).
"""
from __future__ import annotations

import io
import uuid

from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from apps.forms.models import FormSchema, FormSubmission
from apps.forms.services import FormSubmissionService
from apps.forms.tests.factories import (
    UserFactory,
    make_class_group,
    make_enrollment,
    make_person,
    make_schema,
)
from apps.workflow.models import (
    ActionLog,
    ApprovalRecord,
    Instance,
    NotificationOutbox,
    State,
    Transition,
    WorkflowDefinition,
)

service = FormSubmissionService()

#: 10-digit national codes (the real format) so mask_identifier produces the
#: expected 3-prefix + 5-star + 2-suffix shape in the PII regression test.
_nc = iter(range(3000000000, 3999999999))


def next_nc() -> str:
    return str(next(_nc))


def seed_role_codes(*codes):
    from apps.accounts.models import Role

    for code in codes:
        Role.objects.get_or_create(code=code, defaults={"name": code, "priority": 50})


def seed_form_workflows():
    call_command("seed_form_workflows", stdout=io.StringIO())


def seed_schemas(*slugs):
    call_command("seed_form_schemas", *slugs, stdout=io.StringIO())


def approval_wf(code="wf-plain"):
    """Minimal 2-state new→done workflow (engine-level tests)."""
    definition, _ = WorkflowDefinition.objects.get_or_create(
        code=code, defaults={"name": "تایید ساده", "is_active": True, "version": 1},
    )
    initial, _ = State.objects.get_or_create(
        workflow_definition=definition, code="new",
        defaults={"name": "جدید", "is_initial": True, "is_final": False},
    )
    final, _ = State.objects.get_or_create(
        workflow_definition=definition, code="done",
        defaults={"name": "پایان", "is_initial": False, "is_final": True},
    )
    transition, _ = Transition.objects.get_or_create(
        workflow_definition=definition, from_state=initial, to_state=final,
        name="approve",
        defaults={"allowed_role_codes": ["manager"], "kind": "approve",
                  "guard_expression": {}},
    )
    return definition, initial, final, transition


def grant_model_perms(user, *models, exclude=()):
    """Grant model perms for StrictDjangoModelPermissions/HasGroupPermission."""
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    perms = []
    for m in models:
        qs = Permission.objects.filter(
            content_type=ContentType.objects.get_for_model(m))
        if exclude:
            qs = qs.exclude(codename__in=exclude)
        perms += list(qs)
    user.user_permissions.set(perms)
    for attr in ("_user_perm_cache", "_group_perm_cache", "_perm_cache"):
        if hasattr(user, attr):
            delattr(user, attr)


def grant_forms_perms(user):
    from apps.forms import models as f_models

    grant_model_perms(
        user, f_models.FormSchema, f_models.FormSubmission,
        f_models.FormAttachment, f_models.FormComment,
    )


def grant_tasks_perms(user):
    from apps.tasks.models import WorkflowTask

    grant_model_perms(user, WorkflowTask)


def _engine():
    from apps.workflow.services import WorkflowEngineService

    return WorkflowEngineService()


def _plain_instance(wf, requester):
    return _engine().create_instance(
        workflow_code=wf.code, requester=requester, title="ت",
    )


# ═════════════════════════════════════════════════════════════════════════════
# L1 — UNIT: smallest pieces, no HTTP, no cross-app flows
# ═════════════════════════════════════════════════════════════════════════════

class UnitTests(TestCase):
    """🧩 Unit — validator/guard/model rules in isolation."""

    def setUp(self):
        seed_role_codes("manager", "employee")

    def _validate(self, instance, transition, actor):
        from apps.workflow.validators import TransitionValidator

        return TransitionValidator().validate(instance, transition, actor)

    def test_validator_rejects_wrong_state(self):
        employee = UserFactory(username="u1", roles=["employee"])
        manager = UserFactory(username="u2", roles=["manager"])
        wf, initial, final, t = approval_wf("unit-wf")
        instance = _plain_instance(wf, employee)
        instance.current_state = final  # simulate already-terminal state
        result = self._validate(instance, t, manager)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("وضعیت جاری" in e or "وضعیت" in e for e in result.errors))

    def test_validator_rejects_missing_role(self):
        employee = UserFactory(username="u3", roles=["employee"])
        wf, *_rest = approval_wf("unit-wf2")
        instance = _plain_instance(wf, employee)
        t = Transition.objects.get(workflow_definition=wf, name="approve")
        result = self._validate(instance, t, employee)  # employee ≠ manager
        self.assertFalse(result.is_valid)
        self.assertTrue(any("نقش" in e for e in result.errors))

    def test_validator_accepts_authorized_actor(self):
        employee = UserFactory(username="u3b", roles=["employee"])
        manager = UserFactory(username="u3c", roles=["manager"])
        wf, *_rest = approval_wf("unit-wf2b")
        instance = _plain_instance(wf, employee)
        t = Transition.objects.get(workflow_definition=wf, name="approve")
        self.assertTrue(self._validate(instance, t, manager).is_valid)

    def test_unknown_guard_fails_closed(self):
        from apps.workflow.guards import GuardEvaluator

        ok, msg = GuardEvaluator().evaluate(
            guard={"type": "nonexistent_kind_xyz"}, instance=None, actor=None,
        )
        self.assertFalse(ok)
        self.assertTrue(msg)

    def test_transition_cannot_reference_foreign_states(self):
        from django.core.exceptions import ValidationError

        other_wf = WorkflowDefinition.objects.create(code="other-wf", name="دیگر")
        s1 = State.objects.create(
            workflow_definition=other_wf, code="a", name="a", is_initial=True,
        )
        s2 = State.objects.create(workflow_definition=other_wf, code="b", name="b")
        wf, *_ = approval_wf("unit-wf3")
        with self.assertRaises(ValidationError):
            Transition(
                workflow_definition=wf, from_state=s1, to_state=s2, name="jump",
            ).clean()

    def test_submission_number_shape_and_monotonicity(self):
        from apps.forms.models import SubmissionSequence
        from apps.forms.services import next_submission_number

        schema = make_schema(slug="num-form")
        n1 = next_submission_number(schema)
        n2 = next_submission_number(schema)
        self.assertTrue(n1.startswith("FORM-NUM-FORM-"))
        self.assertNotEqual(n1, n2)
        seq = SubmissionSequence.objects.get(slug="num-form")
        self.assertGreaterEqual(seq.last_value, 2)

    def test_state_cannot_be_initial_and_final(self):
        from django.core.exceptions import ValidationError

        wf = WorkflowDefinition.objects.create(code="unit-st", name="s")
        with self.assertRaises(ValidationError):
            State(
                workflow_definition=wf, code="both", name="همه",
                is_initial=True, is_final=True,
            ).clean()


# ═════════════════════════════════════════════════════════════════════════════
# L2 — INTEGRATION: services + engine + tasks + outbox wired together
# ═════════════════════════════════════════════════════════════════════════════

class IntegrationTests(TestCase):
    """🔗 Integration — components cooperating, exercised at service level."""

    def setUp(self):
        seed_role_codes("manager", "employee", "teacher")

    def _simple_schema(self, workflow_definition):
        return make_schema(
            slug=f"int-{uuid.uuid4().hex[:8]}",
            workflow_definition=workflow_definition,
            fields=[{"key": "title", "type": "text", "order": 1,
                     "required": True, "label": "عنوان", "max_length": 100}],
        )

    def test_form_submit_spawns_engine_instance_and_link(self):
        employee = UserFactory(username="i1", roles=["employee"])
        wf, *_ = approval_wf("int-wf")
        schema = self._simple_schema(wf)
        draft = service.create_submission(
            schema=schema, user=employee, data={"title": "درخواست"},
        )
        submitted = service.submit_submission(submission=draft, user=employee)
        self.assertIsNotNone(submitted.workflow_instance)
        self.assertEqual(submitted.status, FormSubmission.Status.SUBMITTED)
        # Entity link registered so guards can resolve the payload entity.
        link = submitted.workflow_instance.entity_links.first()
        self.assertEqual(str(link.object_id), str(submitted.pk))
        # Engine logged creation.
        self.assertTrue(ActionLog.objects.filter(
            instance=submitted.workflow_instance, action="create",
        ).exists())

    def test_approve_writes_approval_record_and_syncs_status(self):
        employee = UserFactory(username="i2", roles=["employee"])
        manager = UserFactory(username="i3", roles=["manager"])
        wf, *_ = approval_wf("int-wf2")
        schema = self._simple_schema(wf)
        submitted = service.submit_submission(
            submission=service.create_submission(
                schema=schema, user=employee, data={"title": "درخواست"},
            ),
            user=employee,
        )
        instance = submitted.workflow_instance
        t = Transition.objects.get(workflow_definition=wf, name="approve")
        _engine().execute_transition(
            instance_id=instance.pk, transition_id=t.pk, actor=manager,
        )
        synced = service.sync_status_from_workflow(
            FormSubmission.objects.get(pk=submitted.pk), actor=manager,
        )
        self.assertEqual(synced.status, FormSubmission.Status.APPROVED)
        self.assertEqual(synced.reviewed_by, manager)
        record = ApprovalRecord.objects.get(instance=instance)
        self.assertEqual(record.approver, manager)
        self.assertEqual(record.role_code, "manager")

    def test_transition_enqueues_notification_outside_the_transition_tx(self):
        """Engine queues in-app rows for the requester; nothing is 'sent' inline."""
        employee = UserFactory(username="i3b", roles=["employee"])
        manager = UserFactory(username="i3c", roles=["manager"])
        wf, *_ = approval_wf("int-wf2b")
        instance = _plain_instance(wf, employee)
        t = Transition.objects.get(workflow_definition=wf, name="approve")
        _engine().execute_transition(instance.pk, t.pk, manager)
        row = NotificationOutbox.objects.get(recipient=employee)
        self.assertEqual(row.template, "approved")
        self.assertEqual(row.status, NotificationOutbox.Status.PENDING)

    def test_reject_requires_comment_then_succeeds_with_one(self):
        from apps.workflow.services import InvalidTransitionError

        employee = UserFactory(username="i4", roles=["employee"])
        manager = UserFactory(username="i5", roles=["manager"])
        wf = WorkflowDefinition.objects.create(code="int-wf3", name="r")
        s_new = State.objects.create(
            workflow_definition=wf, code="new", name="جدید", is_initial=True,
        )
        s_done = State.objects.create(
            workflow_definition=wf, code="done", name="پایان", is_final=True,
        )
        t = Transition.objects.create(
            workflow_definition=wf, from_state=s_new, to_state=s_done,
            name="reject", allowed_role_codes=["manager"], kind="reject",
            requires_comment=True,
        )
        instance = _plain_instance(wf, employee)
        with self.assertRaises(InvalidTransitionError):
            _engine().execute_transition(instance.pk, t.pk, manager, comment="   ")
        _engine().execute_transition(instance.pk, t.pk, manager, comment="علت رد: ناقص")
        instance.refresh_from_db()
        self.assertEqual(instance.status, Instance.Status.REJECTED)

    def test_task_fanout_targets_only_role_holders(self):
        from apps.tasks.models import WorkflowTask

        employee = UserFactory(username="i6", roles=["employee"])
        manager = UserFactory(username="i7", roles=["manager"])
        teacher = UserFactory(username="i8", roles=["teacher"])
        wf, *_ = approval_wf("int-wf4")
        instance = _plain_instance(wf, employee)
        _engine()._create_tasks_for_state(instance, instance.current_state)
        assignees = set(
            WorkflowTask.objects.filter(
                instance=instance, status=WorkflowTask.Status.PENDING,
            ).values_list("assignee_id", flat=True)
        )
        self.assertEqual(assignees, {manager.pk})

    def test_expired_role_assignment_gets_no_task(self):
        """Time-bound validity flows through to fan-out (§13-1 on the engine)."""
        import datetime

        from apps.accounts.models import Role
        from apps.tasks.models import WorkflowTask

        employee = UserFactory(username="i6b", roles=["employee"])
        lapsed = UserFactory(username="i6c", roles=[])
        role = Role.objects.get(code="manager")
        now = _now()
        lapsed.assign_role(role, valid_from=now - datetime.timedelta(days=10),
                           valid_to=now - datetime.timedelta(days=1))
        wf, *_ = approval_wf("int-wf4b")
        instance = _plain_instance(wf, employee)
        _engine()._create_tasks_for_state(instance, instance.current_state)
        assignees = set(WorkflowTask.objects.filter(
            instance=instance,
        ).values_list("assignee_id", flat=True))
        self.assertNotIn(lapsed.pk, assignees)

    def test_capacity_guard_blocks_final_approval(self):
        """entity_field_lt on the linked offering: full class cannot be approved."""
        from apps.education.models import Course, CourseOffering
        from apps.workflow.services import InvalidTransitionError

        employee = UserFactory(username="i9", roles=["employee"])
        manager = UserFactory(username="i10", roles=["manager"])
        wf = WorkflowDefinition.objects.create(code="int-wf5", name="cap")
        s_new = State.objects.create(
            workflow_definition=wf, code="new", name="جدید", is_initial=True,
        )
        s_done = State.objects.create(
            workflow_definition=wf, code="done", name="پایان", is_final=True,
        )
        t = Transition.objects.create(
            workflow_definition=wf, from_state=s_new, to_state=s_done,
            name="approve", allowed_role_codes=["manager"], kind="approve",
            guard_expression={"type": "entity_field_lt",
                              "field": "enrolled_count", "other_field": "capacity"},
        )
        instance = _plain_instance(wf, employee)
        offering = CourseOffering.objects.create(
            course=Course.objects.create(title="دوره", code="cap-c"),
            capacity=2, enrolled_count=2,  # FULL
        )
        _engine().link_entity(instance_id=instance.pk, entity=offering)
        with self.assertRaises(InvalidTransitionError):
            _engine().execute_transition(instance.pk, t.pk, manager)
        # Free a seat → the same transition now passes.
        offering.refresh_from_db()
        offering.enrolled_count = 1
        offering.save(update_fields=["enrolled_count"])
        _engine().execute_transition(instance.pk, t.pk, manager)
        instance.refresh_from_db()
        self.assertEqual(instance.status, Instance.Status.COMPLETED)

    def test_cancel_closes_all_pending_tasks(self):
        from apps.tasks.models import WorkflowTask

        employee = UserFactory(username="i11", roles=["employee"])
        manager = UserFactory(username="i12", roles=["manager"])
        wf, *_ = approval_wf("int-wf6")
        instance = _plain_instance(wf, employee)
        _engine()._create_tasks_for_state(instance, instance.current_state)
        self.assertTrue(WorkflowTask.objects.filter(
            instance=instance, status=WorkflowTask.Status.PENDING).exists())
        _engine().cancel_instance(instance.pk, employee)
        self.assertFalse(WorkflowTask.objects.filter(
            instance=instance, status=WorkflowTask.Status.PENDING).exists())


def _now():
    from django.utils import timezone

    return timezone.now()


# ═════════════════════════════════════════════════════════════════════════════
# L3 — FUNCTIONAL: one FEATURE through its public API
# ═════════════════════════════════════════════════════════════════════════════

class FunctionalTests(TestCase):
    """⚙️ Functional — a complete feature driven through its REST API."""

    def setUp(self):
        self.client = APIClient()
        seed_role_codes("manager", "employee", "teacher", "hr", "workflow_admin")
        seed_form_workflows()
        seed_schemas("attendance")
        self.teacher = UserFactory(username="f-teacher", roles=["teacher"])
        self.manager = UserFactory(
            username="f-manager", roles=["manager", "workflow_admin"],
        )
        for u in (self.teacher, self.manager):
            grant_forms_perms(u)
        self.teacher_person = make_person(self.teacher, "teacher",
                                          national_code=next_nc())
        self.group = make_class_group(teacher=self.teacher_person)
        self.students = [
            make_person(None, "student", national_code=next_nc()) for _ in range(2)
        ]
        for s in self.students:
            make_enrollment(self.group, s)

    def _payload(self, date="2026-09-08", number=1):
        return {
            "schema_slug": "attendance",
            "data": {
                "class_group": str(self.group.pk),
                "session_date": date,
                "session_number": number,
                "session_start": "08:00",
                "session_end": "09:30",
                "attendance_list": [
                    {"student_id": str(s.pk), "status": "present", "note": ""}
                    for s in self.students
                ],
            },
        }

    def _submit_form(self, client_user):
        """draft + forms-submit through the API (workflow lands in `new`)."""
        self.client.force_login(client_user)
        r = self.client.post("/api/forms/submissions/", self._payload(),
                             format="json")
        self.assertEqual(r.status_code, 201, r.content)
        sid = r.json()["id"]
        r = self.client.post(f"/api/forms/submissions/{sid}/submit/")
        self.assertEqual(r.status_code, 200, r.content)
        return sid

    def _advance_submit_transition(self, sid):
        """new → pending-manager via the transition endpoint (form-review)."""
        t = Transition.objects.get(
            workflow_definition__code="form-review", name="submit",
        )
        r = self.client.post(
            f"/api/forms/submissions/{sid}/transition/",
            {"transition_id": str(t.pk), "comment": "ارسال به مدیر"},
            format="json",
        )
        self.assertEqual(r.status_code, 200, r.content)

    def test_full_attendance_feature_end_to_end_via_api(self):
        from apps.education.models import AttendanceRecord, ClassSession

        sid = self._submit_form(self.teacher)
        # Typed projection happened at submit (B4 closure).
        self.assertEqual(
            ClassSession.objects.filter(
                class_group=self.group, session_date="2026-09-08",
                session_number=1,
            ).count(), 1,
        )
        self.assertEqual(
            AttendanceRecord.objects.filter(
                session__class_group=self.group).count(), 2,
        )
        # Body of sheet is scoped to the class's roster.
        for s in self.students:
            self.assertTrue(AttendanceRecord.objects.filter(
                session__class_group=self.group, student=s).exists())

        # Advance, then the manager's approve closes the loop.
        self._advance_submit_transition(sid)
        self.client.force_login(self.manager)
        r = self.client.post(
            f"/api/forms/submissions/{sid}/approve/",
            {"comment": "بررسی شد"}, format="json",
        )
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.json()["status"], "approved")
        submission = FormSubmission.objects.get(pk=sid)
        self.assertEqual(submission.reviewed_by, self.manager)
        self.assertTrue(ApprovalRecord.objects.filter(
            instance=submission.workflow_instance, approver=self.manager,
        ).exists())

    def test_approve_before_advance_is_unavailable(self):
        """Real contract: approve is NOT offered while the sheet sits in `new`."""
        sid = self._submit_form(self.teacher)
        self.client.force_login(self.manager)
        r = self.client.post(f"/api/forms/submissions/{sid}/approve/",
                             format="json")
        self.assertEqual(r.status_code, 403)  # engine: no such available transition

    def test_schema_versioning_feature(self):
        """Publishing v2 keeps v1 intact; only one active version per slug."""
        self.client.force_login(self.manager)
        base_fields = [
            {"key": "topic", "type": "text", "order": 1, "required": True,
             "label": "موضوع", "max_length": 100},
        ]
        r = self.client.post(
            "/api/forms/admin/schemas/",
            {"slug": "versioned", "title": "فرم نسخه‌دار", "version": 1,
             "fields": base_fields},
            format="json",
        )
        self.assertEqual(r.status_code, 201, r.content)
        v1_id = r.json()["id"]
        # v2 published INACTIVE (activation swap is a separate admin decision).
        r = self.client.post(
            "/api/forms/admin/schemas/",
            {"slug": "versioned", "title": "فرم نسخه‌دار", "version": 2,
             "is_active": False,
             "fields": base_fields + [
                 {"key": "priority", "type": "select", "order": 2,
                  "label": "اولویت", "options": [{"value": "low", "label": "کم"},
                                                 {"value": "high", "label": "زیاد"}]},
             ]},
            format="json",
        )
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(FormSchema.objects.filter(slug="versioned").count(), 2)
        v1 = FormSchema.objects.get(pk=v1_id)
        self.assertEqual(len(v1.fields), 1)          # definition untouched
        self.assertTrue(v1.is_active)
        self.assertEqual(
            FormSchema.objects.filter(slug="versioned", is_active=True).count(), 1,
        )

    def test_validation_feature_rejects_bad_payload_with_zero_writes(self):
        from apps.education.models import AttendanceRecord

        payload = self._payload()
        stranger = make_person(None, "student", national_code=next_nc())
        payload["data"]["attendance_list"].append(
            {"student_id": str(stranger.pk), "status": "present", "note": ""}
        )
        self.client.force_login(self.teacher)
        r = self.client.post("/api/forms/submissions/", payload, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("attendance_list", r.json())
        self.assertFalse(AttendanceRecord.objects.exists())
        self.assertFalse(
            FormSubmission.objects.filter(form_schema__slug="attendance").exists()
        )


# ═════════════════════════════════════════════════════════════════════════════
# L4 — E2E: the USER PATH across session pages + API, like a browser
# ═════════════════════════════════════════════════════════════════════════════

class EndToEndTests(TestCase):
    """🌐 E2E — a person's full journey: login → picker → create → approve."""

    def setUp(self):
        self.client = APIClient()
        seed_role_codes("manager", "employee", "teacher", "student",
                        "hr", "workflow_admin")
        seed_form_workflows()
        seed_schemas("attendance")
        self.teacher = UserFactory(username="e2e-teacher", roles=["teacher"])
        self.manager = UserFactory(
            username="e2e-manager", roles=["manager", "workflow_admin"],
        )
        grant_forms_perms(self.teacher)
        # One combined grant: grant_model_perms uses .set(), so a second call
        # would REPLACE the forms perms — never call it twice on one user.
        from apps.forms import models as f_models
        from apps.tasks.models import WorkflowTask

        grant_model_perms(self.manager, f_models.FormSchema,
                          f_models.FormSubmission, f_models.FormAttachment,
                          f_models.FormComment, WorkflowTask)

    def _login(self, user):
        self.assertTrue(
            self.client.login(username=user.username, password="pass-12345")
        )

    def _teacher_submits_sheet(self, date, number):
        teacher_person = make_person(self.teacher, "teacher",
                                     national_code=next_nc())
        group = make_class_group(teacher=teacher_person)
        student = make_person(None, "student", national_code=next_nc())
        make_enrollment(group, student)
        self._login(self.teacher)
        r = self.client.post("/api/forms/submissions/", {
            "schema_slug": "attendance",
            "data": {
                "class_group": str(group.pk), "session_date": date,
                "session_number": number, "session_start": "08:00",
                "session_end": "09:00",
                "attendance_list": [
                    {"student_id": str(student.pk), "status": "late",
                     "note": "۱۰ دقیقه"},
                ],
            },
        }, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        sid = r.json()["id"]
        r = self.client.post(f"/api/forms/submissions/{sid}/submit/")
        self.assertEqual(r.status_code, 200, r.content)
        return sid

    def test_teacher_journey_pages_and_api(self):
        """The teacher sees the form in the picker and it in their list."""
        sid = self._teacher_submits_sheet("2026-09-15", 1)
        r = self.client.get("/forms/submissions/new/")
        self.assertContains(r, "ثبت حضور و غیاب")        # picker lists seeded form
        r = self.client.get("/forms/submissions/new/attendance/")
        self.assertContains(r, "class_group")            # create page renders fields
        r = self.client.get("/forms/submissions/")
        self.assertContains(r, "FORM-ATTENDANCE-")       # their sheet is in the list
        r = self.client.get(f"/forms/submissions/{sid}/")
        self.assertEqual(r.status_code, 200)             # detail page opens

    def test_manager_approval_journey(self):
        """Manager: task inbox → see available actions → approve → timeline."""
        sid = self._teacher_submits_sheet("2026-09-16", 1)
        self._login(self.manager)

        # Pending task is in the manager's workbench.
        r = self.client.get("/api/tasks/?status=pending")
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(r.json()["count"], 1)

        # In `new` only submit is available — approve is NOT offered yet.
        submission = FormSubmission.objects.get(pk=sid)
        avail = _engine().get_available_transitions(
            submission.workflow_instance, self.manager,
        )
        self.assertEqual({t.kind for t in avail}, {"submit"})
        t_submit = Transition.objects.get(
            workflow_definition__code="form-review", name="submit",
        )
        r = self.client.post(
            f"/api/forms/submissions/{sid}/transition/",
            {"transition_id": str(t_submit.pk)}, format="json",
        )
        self.assertEqual(r.status_code, 200, r.content)

        # Now approve is offered (and it is a terminal, signed action).
        submission.refresh_from_db()
        avail = _engine().get_available_transitions(
            submission.workflow_instance, self.manager,
        )
        self.assertEqual({t.kind for t in avail}, {"approve", "reject"})
        r = self.client.post(
            f"/api/forms/submissions/{sid}/approve/",
            {"comment": "تایید نهایی"}, format="json",
        )
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.json()["status"], "approved")
        self.assertTrue(ApprovalRecord.objects.filter(
            instance=submission.workflow_instance, approver=self.manager,
        ).exists())
        # The teacher (requester) got an in-app notification; deliver it.
        call_command("flush_notifications", stdout=io.StringIO())
        r = self.client.get(f"/forms/submissions/{sid}/")
        self.assertContains(r, "FORM-ATTENDANCE-")

    def test_teacher_never_sees_approve_action(self):
        """The submitter cannot approve their own sheet (role + name match)."""
        sid = self._teacher_submits_sheet("2026-09-17", 1)
        t_submit = Transition.objects.get(
            workflow_definition__code="form-review", name="submit",
        )
        r = self.client.post(
            f"/api/forms/submissions/{sid}/transition/",
            {"transition_id": str(t_submit.pk)}, format="json",
        )
        self.assertEqual(r.status_code, 200)
        submission = FormSubmission.objects.get(pk=sid)
        avail = _engine().get_available_transitions(
            submission.workflow_instance, self.teacher,
        )
        self.assertFalse(any(t.kind in ("approve", "reject") for t in avail))
        r = self.client.post(f"/api/forms/submissions/{sid}/approve/",
                             format="json")
        self.assertEqual(r.status_code, 403)

    def test_student_cannot_reach_admin_surface(self):
        student = UserFactory(username="e2e-student", roles=["student"])
        self._login(student)
        # Pages 404 (don't advertise), APIs 403 (role trio denies).
        self.assertEqual(self.client.get("/forms/admin/schemas/").status_code, 404)
        self.assertEqual(
            self.client.get("/api/forms/admin/schemas/").status_code, 403,
        )


# ═════════════════════════════════════════════════════════════════════════════
# L5 — REGRESSION: previously fixed behaviors, now locked forever
# ═════════════════════════════════════════════════════════════════════════════

class RegressionTests(TestCase):
    """🔄 Regression — every past bug/fixed behavior gets a permanent guard."""

    def setUp(self):
        self.client = APIClient()
        seed_role_codes("manager", "employee", "teacher", "student",
                        "parent", "hr", "workflow_admin")
        seed_form_workflows()
        seed_schemas("attendance")
        self.teacher = UserFactory(username="r-teacher", roles=["teacher"])
        self.manager = UserFactory(
            username="r-manager", roles=["manager", "workflow_admin"],
        )
        for u in (self.teacher, self.manager):
            grant_forms_perms(u)
        self.teacher_person = make_person(self.teacher, "teacher",
                                          national_code=next_nc())
        self.group = make_class_group(teacher=self.teacher_person)
        self.student = make_person(None, "student", national_code=next_nc())
        make_enrollment(self.group, self.student)

    def _payload(self, date="2026-09-05", number=1, status="present"):
        return {
            "schema_slug": "attendance",
            "data": {
                "class_group": str(self.group.pk), "session_date": date,
                "session_number": number, "session_start": "08:00",
                "session_end": "09:00",
                "attendance_list": [
                    {"student_id": str(self.student.pk), "status": status,
                     "note": ""},
                ],
            },
        }

    def _create_submit(self, *, headers=None, date="2026-09-05", number=1):
        self.client.force_login(self.teacher)
        r = self.client.post("/api/forms/submissions/", self._payload(date, number),
                             format="json", **(headers or {}))
        self.assertEqual(r.status_code, 201, r.content)
        sid = r.json()["id"]
        r = self.client.post(f"/api/forms/submissions/{sid}/submit/",
                             **(headers or {}))
        self.assertEqual(r.status_code, 200, r.content)
        return sid

    def _advance(self, sid):
        t = Transition.objects.get(
            workflow_definition__code="form-review", name="submit",
        )
        r = self.client.post(
            f"/api/forms/submissions/{sid}/transition/",
            {"transition_id": str(t.pk)}, format="json",
        )
        self.assertEqual(r.status_code, 200, r.content)

    # ── forms double-submit (B-cycle fix) ────────────────────────────────
    def test_reg_double_submit_409_no_duplicate(self):
        sid = self._create_submit()
        r = self.client.post(f"/api/forms/submissions/{sid}/submit/")
        self.assertEqual(r.status_code, 409)
        self.assertEqual(
            Instance.objects.filter(form_submissions__pk=sid).count(), 1,
        )

    def test_reg_idempotency_key_replays_submit(self):
        """Retried submit with the same key returns 200 + the SAME submission."""
        self.client.force_login(self.teacher)
        headers = {"HTTP_IDEMPOTENCY_KEY": "reg-key-1"}
        r = self.client.post("/api/forms/submissions/", self._payload(),
                             format="json", **headers)
        sid = r.json()["id"]
        first = self.client.post(f"/api/forms/submissions/{sid}/submit/", **headers)
        second = self.client.post(f"/api/forms/submissions/{sid}/submit/", **headers)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json()["id"], second.json()["id"])
        self.assertEqual(
            ActionLog.objects.filter(instance__form_submissions__pk=sid,
                                     action="create").count(), 1,
        )

    # ── engine replay (this round's fix) ─────────────────────────────────
    def test_reg_engine_transition_replay_returns_current_state(self):
        from apps.workflow.services import WorkflowEngineError

        employee = UserFactory(username="r2", roles=["employee"])
        wf, *_ = approval_wf("reg-wf")
        manager = UserFactory(username="r3", roles=["manager"])
        instance = _plain_instance(wf, employee)
        t = Transition.objects.get(workflow_definition=wf, name="approve")
        engine = _engine()
        engine.execute_transition(instance.pk, t.pk, manager,
                                  idempotency_key="reg-replay-1")
        again = engine.execute_transition(instance.pk, t.pk, manager,
                                          idempotency_key="reg-replay-1")
        self.assertEqual(again.pk, instance.pk)
        self.assertEqual(ActionLog.objects.filter(
            instance=instance, idempotency_key="reg-replay-1").count(), 1)
        # Key reuse on ANOTHER instance is a hard reject, never a silent replay.
        other = _plain_instance(wf, employee)
        with self.assertRaises(WorkflowEngineError):
            engine.execute_transition(other.pk, t.pk, manager,
                                      idempotency_key="reg-replay-1")
        other.refresh_from_db()
        self.assertEqual(other.status, Instance.Status.RUNNING)

    # ── double approve (workflow state machine) ─────────────────────────
    def test_reg_double_approve_single_approval_record(self):
        sid = self._create_submit(date="2026-09-06", number=1)
        self._advance(sid)
        self.client.force_login(self.manager)
        first = self.client.post(f"/api/forms/submissions/{sid}/approve/",
                                 format="json")
        self.assertEqual(first.status_code, 200)
        second = self.client.post(f"/api/forms/submissions/{sid}/approve/",
                                  format="json")
        self.assertIn(second.status_code, (400, 403))
        submission = FormSubmission.objects.get(pk=sid)
        self.assertEqual(ApprovalRecord.objects.filter(
            instance=submission.workflow_instance).count(), 1)

    # ── attendance projection (B4/B5) ───────────────────────────────────
    def test_reg_second_sheet_updates_row_not_duplicate(self):
        from apps.education.models import AttendanceRecord

        sid = self._create_submit(date="2026-09-07", number=3)
        r = self.client.post("/api/forms/submissions/",
                             self._payload("2026-09-07", 3, "excused"),
                             format="json")
        self.assertEqual(r.status_code, 201, r.content)
        self.client.post(f"/api/forms/submissions/{r.json()['id']}/submit/")
        rows = AttendanceRecord.objects.filter(
            session__class_group=self.group,
            session__session_date="2026-09-07", student=self.student,
        )
        self.assertEqual(rows.count(), 1)
        self.assertEqual(rows.first().status, "excused")
        from apps.education.models import ClassSession

        self.assertEqual(ClassSession.objects.filter(
            class_group=self.group, session_date="2026-09-07",
            session_number=3).count(), 1)

    # ── capacity (B4) ────────────────────────────────────────────────────
    def test_reg_capacity_still_enforced_on_api(self):
        from apps.academics import models as ac_models

        tiny = make_class_group(capacity=1)
        grant_model_perms(self.manager, ac_models.AcademicTerm,
                          ac_models.ClassGroup, ac_models.ClassEnrollment)
        self.client.force_login(self.manager)
        codes = []
        for _ in range(2):
            s = make_person(None, "student", national_code=next_nc())
            r = self.client.post("/api/academics/enrollments/",
                                 {"class_group": str(tiny.pk), "student": str(s.pk)},
                                 format="json")
            codes.append(r.status_code)
        self.assertEqual(codes, [201, 400], codes)  # 2nd enrollment hits the cap
        self.assertEqual(tiny.enrollments.filter(is_active=True).count(), 1)

    # ── PII masking (B1) ─────────────────────────────────────────────────
    def test_reg_pii_masked_for_non_custodians(self):
        from apps.persons.tests import grant_persons_model_perms

        other = make_person(None, "student", national_code=next_nc(),
                            address="تهران، خیابان آزمایشی، پلاک ۱۲",
                            email="target.person@example.com")
        grant_persons_model_perms(self.teacher)
        self.client.force_login(self.teacher)
        r = self.client.get(f"/api/persons/{other.pk}/")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        # Raw identifiers must never appear for a non-custodian teacher.
        self.assertNotEqual(body.get("national_code"), other.national_code)
        self.assertIn("*****", body.get("national_code") or "")
        self.assertEqual(body.get("address"), "پنهان")
        self.assertNotEqual(body.get("email"), other.email)

    # ── seeds stability ──────────────────────────────────────────────────
    def test_reg_reseeding_is_idempotent(self):
        self.assertEqual(FormSchema.objects.filter(slug="attendance").count(), 1)
        call_command("seed_form_schemas", "attendance", stdout=io.StringIO())
        call_command("seed_form_workflows", stdout=io.StringIO())
        self.assertEqual(FormSchema.objects.filter(slug="attendance").count(), 1)
        self.assertEqual(
            WorkflowDefinition.objects.filter(code="form-review").count(), 1,
        )
