"""Acceptance-criteria tests (§13 of the engineering report).

Covers the four criteria closed in this round:
  §13-2 DataScope      — students/parents cannot enumerate class groups,
                         enrollments or sessions they do not belong to.
  §13-1 Multi-type     — one Person can be teacher + employee simultaneously
                         with time-bound additional types.
  §13-3 Replay-safety  — a retried transition with the same idempotency key
                         returns the current state instead of an error.
  §13-4 AuditEvent     — denials (403), attachment downloads, masked PII
                         reads and draft field diffs land in the DB table.
  §13-7 Reports        — attendance aggregates read from session_date.
"""
from __future__ import annotations

import datetime

from django.test import TestCase

from apps.core.models import AuditEvent
from apps.education.models import (
    AttendanceRecord,
    ClassSession,
    Course,
    CourseOffering,
)
from apps.forms.tests.factories import (
    UserFactory,
    make_class_group,
    make_person,
    make_term,
)

_seq = iter(range(1000))

#: Real 1×1 PNG (CRC-valid) — private storage requires bytes that sniff as an
#: allowed image type, and the download view checks storage.exists().
_PNG_1PX = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0bIDATx\xdac`\x00"
    b"\x02\x00\x00\x05\x00\x01\xe9\xfa\xdc\xd8\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _nc():
    return f"0099{next(_seq):06d}"


def _roles(*codes):
    from apps.accounts.models import Role

    for code in codes:
        Role.objects.get_or_create(code=code, defaults={"name": code, "priority": 50})


# ─────────────────────────────────────────────────────────────────────────────
# §13-2 DataScope
# ─────────────────────────────────────────────────────────────────────────────

class DataScopeTests(TestCase):
    def setUp(self):
        _roles("manager", "student", "teacher", "parent", "employee")
        self.student_user = UserFactory(username="sc-student", roles=["student"])
        self.student = make_person(self.student_user, "student", national_code=_nc())
        self.other_group = make_class_group()  # nobody's class
        self.my_group = make_class_group()
        from apps.academics.models import ClassEnrollment

        ClassEnrollment.objects.create(class_group=self.my_group, student=self.student)

    @staticmethod
    def _grant_academics_perms(user):
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType

        from apps.academics import models as ac_models

        perms = []
        for model in (ac_models.AcademicTerm, ac_models.ClassGroup,
                      ac_models.ClassEnrollment):
            perms += list(
                Permission.objects.filter(
                    content_type=ContentType.objects.get_for_model(model)
                )
            )
        user.user_permissions.set(perms)
        for attr in ("_user_perm_cache", "_group_perm_cache", "_perm_cache"):
            if hasattr(user, attr):
                delattr(user, attr)

    def test_student_sees_only_own_class_groups(self):
        from apps.academics.scoping import class_groups_visible_to

        visible = set(class_groups_visible_to(self.student_user))
        self.assertIn(self.my_group, visible)
        self.assertNotIn(self.other_group, visible)

    def test_student_sees_only_own_enrollments(self):
        from apps.academics.scoping import enrollments_visible_to

        qs = enrollments_visible_to(self.student_user)
        self.assertTrue(qs.filter(class_group=self.my_group).exists())
        self.assertEqual(qs.count(), 1)

    def test_stranger_cannot_fetch_other_class_group_by_uuid(self):
        # Layer 1 (coarse role gate): students are NOT academic read roles →
        # they never reach the endpoint at all (403, fail-closed).
        self._grant_academics_perms(self.student_user)
        self.client.force_login(self.student_user)
        denied = self.client.get(f"/api/academics/class-groups/{self.my_group.pk}/")
        self.assertEqual(denied.status_code, 403)

        # Layer 2 (object scoping): a teacher CAN reach the endpoint, but a
        # group outside their scope must 404 — existence is never leaked.
        other_teacher = UserFactory(username="sc-teacher2", roles=["teacher"])
        other_person = make_person(other_teacher, "teacher", national_code=_nc())
        foreign_group = make_class_group(teacher=other_person)
        my_teacher = UserFactory(username="sc-teacher1", roles=["teacher"])
        my_person = make_person(my_teacher, "teacher", national_code=_nc())
        own_group = make_class_group(teacher=my_person)
        self._grant_academics_perms(my_teacher)
        self.client.force_login(my_teacher)
        ok = self.client.get(f"/api/academics/class-groups/{own_group.pk}/")
        self.assertEqual(ok.status_code, 200)
        probe = self.client.get(f"/api/academics/class-groups/{foreign_group.pk}/")
        self.assertEqual(probe.status_code, 404)

    def test_parent_scope_via_child_enrollment(self):
        parent_user = UserFactory(username="sc-parent", roles=["parent"])
        parent = make_person(parent_user, "parent", national_code=_nc())
        from apps.persons.models import StudentParent

        StudentParent.objects.create(parent=parent, student=self.student)
        from apps.academics.scoping import enrollments_visible_to

        self.assertTrue(
            enrollments_visible_to(parent_user).filter(
                class_group=self.my_group
            ).exists()
        )

    def test_sessions_scoped_for_student(self):
        offering = CourseOffering.objects.create(
            course=Course.objects.create(title="د", code=_nc()),
            capacity=0,
        )
        session = ClassSession.objects.create(
            offering=offering, session_date=datetime.date(2026, 9, 10),
            start_time="08:00", end_time="09:30",
        )
        from apps.academics.scoping import education_sessions_visible_to

        # The student's ClassGroup-based session is visible; a foreign one not.
        my_session = ClassSession.objects.create(
            class_group=self.my_group,
            session_date=datetime.date(2026, 9, 10),
            start_time="10:00", end_time="11:00",
        )
        visible = set(education_sessions_visible_to(self.student_user))
        self.assertIn(my_session, visible)
        self.assertNotIn(session, visible)


# ─────────────────────────────────────────────────────────────────────────────
# §13-1 Multi-type person
# ─────────────────────────────────────────────────────────────────────────────

class MultiTypePersonTests(TestCase):
    def setUp(self):
        _roles("teacher", "employee", "manager", "student")

    def test_one_person_holds_two_types(self):
        person = make_person(None, "teacher", national_code=_nc())
        from apps.persons.services import person_service

        person_service.add_person_type(
            person=person, type_code="employee",
        )
        self.assertEqual(person.type_codes(), {"teacher", "employee"})
        self.assertTrue(person.is_teacher() and person.is_employee())
        self.assertFalse(person.is_student())

    def test_type_assignment_is_time_bound(self):
        from django.utils import timezone

        person = make_person(None, "teacher", national_code=_nc())
        from apps.persons.services import person_service

        person_service.add_person_type(
            person=person, type_code="employee",
            valid_to=timezone.now() - datetime.timedelta(days=1),
        )
        # Expired additional type is NOT in effective codes.
        self.assertEqual(person.type_codes(), {"teacher"})

    def test_provisioning_grants_all_type_roles(self):
        # Person created WITHOUT a user; provisioning then creates the account.
        person = make_person(None, "teacher", national_code=_nc())
        from apps.persons.services import person_service

        person_service.add_person_type(person=person, type_code="employee")
        person_service._create_user_for_person(person)
        created_user = person.user
        self.assertIsNotNone(created_user)
        self.assertTrue(created_user.has_role("teacher"))
        self.assertTrue(created_user.has_role("employee"))

    def test_duplicate_type_assignment_is_idempotent(self):
        person = make_person(None, "teacher", national_code=_nc())
        from apps.persons.services import person_service

        person_service.add_person_type(person=person, type_code="employee")
        person_service.add_person_type(person=person, type_code="employee")
        from apps.persons.models import PersonTypeAssignment

        self.assertEqual(
            PersonTypeAssignment.objects.filter(person=person, type="employee").count(),
            1,
        )


# ─────────────────────────────────────────────────────────────────────────────
# §13-3 Replay safety
# ─────────────────────────────────────────────────────────────────────────────

class ReplaySafetyTests(TestCase):
    def setUp(self):
        _roles("employee", "manager", "workflow_admin")
        from apps.workflow.models import State, Transition, WorkflowDefinition

        self.employee = UserFactory(username="rp-employee", roles=["employee"])
        self.manager = UserFactory(username="rp-manager", roles=["manager"])
        self.wf = WorkflowDefinition.objects.create(
            code="rp-wf", name="تست تکرار", is_active=True,
        )
        self.s_new = State.objects.create(
            workflow_definition=self.wf, code="new", name="جدید", is_initial=True,
        )
        self.s_done = State.objects.create(
            workflow_definition=self.wf, code="done", name="پایان", is_final=True,
        )
        self.transition = Transition.objects.create(
            workflow_definition=self.wf, from_state=self.s_new,
            to_state=self.s_done, name="approve",
            allowed_role_codes=["manager"], kind="approve",
        )
        from apps.workflow.services import WorkflowEngineService

        self.instance = WorkflowEngineService().create_instance(
            workflow_code="rp-wf", requester=self.employee, title="تست",
        )

    def test_replayed_key_returns_instance_not_error(self):
        from apps.workflow.services import WorkflowEngineService

        engine = WorkflowEngineService()
        first = engine.execute_transition(
            instance_id=self.instance.pk, transition_id=self.transition.pk,
            actor=self.manager, idempotency_key="op-123",
        )
        self.assertEqual(first.status, "completed")
        # Same key again → current instance, NO InvalidTransitionError.
        second = engine.execute_transition(
            instance_id=self.instance.pk, transition_id=self.transition.pk,
            actor=self.manager, idempotency_key="op-123",
        )
        self.assertEqual(second.pk, self.instance.pk)

    def test_same_key_on_another_instance_is_rejected(self):
        from apps.workflow.services import WorkflowEngineService, WorkflowEngineError

        engine = WorkflowEngineService()
        engine.execute_transition(
            instance_id=self.instance.pk, transition_id=self.transition.pk,
            actor=self.manager, idempotency_key="op-456",
        )
        other = engine.create_instance(
            workflow_code="rp-wf", requester=self.employee, title="دوم",
        )
        with self.assertRaises(WorkflowEngineError):
            engine.execute_transition(
                instance_id=other.pk, transition_id=self.transition.pk,
                actor=self.manager, idempotency_key="op-456",
            )
        # The second instance stayed untouched.
        other.refresh_from_db()
        self.assertEqual(other.status, "running")

    def test_replay_without_key_fails_closed(self):
        from apps.workflow.services import (
            InvalidTransitionError,
            WorkflowEngineService,
        )

        engine = WorkflowEngineService()
        engine.execute_transition(
            instance_id=self.instance.pk, transition_id=self.transition.pk,
            actor=self.manager,
        )
        # No key: the old behavior (invalid transition error) remains.
        with self.assertRaises(InvalidTransitionError):
            engine.execute_transition(
                instance_id=self.instance.pk, transition_id=self.transition.pk,
                actor=self.manager,
            )


# ─────────────────────────────────────────────────────────────────────────────
# §13-4 AuditEvent
# ─────────────────────────────────────────────────────────────────────────────

class AuditEventTests(TestCase):
    def setUp(self):
        _roles("manager", "student", "employee", "teacher")
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType

        from apps.academics import models as ac_models

        self.manager = UserFactory(username="au-manager", roles=["manager"])
        perms = []
        for model in (ac_models.AcademicTerm, ac_models.ClassGroup,
                      ac_models.ClassEnrollment):
            perms += list(Permission.objects.filter(
                content_type=ContentType.objects.get_for_model(model)))
        self.manager.user_permissions.set(perms)
        for attr in ("_user_perm_cache", "_group_perm_cache", "_perm_cache"):
            if hasattr(self.manager, attr):
                delattr(self.manager, attr)
        # Base persons model perms for manager (custodian reads) — WITHOUT
        # view_person_detail so the masking path itself is exercised.
        from apps.persons.models import Person
        from apps.persons.tests import grant_persons_model_perms
        grant_persons_model_perms(self.manager)
        self.student_user = UserFactory(username="au-student", roles=["student"])
        grant_persons_model_perms(self.student_user)
        self.student = make_person(self.student_user, "student", national_code=_nc())

    def test_denial_is_recorded(self):
        # A student is forbidden to create a class group → 403 (or 404 by
        # model-permission ordering) — either way an audit row must exist.
        self.client.force_login(self.student_user)
        self.client.post(
            "/api/academics/class-groups/",
            {"term": str(make_term().pk), "code": "x", "name": "کلاس"},
            format="json",
        )
        self.assertTrue(
            AuditEvent.objects.filter(kind=AuditEvent.Kind.ACCESS_DENIED).exists()
        )

    def test_masked_pii_read_is_recorded(self):
        # A TEACHER can address the row (staff directory scoping) but is not
        # its custodian → the serializer masks PII → one sensitive_read event.
        other = make_person(None, "student", national_code=_nc())
        teacher = UserFactory(username="au-teacher", roles=["teacher"])
        # Model perms for StrictDjangoModelPermissions — deliberately WITHOUT
        # view_person_detail (that would make the teacher a custodian).
        from apps.persons.tests import grant_persons_model_perms
        grant_persons_model_perms(teacher)
        self.client.force_login(teacher)
        response = self.client.get(f"/api/persons/{other.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            AuditEvent.objects.filter(
                kind=AuditEvent.Kind.SENSITIVE_READ,
                object_id=str(other.pk),
            ).exists()
        )

    def test_full_detail_read_is_not_audited(self):
        # Custodian (manager) reads the same person → no masked-read event.
        other = make_person(None, "student", national_code=_nc())
        self.client.force_login(self.manager)
        self.client.get(f"/api/persons/{other.pk}/")
        self.assertFalse(
            AuditEvent.objects.filter(
                kind=AuditEvent.Kind.SENSITIVE_READ, object_id=str(other.pk),
            ).exists()
        )

    def test_download_is_recorded(self):
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        from django.core.files.uploadedfile import SimpleUploadedFile

        from apps.forms.models import FormAttachment, FormSubmission
        from apps.forms.tests.factories import make_schema

        employee = UserFactory(username="au-employee", roles=["employee"])
        # HasGroupPermission requires the model-level view perm on downloads.
        ct = ContentType.objects.get_for_model(FormAttachment)
        employee.user_permissions.add(
            Permission.objects.get(content_type=ct, codename="view_formattachment")
        )
        schema = make_schema(slug="audit-dl")
        submission = FormSubmission.objects.create(
            form_schema=schema, submitted_by=employee, data={"title": "س"},
            status=FormSubmission.Status.SUBMITTED, submission_number="F-1",
        )
        # Persist real bytes so the storage-exists() check passes and the
        # view reaches the streaming (and the audit) path.
        upload = SimpleUploadedFile(
            "report.png", _PNG_1PX, content_type="image/png",
        )
        name = upload.name
        attachment = FormAttachment(
            submission=submission, field_key="title",
            original_filename="report.png", mime_type="image/png",
            file_size=len(_PNG_1PX), uploaded_by=employee,
        )
        attachment.file.save(name, upload, save=True)
        self.client.force_login(employee)
        response = self.client.get(f"/api/forms/attachments/{attachment.pk}/download/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            AuditEvent.objects.filter(
                kind=AuditEvent.Kind.DOWNLOAD, object_id=str(attachment.pk),
            ).exists()
        )


# ─────────────────────────────────────────────────────────────────────────────
# §13-7 Reports
# ─────────────────────────────────────────────────────────────────────────────

class ReportTests(TestCase):
    def setUp(self):
        _roles("manager", "teacher")
        self.manager = UserFactory(username="rep-manager", roles=["manager"])
        self.student_user = UserFactory(username="rep-student", roles=["student"])
        self.student = make_person(self.student_user, "student", national_code=_nc())
        self.other_user = UserFactory(username="rep-other", roles=["student"])
        self.other = make_person(self.other_user, "student", national_code=_nc())

    def _session(self, date):
        return ClassSession.objects.create(
            class_group=make_class_group(),
            session_date=date, start_time="08:00", end_time="09:00",
        )

    def test_daily_attendance_counts(self):
        session = self._session(datetime.date(2026, 9, 9))
        AttendanceRecord.objects.create(session=session, student=self.student,
                                        status="present")
        AttendanceRecord.objects.create(session=session, student=self.other,
                                        status="absent")
        from apps.education.reports import attendance_report

        data = attendance_report(user=self.manager, period="day",
                                 ref=datetime.date(2026, 9, 9))
        self.assertEqual(data["totals"]["present"], 1)
        self.assertEqual(data["totals"]["absent"], 1)
        self.assertEqual(data["all"], 2)

    def test_report_excludes_other_days(self):
        session = self._session(datetime.date(2026, 9, 9))
        AttendanceRecord.objects.create(session=session, student=self.student,
                                        status="present")
        from apps.education.reports import attendance_report

        data = attendance_report(user=self.manager, period="day",
                                 ref=datetime.date(2026, 9, 15))
        self.assertEqual(data["all"], 0)

    def test_capacity_report_lists_offerings(self):
        course = Course.objects.create(title="دوره ظرفیت", code=_nc())
        offering = CourseOffering.objects.create(
            course=course, capacity=2, enrolled_count=2,
        )
        from apps.education.reports import capacity_report

        rows = capacity_report(user=self.manager)
        match = [r for r in rows if r["id"] == str(offering.pk)]
        self.assertTrue(match)
        self.assertTrue(match[0]["full"])
        self.assertEqual(match[0]["seats_left"], 0)

    def test_report_api_requires_permission(self):
        self.client.force_login(self.student_user)
        response = self.client.get("/api/education/reports/attendance/?period=day")
        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            AuditEvent.objects.filter(kind=AuditEvent.Kind.ACCESS_DENIED).exists()
        )
