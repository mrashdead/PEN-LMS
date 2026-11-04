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


class NationalCodeExceptionTests(TestCase):
    def setUp(self):
        seed_roles()
        self.manager = UserFactory(username="exception-manager", roles=["manager"])
        self.employee = UserFactory(username="exception-employee", roles=["employee"])
        self.data = {
            "target": "student", "first_name": "آوا", "last_name": "آزمون",
            "national_code": "2300331441", "phone_number": "09121234567",
            "gender": "female", "father_first_name": "رضا",
            "father_last_name": "آزمون", "father_phone_number": "09129876543",
        }

    def test_manager_explicitly_approves_and_records_exception(self):
        self.client.force_login(self.manager)
        url = "/workspace/persons/create/"
        response = self.client.post(url, self.data)
        self.assertEqual(response.status_code, 400)
        response = self.client.post(url, {**self.data, "approve_national_code_exception": "on"})
        self.assertEqual(response.status_code, 201, response.content)
        person = Person.objects.get(pk=response.json()["person"]["id"])
        self.assertEqual(person.national_code_exception_approved_by, self.manager)
        self.assertTrue(person.national_code_exception_approved)
        person.full_clean()
        person.national_code = "2300331442"
        self.assertFalse(person.national_code_exception_approved)
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            person.full_clean()

    def test_employee_cannot_approve_and_manager_cannot_override_bad_format(self):
        for actor, code in ((self.employee, "2300331441"), (self.manager, "123"),
                            (self.manager, "1111111111")):
            form = PersonDefinitionForm(data={**self.data, "national_code": code,
                "approve_national_code_exception": "on"}, actor=actor)
            self.assertFalse(form.is_valid())
            self.assertIn("national_code", form.errors)

    def test_service_rechecks_permission_when_form_is_bypassed(self):
        from apps.persons.services import PersonService, PersonServiceError
        with self.assertRaises(PersonServiceError):
            PersonService().create_person(
                national_code="2300331441", first_name="آ", last_name="ب",
                person_type="student", mobile="09121234567", registered_by=self.employee,
                approve_national_code_exception=True,
            )


class DuplicateAccountEmailTests(TestCase):
    def setUp(self):
        seed_roles()
        self.manager = UserFactory(username="email-manager", roles=["manager"])
        UserFactory(username="email-owner", email="existing@example.com")
        self.client.force_login(self.manager)

    def test_staff_creation_reports_duplicate_email_without_creating_person(self):
        response = self.client.post("/workspace/persons/staff/create/", {
            "target": "employee", "first_name": "مریم", "last_name": "آزمون",
            "national_code": "0012345679", "phone_number": "09121112233",
            "gender": "female", "employee_kind": "ordinary", "job_title": "کارمند",
            "password": "SafePass123!", "email": "existing@example.com",
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.json()["errors"])
        self.assertFalse(Person.objects.filter(national_code="0012345679").exists())

    def test_recreate_deleted_person_with_same_email_and_national_code(self):
        data = {
            "target": "employee", "first_name": "مریم", "last_name": "آزمون",
            "national_code": "0012345679", "phone_number": "09121112233",
            "gender": "female", "employee_kind": "ordinary", "job_title": "کارمند",
            "password": "SafePass123!", "email": "reusable@example.com",
        }
        first = self.client.post("/workspace/persons/staff/create/", data)
        self.assertEqual(first.status_code, 201, first.content)
        original = Person.objects.get(pk=first.json()["person"]["id"])
        old_user = original.user
        original.soft_delete()
        second = self.client.post("/workspace/persons/staff/create/", data)
        self.assertEqual(second.status_code, 201, second.content)
        old_user.refresh_from_db()
        self.assertTrue(old_user.is_deleted)
        self.assertFalse(old_user.is_active)
        self.assertIsNone(old_user.email)
        new = Person.objects.get(pk=second.json()["person"]["id"])
        self.assertNotEqual(new.user_id, old_user.pk)
        self.assertEqual(new.user.username, data["national_code"])
        self.assertEqual(new.user.email, data["email"])
        self.assertTrue(new.user.check_password(data["password"]))


class DeletedPersonAccountLifecycleTests(TestCase):
    def setUp(self):
        from apps.accounts.models import User
        self.admin = User.objects.create_superuser(username="lifecycle-admin", password="password")
        self.user = User.objects.create_user(username="lifecycle-user", password="password", email="lifecycle@example.com")
        self.person = Person.objects.create(national_code="0012345679", first_name="آ", last_name="ب", mobile="09121112233", person_type="student", user=self.user)
        self.client.force_login(self.admin)

    def test_delete_disables_account_hides_permissions_and_restore_recovers_it(self):
        from apps.org.services import user_directory
        response = self.client.post(f"/api/persons/{self.person.pk}/delete/")
        self.assertEqual(response.status_code, 200, response.content)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_deleted)
        self.assertFalse(self.user.is_active)
        self.assertNotIn(str(self.user.pk), [str(row["id"]) for row in user_directory()])
        self.client.logout()
        self.assertFalse(self.client.login(username="lifecycle-user", password="password"))
        self.client.force_login(self.admin)
        response = self.client.post(f"/api/persons/{self.person.pk}/restore/")
        self.assertEqual(response.status_code, 200, response.content)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_deleted)
        self.assertTrue(self.user.is_active)
        self.client.logout()
        self.assertTrue(self.client.login(username="lifecycle-user", password="password"))

    def test_delete_preserves_prior_inactive_status_on_restore(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        self.assertEqual(self.client.post(f"/api/persons/{self.person.pk}/delete/").status_code, 200)
        self.assertEqual(self.client.post(f"/api/persons/{self.person.pk}/restore/").status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertFalse(self.user.is_deleted)

    def test_system_administrator_account_cannot_be_deleted_via_person(self):
        self.person.user = self.admin
        self.person.save(update_fields=["user"])
        response = self.client.post(f"/api/persons/{self.person.pk}/delete/")
        self.assertEqual(response.status_code, 400)
        self.person.refresh_from_db()
        self.assertFalse(self.person.is_deleted)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)
