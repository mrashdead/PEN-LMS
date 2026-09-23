"""Tests for organizational read-models + delegation."""
from __future__ import annotations

from datetime import timedelta

from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.org import services
from apps.org.models import Delegation


class OrgServicesTest(TestCase):
    def setUp(self):
        self.manager_role = Role.objects.create(code="manager", name="مدیر")
        self.employee_role = Role.objects.create(code="employee", name="کارمند")
        self.boss = User.objects.create_user(username="boss", password="x", first_name="علی", department="آموزش")
        self.staff = User.objects.create_user(username="staff", password="x", first_name="رضا", department="آموزش", manager=self.boss)
        self.boss.assign_role(self.manager_role.code)
        self.staff.assign_role(self.employee_role.code)

    def test_org_chart_roots_and_reports(self):
        chart = services.org_chart()
        # boss is a root (no manager); staff hangs under boss
        self.assertEqual(len(chart), 1)
        self.assertEqual(chart[0]["username"], "boss")
        self.assertEqual([c["username"] for c in chart[0]["reports"]], ["staff"])

    def test_departments_count(self):
        deps = {d["department"]: d["count"] for d in services.departments()}
        self.assertEqual(deps.get("آموزش"), 2)

    def test_profile_includes_roles_and_manager(self):
        p = services.person_profile(self.staff.pk)
        self.assertEqual(p["manager"], "علی")
        self.assertIn("employee", p["roles"])

    def test_matrix_has_group_rows(self):
        # seed a group with a persons permission
        g = Group.objects.create(name="کارمند")
        g.permissions.add(Permission.objects.get(codename="view_person"))
        m = services.permission_matrix()
        row = next(r for r in m["rows"] if r["group"] == "کارمند")
        self.assertTrue(row["resources"]["persons"]["view"])
        self.assertFalse(row["resources"]["persons"]["add"])

    def test_simulator_denies_without_perm(self):
        res = services.simulate_access(self.staff.pk, "schemas", "add")
        self.assertFalse(res["allowed"])

    def test_simulator_allows_elevated_schema_add(self):
        # give boss the group perm that gates schema creation
        g = Group.objects.create(name="مدیر")
        g.permissions.add(Permission.objects.get(codename="add_formschema"))
        self.boss.groups.add(g)
        res = services.simulate_access(self.boss.pk, "schemas", "add")
        self.assertTrue(res["allowed"])

    def test_legacy_hr_role_is_not_an_assignment_option(self):
        Role.objects.create(code="hr", name="منابع انسانی")

        self.assertNotIn("hr", {row["code"] for row in services.all_roles()})

    def test_new_hr_assignment_is_rejected_without_revoking_existing_roles(self):
        with self.assertRaisesMessage(ValueError, "برای تخصیص جدید غیرفعال هستند"):
            services.set_user_roles(
                user_id=self.staff.pk,
                role_codes=["employee", "hr"],
                actor=self.boss,
            )

        self.assertEqual(self.staff.role_codes(), {"employee"})

    def test_existing_hr_assignment_can_be_retained_during_migration(self):
        Role.objects.create(code="hr", name="منابع انسانی")
        self.staff.assign_role("hr", assigned_by=self.boss)

        result = services.set_user_roles(
            user_id=self.staff.pk,
            role_codes=["employee", "hr"],
            actor=self.boss,
        )

        self.assertEqual(set(result["roles"]), {"employee", "hr"})

    def test_unit_performance_groups_by_department(self):
        from apps.tasks.models import WorkflowTask  # noqa: F401 (ensure import ok)
        perf = services.unit_performance()
        # no tasks yet → empty (or zero-rate rows); just assert shape
        self.assertIsInstance(perf, list)


class DelegationTest(TestCase):
    def setUp(self):
        self.a = User.objects.create_user(username="a", password="x")
        self.b = User.objects.create_user(username="b", password="x")

    def test_create_and_list(self):
        now = timezone.now()
        d = services.create_delegation(
            principal_id=self.a.pk, delegate_id=self.b.pk,
            department="آموزش", workflow_code="", reason="مرخصی",
            valid_from=now - timedelta(days=1), valid_to=now + timedelta(days=5),
            actor=self.a,
        )
        self.assertTrue(d.is_live)
        rows = services.list_delegations()
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["is_live"])

    def test_self_delegation_rejected(self):
        from django.core.exceptions import ValidationError
        now = timezone.now()
        with self.assertRaises(ValidationError):
            services.create_delegation(
                principal_id=self.a.pk, delegate_id=self.a.pk,
                department="x", workflow_code="", reason="",
                valid_from=now, valid_to=now + timedelta(days=1), actor=self.a,
            )

    def test_requires_scope(self):
        from django.core.exceptions import ValidationError
        now = timezone.now()
        with self.assertRaises(ValidationError):
            services.create_delegation(
                principal_id=self.a.pk, delegate_id=self.b.pk,
                department="", workflow_code="", reason="",
                valid_from=now, valid_to=now + timedelta(days=1), actor=self.a,
            )

    def test_revoke(self):
        now = timezone.now()
        d = services.create_delegation(
            principal_id=self.a.pk, delegate_id=self.b.pk,
            department="آموزش", workflow_code="", reason="",
            valid_from=now, valid_to=now + timedelta(days=2), actor=self.a,
        )
        self.assertTrue(services.revoke_delegation(delegation_id=d.pk, actor=self.a))
        d.refresh_from_db()
        self.assertFalse(d.is_active)
        self.assertIsNotNone(d.revoked_at)


class OrgAPITest(TestCase):
    def setUp(self):
        self.manager_role = Role.objects.create(code="manager", name="مدیر")
        self.student_role = Role.objects.create(code="student", name="دانش")
        self.boss = User.objects.create_user(username="boss", password="x")
        self.student = User.objects.create_user(username="stud", password="x")
        self.boss.assign_role(self.manager_role.code)
        self.student.assign_role(self.student_role.code)

    def test_chart_requires_staff(self):
        self.client.force_login(self.student)
        r = self.client.get("/api/org/chart/")
        self.assertEqual(r.status_code, 403)

    def test_chart_ok_for_manager(self):
        self.client.force_login(self.boss)
        r = self.client.get("/api/org/chart/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("chart", r.json())

    def test_simulate_elevated_only(self):
        self.client.force_login(self.boss)
        r = self.client.post(
            "/api/org/permissions/simulate/",
            {"user": str(self.boss.pk), "resource": "persons", "verb": "view"},
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn("allowed", r.json())

    def test_delegation_create_via_api(self):
        self.client.force_login(self.boss)
        now = timezone.now()
        r = self.client.post(
            "/api/org/delegations/",
            {
                "principal": str(self.boss.pk), "delegate": str(self.student.pk),
                "department": "آموزش", "workflow_code": "", "reason": "مرخصی",
                "valid_from": (now - timedelta(days=1)).isoformat(),
                "valid_to": (now + timedelta(days=3)).isoformat(),
            },
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 201)
        self.assertEqual(Delegation.objects.count(), 1)
