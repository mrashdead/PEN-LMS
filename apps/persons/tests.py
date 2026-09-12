"""HTTP-level authorization + PII masking tests for the persons API (B1/B5).

These tests use the SAME conventions as apps/forms/tests/factories.py:
UserFactory with seeded role codes, make_person-style Person rows.
Run with the project's test settings (PostgreSQL or DB_ENGINE=sqlite3).
"""
from __future__ import annotations

import itertools

from django.test import TestCase

from apps.persons.models import Person, StudentParent

_nc_counter = itertools.count(1)


def _next_nc() -> str:
    """Unique 10-digit national code across the whole test run."""
    return f"{8000000000 + next(_nc_counter)}"


def grant_persons_model_perms(user):
    """
    Assign the BASE persons model permissions so StrictDjangoModelPermissions
    passes. Deliberately EXCLUDES the custom ``view_person_detail`` perm: the
    masking logic is driven by business ROLE, and granting the custodian perm
    here would let every test user read raw PII and defeat the point.
    """
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    wanted = {"add_person", "change_person", "delete_person", "view_person",
              "view_person_list"}
    perms = list(
        Permission.objects.filter(
            content_type=ContentType.objects.get_for_model(Person),
            codename__in=wanted,
        )
    )
    perms += list(
        Permission.objects.filter(
            content_type=ContentType.objects.get_for_model(StudentParent)
        )
    )
    user.user_permissions.set(perms)
    for attr in ("_user_perm_cache", "_group_perm_cache", "_perm_cache"):
        if hasattr(user, attr):
            delattr(user, attr)


class _BasePersonsAPITest(TestCase):
    def setUp(self):
        from apps.accounts.models import Role
        from apps.forms.tests.factories import UserFactory

        # Ensure the role codes used here exist (seed_roles equivalent).
        for code in ("employee", "manager", "hr", "workflow_admin",
                     "student", "teacher", "parent"):
            Role.objects.get_or_create(
                code=code, defaults={"name": code, "priority": 50}
            )

        self.manager = UserFactory(username="piim-manager", roles=["manager"])
        self.student = UserFactory(username="piim-student", roles=["student"])
        self.parent = UserFactory(username="piim-parent", roles=["parent"])
        self.teacher = UserFactory(username="piim-teacher", roles=["teacher"])
        self.other_student = UserFactory(username="piim-student2", roles=["student"])

        # The manager acts as custodian without needing a Person row.
        self.target = Person.objects.create(
            national_code=_next_nc(),
            first_name="حسین",
            last_name="هدف",
            mobile="09121110000",
            email="hossein.target@example.com",
            address="تهران، خیابان آزمایشی، پلاک ۱۲",
            postal_code="1234567890",
            person_type=Person.Type.STUDENT,
            student_code=f"S-{_next_nc()}",
        )
        # Give every test user a Person of their own (self-visibility path).
        for user, ptype in (
            (self.student, Person.Type.STUDENT),
            (self.parent, Person.Type.PARENT),
            (self.teacher, Person.Type.TEACHER),
            (self.other_student, Person.Type.STUDENT),
        ):
            person = Person.objects.create(
                national_code=_next_nc(),
                first_name="خود",
                last_name=user.username,
                mobile="09120000000",
                person_type=ptype,
            )
            person.user = user
            person.save(update_fields=["user", "updated_at"])

    def _login(self, user):
        grant_persons_model_perms(user)
        self.client.force_login(user)

    # ── B1: raw PII is masked / unreachable for non-custodians ─────────

    def test_student_cannot_reach_another_students_record(self):
        # Scoping: a student's person-API world is their own record only —
        # another student's detail is a 404 (existence not leaked).
        self._login(self.student)
        response = self.client.get(f"/api/persons/{self.target.pk}/")
        self.assertIn(response.status_code, (403, 404))

    def test_teacher_sees_masked_pii_in_directory_list(self):
        # teacher CAN list the active directory (scoped), but PII arrives
        # masked because the teacher is not the custodian of the row.
        self._login(self.teacher)
        response = self.client.get("/api/persons/")
        self.assertEqual(response.status_code, 200)
        rows = response.json()["results"]
        target = next(r for r in rows if r["id"] == str(self.target.pk))
        self.assertNotEqual(target["national_code"], self.target.national_code)
        self.assertIn("*", target["national_code"])
        self.assertNotEqual(target["mobile"], self.target.mobile)

    def test_student_cannot_list_other_persons(self):
        self._login(self.student)
        response = self.client.get("/api/persons/")
        self.assertEqual(response.status_code, 200)
        ids = {row["id"] for row in response.json()["results"]}
        own_person = self.student.person
        self.assertIn(str(own_person.pk), ids)
        self.assertNotIn(str(self.target.pk), ids)

    def test_parent_sees_own_children_with_full_detail(self):
        StudentParent.objects.create(
            parent=self.parent.person, student=self.target, relation="پدر"
        )
        self._login(self.parent)
        response = self.client.get(f"/api/persons/{self.target.pk}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Parent is a custodian of their child's record.
        self.assertEqual(data["national_code"], self.target.national_code)
        self.assertEqual(data["mobile"], self.target.mobile)

    def test_parent_cannot_read_unrelated_child(self):
        self._login(self.parent)
        response = self.client.get(f"/api/persons/{self.target.pk}/")
        # No StudentParent link → row must not even be reachable (404, not
        # 403, so existence is not leaked).
        self.assertIn(response.status_code, (403, 404))

    def test_masked_output_shape(self):
        # The mask keeps a recognisable prefix/suffix but hides the body.
        self._login(self.teacher)
        response = self.client.get("/api/persons/")
        rows = response.json()["results"]
        target = next(r for r in rows if r["id"] == str(self.target.pk))
        nc = self.target.national_code
        self.assertEqual(target["national_code"], f"{nc[:3]}*****{nc[-2:]}")

    def test_manager_reads_full_pii(self):
        self._login(self.manager)
        response = self.client.get(f"/api/persons/{self.target.pk}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["national_code"], self.target.national_code)
        self.assertEqual(data["address"], self.target.address)

    def test_teacher_reads_masked_pii_of_unrelated_person(self):
        self._login(self.teacher)
        response = self.client.get(f"/api/persons/{self.target.pk}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertNotEqual(data["national_code"], self.target.national_code)
        self.assertIn("*", data["national_code"])

    # ── B5: soft-deleted persons free their national code ───────────────

    def test_national_code_reusable_after_soft_delete(self):
        from apps.persons.services import PersonService

        service = PersonService()
        deleted = Person.objects.create(
            national_code=_next_nc(),
            first_name="حذف",
            last_name="شده",
            mobile="09123330000",
            person_type=Person.Type.STUDENT,
        )
        deleted.delete()  # soft delete → is_deleted=True
        # Creating a NEW person with the same national code must succeed.
        reused = service.create_person(
            national_code=deleted.national_code,
            first_name="مجدداً",
            last_name="ثبت‌شده",
            person_type=Person.Type.STUDENT,
            mobile="09124440000",
        )
        self.assertEqual(reused.national_code, deleted.national_code)

    def test_create_duplicate_national_code_returns_400_not_500(self):
        self._login(self.manager)
        response = self.client.post(
            "/api/persons/",
            {
                "national_code": self.target.national_code,
                "first_name": "تکراری",
                "last_name": "کدملی",
                "person_type": "student",
                "mobile": "09125550000",
                "student_code": f"S-{_next_nc()}",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400, response.content)
        self.assertIn("national_code", response.json())

    def test_soft_delete_does_not_remove_person_row(self):
        self.target.delete()
        # Row still exists for audit (hard delete requires hard_delete()).
        self.assertTrue(
            Person.all_objects.filter(pk=self.target.pk, is_deleted=True).exists()
        )
