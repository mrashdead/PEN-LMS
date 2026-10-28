from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser, Group, Permission
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.accounts.models import Role, User, UserRole


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
class ManagementRolePermissionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.manager_role = Role.objects.create(code="manager", name="Manager")
        cls.admin_role = Role.objects.create(code="workflow_admin", name="System manager")
        cls.employee_role = Role.objects.create(code="employee", name="Employee")
        cls.view_person = Permission.objects.get(
            content_type__app_label="persons", codename="view_person",
        )

    def setUp(self):
        self.user = User.objects.create_user(username="new-management-user")

    def test_new_manager_can_load_directory_without_manual_permissions_or_groups(self):
        self.user.assign_role(self.manager_role)
        self.assertFalse(self.user.is_superuser)
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.groups.exists())
        self.assertFalse(self.user.user_permissions.exists())
        self.client.force_login(self.user)
        response = self.client.get(
            "/api/persons/?directory=education&ordering=-created_at&page_size=50",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertIn("results", response.json())

    def test_existing_role_assignment_gets_permissions_without_backfill(self):
        UserRole.objects.create(user=self.user, role=self.admin_role)
        self.assertTrue(self.user.has_perm("persons.view_person"))
        self.assertTrue(self.user.has_perm("persons.change_person"))
        self.assertTrue(self.user.has_perm("accounts.change_user"))

    def test_manager_created_by_person_wizard_can_load_directory(self):
        from apps.persons.forms import PersonDefinitionForm
        from apps.persons.person_definition import PersonDefinitionService

        self.user.assign_role(self.admin_role)
        form = PersonDefinitionForm(actor=self.user, directory="staff", data={
            "target": "manager", "first_name": "مدیر", "last_name": "آزمایشی",
            "national_code": "8000000016", "phone_number": "09121110000",
            "gender": "unspecified", "job_title": "مدیریت آموزش",
            "password": "TestManager-Pass-349!",
        })
        self.assertTrue(form.is_valid(), form.errors)
        person = PersonDefinitionService().create(actor=self.user, cleaned_data=form.cleaned_data)
        self.assertIn("manager", person.user.role_codes())
        self.assertFalse(person.user.is_superuser)
        self.assertFalse(person.user.user_permissions.exists())
        self.client.force_login(person.user)
        response = self.client.get("/api/persons/?directory=education&page_size=50")
        self.assertEqual(response.status_code, 200, response.content)

    def test_group_seeding_and_role_defaults_use_the_same_policy(self):
        import io
        from django.core.management import call_command

        call_command("seed_groups", stdout=io.StringIO())
        self.user.assign_role(self.manager_role)
        manager_group = Group.objects.get(name="مدیر مؤسسه")
        seeded = {
            f"{app}.{code}"
            for app, code in manager_group.permissions.values_list("content_type__app_label", "codename")
        }
        self.assertEqual(self.user.get_group_permissions(), seeded)

    def test_manager_inherits_only_its_existing_permission_policy(self):
        self.user.assign_role(self.manager_role)
        self.assertTrue(self.user.has_perm("persons.add_person"))
        self.assertTrue(self.user.has_module_perms("persons"))
        self.assertFalse(self.user.has_perm("accounts.change_user"))
        self.assertFalse(self.user.has_perm("persons.nonexistent_permission"))
        self.assertFalse(self.user.has_perm("persons.view_person", obj=object()))

    def test_revocation_removes_role_grants_on_the_same_user_instance(self):
        self.user.assign_role(self.admin_role)
        self.assertTrue(self.user.has_perm("accounts.change_user"))
        self.user.revoke_role(self.admin_role)
        self.assertFalse(self.user.has_perm("accounts.change_user"))

    def test_expiration_removes_role_grants_on_the_same_user_instance(self):
        now = timezone.now()
        self.user.assign_role(self.admin_role, valid_to=now + timedelta(minutes=1))
        self.assertTrue(self.user.has_perm("accounts.change_user"))
        with patch("apps.accounts.models.timezone.now", return_value=now + timedelta(minutes=2)):
            self.assertFalse(self.user.has_perm("accounts.change_user"))

    def test_future_inactive_and_deleted_roles_do_not_grant_permissions(self):
        link = self.user.assign_role(self.admin_role, valid_from=timezone.now() + timedelta(days=1))
        self.assertFalse(self.user.has_perm("persons.view_person"))
        link.valid_from = None
        link.is_active = False
        link.save()
        self.assertFalse(self.user.has_perm("persons.view_person"))
        link.is_active = True
        link.save()
        self.admin_role.is_active = False
        self.admin_role.save()
        self.assertFalse(self.user.has_perm("persons.view_person"))
        self.admin_role.is_active = True
        self.admin_role.is_deleted = True
        self.admin_role.save()
        self.assertFalse(self.user.has_perm("persons.view_person"))

    def test_downgrade_keeps_manager_grants_but_removes_system_manager_grants(self):
        self.user.assign_role(self.manager_role)
        self.user.assign_role(self.admin_role)
        self.assertTrue(self.user.has_perm("accounts.change_user"))
        self.user.revoke_role(self.admin_role)
        self.assertTrue(self.user.has_perm("persons.view_person"))
        self.assertFalse(self.user.has_perm("accounts.change_user"))

    def test_employee_does_not_inherit_management_permissions(self):
        self.user.assign_role(self.employee_role)
        self.assertFalse(self.user.has_perm("persons.view_person"))
        self.client.force_login(self.user)
        response = self.client.get("/api/persons/?directory=education")
        self.assertEqual(response.status_code, 403)

    def test_explicit_permissions_and_custom_groups_still_work(self):
        self.user.user_permissions.add(self.view_person)
        group = Group.objects.create(name="Custom operations")
        group.permissions.add(Permission.objects.get(
            content_type__app_label="persons", codename="add_person",
        ))
        self.user.groups.add(group)
        self.assertTrue(self.user.has_perm("persons.view_person"))
        self.assertTrue(self.user.has_perm("persons.add_person"))

    def test_inactive_deleted_and_anonymous_users_get_no_role_grants(self):
        self.user.assign_role(self.admin_role)
        self.user.is_active = False
        self.assertFalse(self.user.has_perm("persons.view_person"))
        self.user.is_active = True
        self.user.is_deleted = True
        self.assertFalse(self.user.has_perm("persons.view_person"))
        self.assertFalse(AnonymousUser().has_perm("persons.view_person"))

    def test_permission_panel_includes_effective_management_permissions(self):
        from apps.org.services import user_permissions

        self.user.assign_role(self.manager_role)
        rows = {row["resource"]: row["verbs"] for row in user_permissions(self.user.pk)["permissions"]}
        self.assertIn("persons.person", rows)
        self.assertTrue(rows["persons.person"]["view"])
