import io
from datetime import timedelta

from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from apps.accounts.admin import UserRoleAdminForm
from apps.accounts.models import Role, User, UserRole


class OfficialCodeConstraintTests(TestCase):
    def test_live_user_employee_code_is_unique_in_database(self):
        User.objects.create_user(
            username="employee-code-one", password="x", employee_code="EMP-42",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                User.objects.create_user(
                    username="employee-code-two", password="x", employee_code="EMP-42",
                )

    def test_soft_deleted_user_does_not_reserve_employee_code(self):
        User.objects.create_user(
            username="employee-code-deleted", password="x",
            employee_code="EMP-43", is_deleted=True,
        )
        User.objects.create_user(
            username="employee-code-reused", password="x", employee_code="EMP-43",
        )


class LegacyRoleLifecycleTests(TestCase):
    def test_seed_roles_does_not_reactivate_disabled_legacy_role(self):
        Role.objects.create(code="hr", name="منابع انسانی", is_active=False)

        call_command("seed_roles", stdout=io.StringIO())

        self.assertFalse(Role.objects.get(code="hr").is_active)

    def test_audit_reports_active_legacy_assignments(self):
        role = Role.objects.create(code="hr", name="منابع انسانی")
        user = User.objects.create_user(username="legacy-hr", password="x")
        UserRole.objects.create(user=user, role=role)

        output = io.StringIO()
        call_command("audit_legacy_roles", stdout=output)

        report = output.getvalue()
        self.assertIn("hr: active=True deleted=False", report)
        self.assertIn("user=legacy-hr role=hr active=True", report)

    def test_audit_hides_inactive_assignments_by_default(self):
        role = Role.objects.create(code="hr", name="منابع انسانی")
        user = User.objects.create_user(username="old-hr", password="x")
        UserRole.objects.create(user=user, role=role, is_active=False)

        output = io.StringIO()
        call_command("audit_legacy_roles", stdout=output)

        self.assertNotIn("user=old-hr", output.getvalue())

    def test_audit_hides_expired_assignments_by_default(self):
        role = Role.objects.create(code="hr", name="منابع انسانی")
        user = User.objects.create_user(username="expired-hr", password="x")
        UserRole.objects.create(
            user=user,
            role=role,
            valid_to=timezone.now() - timedelta(minutes=1),
        )

        output = io.StringIO()
        call_command("audit_legacy_roles", stdout=output)

        self.assertNotIn("user=expired-hr", output.getvalue())

    def test_admin_role_form_hides_new_legacy_assignment_but_keeps_existing_one(self):
        hr_role = Role.objects.create(code="hr", name="منابع انسانی")
        manager_role = Role.objects.create(code="manager", name="مدیر")

        new_form = UserRoleAdminForm()
        self.assertNotIn(hr_role.pk, new_form.fields["role"].queryset.values_list("pk", flat=True))
        self.assertIn(manager_role.pk, new_form.fields["role"].queryset.values_list("pk", flat=True))

        user = User.objects.create_user(username="legacy-admin", password="x")
        assignment = UserRole.objects.create(user=user, role=hr_role)
        existing_form = UserRoleAdminForm(instance=assignment)
        self.assertIn(hr_role.pk, existing_form.fields["role"].queryset.values_list("pk", flat=True))
