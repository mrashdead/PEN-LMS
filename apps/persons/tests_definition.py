from __future__ import annotations

import itertools

from django.test import TestCase

from apps.accounts.models import Role
from apps.forms.tests.factories import UserFactory
from apps.persons.forms import PersonDefinitionForm
from apps.persons.models import Person
from apps.persons.person_definition import PersonDefinitionService


_codes = itertools.count(9100000001)


def next_code() -> str:
    return str(next(_codes))


def seed_roles():
    for code in (
        "employee", "supervisor", "manager", "workflow_admin", "teacher", "student"
    ):
        Role.objects.get_or_create(code=code, defaults={"name": code, "priority": 50})


class PersonDefinitionFormTests(TestCase):
    def setUp(self):
        seed_roles()

    def test_targets_are_filtered_by_the_creation_matrix(self):
        expected = {
            "workflow_admin": {"manager", "employee", "teacher", "student"},
            "manager": {"employee", "teacher", "student"},
            "supervisor": {"teacher", "student"},
            "employee": {"student"},
        }
        for role, wanted in expected.items():
            user = UserFactory(username=f"form-{role}", roles=[role])
            form = PersonDefinitionForm(actor=user)
            self.assertEqual({value for value, _label in form.fields["target"].choices}, wanted)

    def test_student_form_requires_one_parent_mobile(self):
        user = UserFactory(username="form-clerk", roles=["employee"])
        form = PersonDefinitionForm(data={
            "target": "student", "first_name": "آوا", "last_name": "آزمون",
            "national_code": next_code(), "phone_number": "09121234567",
            "gender": "female",
        }, actor=user)
        self.assertFalse(form.is_valid())
        self.assertIn("حداقل یکی از شماره موبایل", " ".join(form.non_field_errors()))

    def test_student_creation_provisions_login_and_parent_profile(self):
        user = UserFactory(username="form-clerk-2", roles=["employee"])
        data = {
            "target": "student", "first_name": "آوا", "last_name": "آزمون",
            "national_code": next_code(), "phone_number": "09121234567",
            "gender": "female", "father_first_name": "رضا",
            "father_last_name": "آزمون", "father_phone_number": "09129876543",
        }
        form = PersonDefinitionForm(data=data, actor=user)
        self.assertTrue(form.is_valid(), form.errors)
        person = PersonDefinitionService().create(actor=user, cleaned_data=form.cleaned_data)
        self.assertEqual(person.user.username, data["national_code"])
        self.assertTrue(person.user.check_password(data["national_code"]))
        self.assertEqual(person.student_profile.father_phone, "09129876543")
        self.assertEqual(person.student_profile.father_first_name, "رضا")

    def test_employee_creation_requires_password_and_provisions_supervisor_role(self):
        user = UserFactory(username="form-manager", roles=["manager"])
        data = {
            "target": "employee", "first_name": "مریم", "last_name": "مدیر",
            "national_code": next_code(), "phone_number": "09121112233",
            "gender": "female", "employee_kind": "supervisor",
            "job_title": "سرپرست آموزش", "password": "SafePass123!",
        }
        form = PersonDefinitionForm(data=data, actor=user)
        self.assertTrue(form.is_valid(), form.errors)
        person = PersonDefinitionService().create(actor=user, cleaned_data=form.cleaned_data)
        self.assertEqual(person.user.username, data["national_code"])
        self.assertTrue(person.user.check_password("SafePass123!"))
        self.assertIn("supervisor", person.user.role_codes())

    def test_strict_national_phone_and_email_validation(self):
        user = UserFactory(username="form-strict", roles=["employee"])
        form = PersonDefinitionForm(data={
            "target": "student", "first_name": "آ", "last_name": "ب",
            "national_code": "123", "phone_number": "0912", "email": "bad-email",
            "gender": "unspecified", "father_phone_number": "09121234567",
            "father_first_name": "پدر", "father_last_name": "آزمون",
        }, actor=user)
        self.assertFalse(form.is_valid())
        self.assertIn("national_code", form.errors)
        self.assertIn("phone_number", form.errors)
        self.assertIn("email", form.errors)

    def test_workspace_create_endpoint_uses_the_django_form(self):
        user = UserFactory(username="form-http", roles=["employee"])
        self.client.force_login(user)
        response = self.client.post("/workspace/persons/create/", {
            "target": "student", "first_name": "وب", "last_name": "آزمون",
            "national_code": next_code(), "phone_number": "09123334455",
            "gender": "unspecified", "mother_first_name": "مریم",
            "mother_last_name": "آزمون", "mother_phone_number": "09125556677",
        })
        self.assertEqual(response.status_code, 201, response.content)
        person = Person.objects.get(national_code=response.json()["person"]["username"])
        self.assertTrue(person.user_id)

    def test_persons_workspace_uses_the_existing_bootstrap_shell(self):
        user = UserFactory(username="form-page", roles=["employee"])
        self.client.force_login(user)
        response = self.client.get("/workspace/persons/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="person-create-form"')
        self.assertContains(response, "assets/pen/js/persons.js")
