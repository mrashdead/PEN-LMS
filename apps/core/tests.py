"""Unit tests for custom permission classes — pure, no DB needed."""
from __future__ import annotations

from unittest.mock import MagicMock, create_autospec

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.core.group_permissions import (
    StrictDjangoModelPermissions,
    HasGroupPermission,
)
from apps.core.permissions import (
    IsActiveUser,
    HasAnyRole,
    IsManagerOrAdmin,
    IsAcademicManager,
    IsWorkflowParticipant,
    IsPersonOwnerOrManager,
    CanCreateUserForPerson,
    CanManageWorkflow,
    CanAccessPersons,
    CanManageStudentParent,
)

User = get_user_model()


class MockUser:
    """Replace with anonymous user pattern tests."""

    def __init__(self, roles=None, pk="u1", is_active=True, is_deleted=False):
        self.pk = pk
        self.id = pk
        self._roles = roles or set()
        self.is_authenticated = True
        self.is_active = is_active
        self.is_deleted = is_deleted
        self.is_superuser = False
        self._perms = set()

    def role_codes(self):
        return self._roles

    def has_perm(self, perm):
        return perm in self._perms

    def has_perms(self, perm_list):
        return all(p in self._perms for p in perm_list)


class MockRequest:
    def __init__(self, user=None, method="GET"):
        self.user = user or MockUser()
        self.method = method
        self.META = {}
        self.session = {}


class MockView:
    def __init__(self, **attrs):
        for k, v in attrs.items():
            setattr(self, k, v)


# ─── IsActiveUser ──────────────────────────────────────────────


class IsActiveUserTest(TestCase):
    def setUp(self):
        self.perm = IsActiveUser()
        self.view = MockView()

    def test_active_authenticated_allowed(self):
        req = MockRequest(user=MockUser(is_active=True, is_deleted=False))
        self.assertTrue(self.perm.has_permission(req, self.view))

    def test_inactive_denied(self):
        req = MockRequest(user=MockUser(is_active=False, is_deleted=False))
        self.assertFalse(self.perm.has_permission(req, self.view))

    def test_deleted_denied(self):
        req = MockRequest(user=MockUser(is_active=True, is_deleted=True))
        self.assertFalse(self.perm.has_permission(req, self.view))

    def test_unauthenticated_denied(self):
        user = MockUser()
        user.is_authenticated = False
        req = MockRequest(user=user)
        self.assertFalse(self.perm.has_permission(req, self.view))


# ─── HasAnyRole ───────────────────────────────────────────────


class HasAnyRoleTest(TestCase):
    def setUp(self):
        self.perm = HasAnyRole()
        self.view = MockView()

    def test_required_role_allowed(self):
        self.view.required_roles = {"manager"}
        req = MockRequest(user=MockUser(roles={"manager"}))
        self.assertTrue(self.perm.has_permission(req, self.view))

    def test_wrong_role_denied(self):
        self.view.required_roles = {"manager"}
        req = MockRequest(user=MockUser(roles={"student"}))
        self.assertFalse(self.perm.has_permission(req, self.view))

    def test_empty_required_roles_anyone(self):
        self.view.required_roles = set()
        req = MockRequest(user=MockUser(roles={"student"}))
        self.assertTrue(self.perm.has_permission(req, self.view))

    def test_no_required_roles_attr_anyone(self):
        class CleanView:
            pass

        req = MockRequest(user=MockUser(roles={"student"}))
        self.assertTrue(self.perm.has_permission(req, CleanView()))


# ─── Academic & Manager Permissions ───────────────────────────


class IsManagerOrAdminTest(TestCase):
    def setUp(self):
        self.perm = IsManagerOrAdmin()
        self.view = MockView()

    def test_manager_allowed(self):
        req = MockRequest(user=MockUser(roles={"manager"}))
        self.assertTrue(self.perm.has_permission(req, self.view))

    def test_student_denied(self):
        req = MockRequest(user=MockUser(roles={"student"}))
        self.assertFalse(self.perm.has_permission(req, self.view))


class IsAcademicManagerTest(TestCase):
    def setUp(self):
        self.perm = IsAcademicManager()
        self.view = MockView()

    def test_teacher_read_allowed(self):
        req = MockRequest(user=MockUser(roles={"teacher"}), method="GET")
        self.assertTrue(self.perm.has_permission(req, self.view))

    def test_teacher_write_denied(self):
        req = MockRequest(user=MockUser(roles={"teacher"}), method="POST")
        self.assertFalse(self.perm.has_permission(req, self.view))

    def test_manager_write_allowed(self):
        req = MockRequest(user=MockUser(roles={"manager"}), method="PATCH")
        self.assertTrue(self.perm.has_permission(req, self.view))


class IsWorkflowParticipantTest(TestCase):
    def setUp(self):
        self.perm = IsWorkflowParticipant()
        self.view = MockView()

    def test_elevated_role_ok(self):
        req = MockRequest(user=MockUser(roles={"workflow_admin"}))
        self.assertTrue(self.perm.has_permission(req, self.view))

    # object-level tests in next function


class IsPersonOwnerOrManagerTest(TestCase):
    def setUp(self):
        self.perm = IsPersonOwnerOrManager()
        self.view = MockView()

    def test_safe_method_anyone(self):
        req = MockRequest(user=MockUser(roles={"student"}), method="GET")
        self.assertTrue(self.perm.has_permission(req, self.view))

    def test_self_write_ok(self):
        user = MockUser(roles={"student"}, pk="u1")
        req = MockRequest(user=user, method="PATCH")
        obj = MagicMock()
        obj.user_id = "u1"
        self.assertTrue(self.perm.has_object_permission(req, self.view, obj))

    def test_other_student_write_denied(self):
        user = MockUser(roles={"student"}, pk="u1")
        req = MockRequest(user=user, method="PATCH")
        obj = MagicMock()
        obj.user_id = "u2"
        self.assertFalse(self.perm.has_object_permission(req, self.view, obj))


class CanCreateUserForPersonTest(TestCase):
    def test_manager_allowed(self):
        req = MockRequest(user=MockUser(roles={"manager"}))
        self.assertTrue(CanCreateUserForPerson().has_permission(req, MockView()))

    def test_employee_denied(self):
        req = MockRequest(user=MockUser(roles={"employee"}))
        self.assertFalse(CanCreateUserForPerson().has_permission(req, MockView()))


class CanAccessPersonsTest(TestCase):
    def test_student_read_allowed(self):
        req = MockRequest(user=MockUser(roles={"student"}), method="GET")
        self.assertTrue(CanAccessPersons().has_permission(req, MockView()))

    def test_student_write_denied(self):
        req = MockRequest(user=MockUser(roles={"student"}), method="POST")
        self.assertFalse(CanAccessPersons().has_permission(req, MockView()))

    def test_manager_write_allowed(self):
        req = MockRequest(user=MockUser(roles={"manager"}), method="POST")
        self.assertTrue(CanAccessPersons().has_permission(req, MockView()))


class CanManageStudentParentTest(TestCase):
    def test_manager_allowed(self):
        req = MockRequest(user=MockUser(roles={"manager"}))
        self.assertTrue(CanManageStudentParent().has_permission(req, MockView()))

    def test_teacher_denied(self):
        req = MockRequest(user=MockUser(roles={"teacher"}))
        self.assertFalse(CanManageStudentParent().has_permission(req, MockView()))


class CanManageWorkflowTest(TestCase):
    def test_workflow_admin_allowed(self):
        req = MockRequest(user=MockUser(roles={"workflow_admin"}))
        self.assertTrue(CanManageWorkflow().has_permission(req, MockView()))

    def test_employee_denied(self):
        req = MockRequest(user=MockUser(roles={"employee"}))
        self.assertFalse(CanManageWorkflow().has_permission(req, MockView()))


# ─── Group Permissions ────────────────────────────────────────


class HasGroupPermissionTest(TestCase):
    def setUp(self):
        self.perm = HasGroupPermission()
        self.view = MockView()

    def test_superuser_bypasses(self):
        user = MockUser(roles={"student"})
        user.is_superuser = True
        req = MockRequest(user=user, method="DELETE")
        self.assertTrue(self.perm.has_permission(req, self.view))

    def test_no_required_perms_allows(self):
        self.view.required_permissions = {}
        req = MockRequest(user=MockUser(roles={"student"}), method="GET")
        self.assertTrue(self.perm.has_permission(req, self.view))

    def test_missing_perm_denied(self):
        self.view.required_permissions = {"GET": ["persons.view_person"]}
        user = MockUser(roles={"student"})
        req = MockRequest(user=user, method="GET")
        self.assertFalse(self.perm.has_permission(req, self.view))

    def test_has_perm_allowed(self):
        self.view.required_permissions = {"GET": ["persons.view_person"]}
        user = MockUser(roles={"student"})
        user._perms.add("persons.view_person")
        req = MockRequest(user=user, method="GET")
        self.assertTrue(self.perm.has_permission(req, self.view))


# ─── StrictDjangoModelPermissions ─────────────────────────────


class StrictDjangoModelPermissionsTest(TestCase):
    def setUp(self):
        self.perm = StrictDjangoModelPermissions()
        self.model_cls = MagicMock()
        self.model_cls._meta.app_label = "persons"
        self.model_cls._meta.model_name = "person"
        self.queryset = MagicMock(model=self.model_cls)

    def test_superuser_bypass(self):
        user = MockUser(roles={"student"})
        user.is_superuser = True
        req = MockRequest(user=user, method="DELETE")
        view = MockView(queryset=self.queryset)
        self.assertTrue(self.perm.has_permission(req, view))

    def test_has_model_perm(self):
        user = MockUser(roles={"student"})
        user._perms.update({"persons.add_person", "persons.view_person"})
        req = MockRequest(user=user, method="POST")
        view = MockView(queryset=self.queryset)
        self.assertTrue(self.perm.has_permission(req, view))

    def test_missing_model_perm(self):
        user = MockUser(roles={"student"})
        req = MockRequest(user=user, method="DELETE")
        view = MockView(queryset=self.queryset)
        self.assertFalse(self.perm.has_permission(req, view))