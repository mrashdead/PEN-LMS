"""Default model permissions for effective management roles.

This backend only adds the existing management policy; authentication and
explicit user/group permissions continue through Django's ModelBackend.
Business-role, row-scope and object checks remain in their existing views.
"""
from __future__ import annotations

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import Permission

from apps.accounts.permission_policy import GROUPS, MANAGEMENT_ROLE_GROUPS


class ManagementRolePermissionBackend(BaseBackend):
    def get_group_permissions(self, user_obj, obj=None):
        if (
            obj is not None
            or not user_obj.is_authenticated
            or not user_obj.is_active
            or getattr(user_obj, "is_deleted", False)
        ):
            return set()

        # Re-evaluate effective roles, including validity windows, on every
        # check. Never persist derived grants or cache them on the user: a
        # revoked/expired role must stop granting even on the same instance.
        roles = user_obj.role_codes()
        wanted = set()
        all_permissions = False
        for role_code, group_name in MANAGEMENT_ROLE_GROUPS.items():
            if role_code not in roles:
                continue
            policy = GROUPS[group_name]["perms"]
            if policy == "*":
                all_permissions = True
                break
            wanted.update(policy)

        if not all_permissions and not wanted:
            return set()

        permissions = Permission.objects.all()
        if not all_permissions:
            permissions = permissions.filter(
                content_type__app_label__in={perm.split(".", 1)[0] for perm in wanted},
                codename__in={perm.split(".", 1)[1] for perm in wanted},
            )
        existing = {
            f"{app_label}.{codename}"
            for app_label, codename in permissions.values_list("content_type__app_label", "codename")
        }
        return existing if all_permissions else existing & wanted

    def has_module_perms(self, user_obj, app_label):
        return any(
            perm.split(".", 1)[0] == app_label
            for perm in self.get_group_permissions(user_obj)
        )
