"""
Seed the workflow definitions used by form schemas.

    python manage.py seed_form_workflows [--dry-run] [--force]

Creates (idempotently, via get_or_create) the three workflow definitions the
form catalog references, using the EXISTING engine models (WorkflowDefinition,
State, Transition) and its role-code conventions:

  form-approval      new → pending-manager → done      (تعریف درس/دوره/برگزاری)
                     approve: manager, hr, workflow_admin; reject: manager, hr, workflow_admin
  form-review        new → pending-manager → done      (حضور و غیاب/کارنامه)
                     approve/reject: manager, workflow_admin
  lead-assessment    new → assessed → enrolled/closed  (تعیین سطح)
                     assess: employee, hr, manager, workflow_admin
                     enroll: employee, hr, manager, workflow_admin
                     close:  employee, hr, manager, workflow_admin

Roles must already exist (seed_roles). Transitions carry empty guard
expressions; the engine treats unknown/empty guards per its own fail-closed
rules. Never executes or mutates instances — definitions only.
"""
from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import Role
from apps.workflow.models import State, Transition, WorkflowDefinition

# (workflow_code, name) → list of (state_code, state_name, is_initial, is_final)
WORKFLOW_BLUEPRINTS: dict[str, dict[str, Any]] = {
    "form-approval": {
        "name": "تأیید فرم‌های آموزشی",
        "states": [
            ("new", "جدید", True, False),
            ("pending-manager", "در انتظار تأیید مدیر", False, False),
            ("done", "پایان", False, True),
        ],
        # (name, from_state, to_state, allowed_role_codes, kind)
        "transitions": [
            ("submit", "new", "pending-manager", ["employee", "hr", "manager", "workflow_admin"], "submit"),
            ("approve", "pending-manager", "done", ["manager", "hr", "workflow_admin"], "approve"),
            ("reject", "pending-manager", "done", ["manager", "hr", "workflow_admin"], "reject"),
        ],
    },
    "form-review": {
        "name": "بازبینی فرم‌های کلاسی",
        "states": [
            ("new", "ثبت‌شده", True, False),
            ("pending-manager", "در انتظار بازبینی مدیر", False, False),
            ("done", "پایان", False, True),
        ],
        "transitions": [
            ("submit", "new", "pending-manager", ["teacher", "manager"], "submit"),
            ("approve", "pending-manager", "done", ["manager", "workflow_admin"], "approve"),
            ("reject", "pending-manager", "done", ["manager", "workflow_admin"], "reject"),
        ],
    },
    "lead-assessment": {
        "name": "تعیین سطح لید",
        "states": [
            ("new", "جدید", True, False),
            ("assessed", "ارزیابی‌شده", False, False),
            ("enrolled", "ثبت‌نام‌شده", False, True),
            ("closed", "بسته‌شده", False, True),
        ],
        "transitions": [
            ("assess", "new", "assessed",
             ["employee", "hr", "manager", "workflow_admin"], ""),
            ("enroll", "assessed", "enrolled",
             ["employee", "hr", "manager", "workflow_admin"], "complete"),
            ("close", "assessed", "closed",
             ["employee", "hr", "manager", "workflow_admin"], "reject"),
        ],
    },
}


class Command(BaseCommand):
    help = "Seed workflow definitions backing the form schemas (idempotent)"

    def add_arguments(self, parser) -> None:
        parser.add_argument("--dry-run", action="store_true",
                            help="Validate without writing anything.")
        parser.add_argument("--force", action="store_true",
                            help="Reset transition role codes to the blueprint "
                                 "(existing transitions keep their codes otherwise).")

    def _preflight(self, wanted: list[str]) -> list[str]:
        """Collect problems before any write; roles must exist up front."""
        problems: list[str] = []
        role_codes: set[str] = set()
        for code in wanted:
            blueprint = WORKFLOW_BLUEPRINTS[code]
            for _n, _f, _t, roles, *_rest in blueprint["transitions"]:
                role_codes.update(roles)
        existing = set(Role.objects.filter(code__in=role_codes).values_list("code", flat=True))
        missing = sorted(role_codes - existing)
        if missing:
            problems.append(
                f"missing role(s): {', '.join(missing)} — run `seed_roles` first."
            )
        return problems

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        wanted = list(WORKFLOW_BLUEPRINTS)
        problems = self._preflight(wanted)
        if problems:
            raise CommandError(
                "seed_form_workflows aborted (no database changes were made):\n  - "
                + "\n  - ".join(problems)
            )

        if options["dry_run"]:
            for code in wanted:
                self.stdout.write(
                    f"[dry-run] would seed workflow '{code}' "
                    f"({len(WORKFLOW_BLUEPRINTS[code]['states'])} states, "
                    f"{len(WORKFLOW_BLUEPRINTS[code]['transitions'])} transitions)"
                )
            self.stdout.write(self.style.SUCCESS("dry-run complete — no writes"))
            return

        for code in wanted:
            blueprint = WORKFLOW_BLUEPRINTS[code]
            definition, created = WorkflowDefinition.objects.get_or_create(
                code=code,
                defaults={
                    "name": blueprint["name"],
                    "is_active": True,
                    "version": 1,
                },
            )
            if created:
                state = "created"
            else:
                definition.is_active = True
                definition.name = blueprint["name"]
                definition.save(update_fields=["is_active", "name", "updated_at"])
                state = "updated"

            states: dict[str, State] = {}
            for state_code, state_name, is_initial, is_final in blueprint["states"]:
                state, _ = State.objects.get_or_create(
                    workflow_definition=definition,
                    code=state_code,
                    defaults={
                        "name": state_name,
                        "is_initial": is_initial,
                        "is_final": is_final,
                    },
                )
                states[state_code] = state

            for transition_spec in blueprint["transitions"]:
                name, from_code, to_code, roles = transition_spec[:4]
                kind = transition_spec[4] if len(transition_spec) > 4 else ""
                transition, t_created = Transition.objects.get_or_create(
                    workflow_definition=definition,
                    from_state=states[from_code],
                    to_state=states[to_code],
                    name=name,
                    defaults={
                        "allowed_role_codes": roles,
                        "requires_comment": False,
                        "guard_expression": {},
                        "kind": kind,
                    },
                )
                if not t_created and options["force"]:
                    transition.allowed_role_codes = roles
                    transition.kind = kind
                    transition.save(
                        update_fields=["allowed_role_codes", "kind", "updated_at"]
                    )

            self.stdout.write(f"[{state}] {code}")

        self.stdout.write(self.style.SUCCESS("form workflows ready"))
