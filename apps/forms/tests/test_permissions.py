"""Role- and object-level visibility rules for schemas and submissions."""
from __future__ import annotations

from django.test import TestCase

from apps.forms.models import FormComment, FormSubmission
from apps.forms.permissions import (
    can_view_internal_comments,
    visible_schemas_for,
    visible_submissions_for,
)
from apps.forms.tests.factories import (
    UserFactory,
    make_class_group,
    make_enrollment,
    make_person,
    make_schema,
)


class SchemaVisibilityTests(TestCase):
    def test_role_restricted_schema_hidden_from_other_roles(self):
        schema = make_schema(slug="teachers-only")
        schema.allowed_roles.add(*_roles("teacher"))
        teacher = UserFactory(username="pv-teacher", roles=["teacher"])
        student = UserFactory(username="pv-student", roles=["student"])
        self.assertTrue(visible_schemas_for(teacher).filter(pk=schema.pk).exists())
        self.assertFalse(visible_schemas_for(student).filter(pk=schema.pk).exists())

    def test_public_schema_visible_to_all(self):
        schema = make_schema(slug="public-form")  # no allowed_roles → public
        student = UserFactory(username="pv-student2", roles=["student"])
        self.assertTrue(visible_schemas_for(student).filter(pk=schema.pk).exists())


class SubmissionVisibilityTests(TestCase):
    def setUp(self):
        self.schema = make_schema(slug="vis")
        self.teacher = UserFactory(username="vis-teacher", roles=["teacher"])
        self.teacher_person = make_person(self.teacher, "teacher")
        self.group = make_class_group(teacher=self.teacher_person)
        self.other_group = make_class_group()

        self.student = UserFactory(username="vis-student", roles=["student"])
        self.student_person = make_person(self.student, "student")
        make_enrollment(self.group, self.student_person)

        self.manager = UserFactory(username="vis-manager", roles=["manager"])
        self.employee = UserFactory(username="vis-employee", roles=["employee"])

    def _sub(self, **kw):
        defaults = {"form_schema": self.schema, "submitted_by": self.employee, "data": {}}
        defaults.update(kw)
        return FormSubmission.objects.create(**defaults)

    def test_submitter_sees_own(self):
        mine = self._sub(submitted_by=self.employee)
        self.assertTrue(visible_submissions_for(self.employee).filter(pk=mine.pk).exists())

    def test_employee_cannot_see_unrelated(self):
        other = UserFactory(username="vis-other", roles=["employee"])
        theirs = self._sub(submitted_by=other)
        self.assertFalse(visible_submissions_for(self.employee).filter(pk=theirs.pk).exists())

    def test_teacher_sees_own_class_group_submissions(self):
        sub = self._sub(class_group=self.group)
        self.assertTrue(visible_submissions_for(self.teacher).filter(pk=sub.pk).exists())

    def test_teacher_cannot_see_other_class_group(self):
        sub = self._sub(class_group=self.other_group)
        self.assertFalse(visible_submissions_for(self.teacher).filter(pk=sub.pk).exists())

    def test_teacher_role_code_alone_is_insufficient(self):
        # A teacher whose Person does NOT own the class group cannot see it.
        rogue = UserFactory(username="vis-rogue", roles=["teacher"])
        make_person(rogue, "teacher")  # teaches nothing
        sub = self._sub(class_group=self.group)
        self.assertFalse(visible_submissions_for(rogue).filter(pk=sub.pk).exists())

    def test_student_sees_own_subject_submission(self):
        sub = self._sub(subject_person=self.student_person)
        self.assertTrue(visible_submissions_for(self.student).filter(pk=sub.pk).exists())

    def test_student_cannot_see_other_student(self):
        other_student = make_person(None, "student", first_name="Other")
        sub = self._sub(subject_person=other_student)
        self.assertFalse(visible_submissions_for(self.student).filter(pk=sub.pk).exists())

    def test_manager_sees_everything(self):
        a = self._sub(class_group=self.group)
        b = self._sub(class_group=self.other_group)
        qs = visible_submissions_for(self.manager)
        self.assertTrue(qs.filter(pk=a.pk).exists())
        self.assertTrue(qs.filter(pk=b.pk).exists())


class InternalCommentVisibilityTests(TestCase):
    def setUp(self):
        self.schema = make_schema(slug="cmt-vis")
        self.employee = UserFactory(username="cv-employee", roles=["employee"])
        self.submission = FormSubmission.objects.create(
            form_schema=self.schema, submitted_by=self.employee, data={},
        )
        self.internal = FormComment.objects.create(
            submission=self.submission, author=self.employee, body="staff-only", is_internal=True,
        )
        self.public = FormComment.objects.create(
            submission=self.submission, author=self.employee, body="open", is_internal=False,
        )

    def test_student_cannot_view_internal(self):
        student = UserFactory(username="cv-student", roles=["student"])
        self.assertFalse(can_view_internal_comments(student))

    def test_teacher_and_manager_can_view_internal(self):
        teacher = UserFactory(username="cv-teacher", roles=["teacher"])
        manager = UserFactory(username="cv-manager", roles=["manager"])
        self.assertTrue(can_view_internal_comments(teacher))
        self.assertTrue(can_view_internal_comments(manager))


def _roles(*codes):
    from apps.accounts.models import Role
    objs = []
    for code in codes:
        role, _ = Role.objects.get_or_create(code=code, defaults={"name": code, "priority": 50})
        objs.append(role)
    return objs
