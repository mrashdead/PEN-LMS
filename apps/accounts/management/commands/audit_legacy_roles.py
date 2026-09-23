"""Report legacy role records and their active user assignments."""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from apps.accounts.models import Role, UserRole
from apps.accounts.role_policy import LEGACY_ROLE_CODES


class Command(BaseCommand):
    help = "Audit legacy roles and active UserRole assignments without changing data"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--all-assignments",
            action="store_true",
            help="Include inactive and expired UserRole records as well.",
        )

    def handle(self, *args, **options) -> None:
        legacy_roles = Role.all_objects.filter(
            code__in=LEGACY_ROLE_CODES,
        ).order_by("code", "-is_deleted", "-updated_at")
        assignments = UserRole.objects.filter(
            role__code__in=LEGACY_ROLE_CODES,
        ).select_related("role", "user", "assigned_by")
        if not options["all_assignments"]:
            now = timezone.now()
            assignments = assignments.filter(
                is_active=True,
            ).filter(
                Q(valid_from__isnull=True) | Q(valid_from__lte=now),
                Q(valid_to__isnull=True) | Q(valid_to__gte=now),
            )
        assignments = assignments.order_by("user__username", "role__code")

        self.stdout.write("Legacy roles:")
        role_count = 0
        for role in legacy_roles:
            role_count += 1
            self.stdout.write(
                "- {code}: active={active} deleted={deleted}".format(
                    code=role.code,
                    active=role.is_active,
                    deleted=role.is_deleted,
                )
            )
        if role_count == 0:
            self.stdout.write("- none")

        self.stdout.write(
            "UserRole assignments{scope}:".format(
                scope=" (all records)" if options["all_assignments"] else " (active only)"
            )
        )
        assignment_count = 0
        for assignment in assignments:
            assignment_count += 1
            assigned_by = assignment.assigned_by.username if assignment.assigned_by else "-"
            self.stdout.write(
                "- user={user} role={role} active={active} valid_from={valid_from} "
                "valid_to={valid_to} assigned_by={assigned_by}".format(
                    user=assignment.user.username,
                    role=assignment.role.code,
                    active=assignment.is_active,
                    valid_from=assignment.valid_from or "-",
                    valid_to=assignment.valid_to or "-",
                    assigned_by=assigned_by,
                )
            )
        if assignment_count == 0:
            self.stdout.write("- none")

        self.stdout.write(
            self.style.SUCCESS(
                f"audit complete: {role_count} role(s), {assignment_count} assignment(s)"
            )
        )
