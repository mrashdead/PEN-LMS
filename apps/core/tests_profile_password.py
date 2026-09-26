"""Coverage for the shared profile and password recovery surfaces."""
from __future__ import annotations

from django.test import TestCase

from apps.forms.tests.factories import UserFactory, make_person


class ProfileAndPasswordPageTests(TestCase):
    def setUp(self):
        self.admin = UserFactory(username="profile-admin", roles=["manager"])
        self.employee = UserFactory(username="profile-employee", roles=["employee"])
        self.student = UserFactory(username="profile-student", roles=["student"])
        make_person(
            user=self.student,
            person_type="student",
            first_name="سارا",
            last_name="آزمون",
            national_code="1234567890",
        )

    def test_profile_is_available_to_a_learner(self):
        self.client.force_login(self.student)
        response = self.client.get("/workspace/profile/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "پنل کاربری من")
        self.assertContains(response, "سارا")

    def test_password_management_is_admin_only(self):
        self.client.force_login(self.employee)
        self.assertEqual(self.client.get("/workspace/password-management/").status_code, 403)

        self.client.force_login(self.admin)
        response = self.client.get("/workspace/password-management/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "سارا آزمون")
        self.assertContains(response, f'data-username="{self.student.username}"')
        self.assertRegex(
            response.content.decode(),
            r'<input[^>]*id="password-target-username"[^>]*readonly',
        )

        response = self.client.post(
            "/workspace/password-management/",
            {
                "target_user": str(self.student.pk),
                "new_password1": "A-safe-new-password-9876",
                "new_password2": "A-safe-new-password-9876",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.student.refresh_from_db()
        self.assertTrue(self.student.check_password("A-safe-new-password-9876"))

    def test_forgot_password_pages_are_public(self):
        response = self.client.get("/dashboard/password/reset/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "فراموشی رمز عبور")
