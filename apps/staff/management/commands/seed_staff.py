"""
Seed the staff module's reference data: leave-type catalog and the two
workflow definitions used by the approval pipeline.

    python manage.py seed_staff [--dry-run] [--force]

Idempotent (get_or_create on the business keys). Roles must already exist
(``seed_roles``); workflow blueprints reuse the EXISTING engine models
(WorkflowDefinition/State/Transition) and their role-code conventions — the
same pattern as ``seed_form_workflows``.
"""
from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import Role
from apps.staff.models import LeaveType
from apps.workflow.models import State, Transition, WorkflowDefinition

LEAVE_TYPES: list[dict[str, Any]] = [
    {"code": "annual", "name": "مرخصی استحقاقی", "accrual": "annual",
     "default_days": 26, "requires_document": False},
    {"code": "sick", "name": "مرخصی استعلاجی", "accrual": "sick",
     "default_days": 0, "requires_document": True},
    {"code": "unpaid", "name": "مرخصی بدون حقوق", "accrual": "unpaid",
     "default_days": 0, "requires_document": False},
    {"code": "emergency", "name": "مرخصی اضطراری", "accrual": "annual",
     "default_days": 5, "requires_document": False},
    {"code": "maternity", "name": "مرخصی زایمان", "accrual": "unlimited",
     "default_days": 90, "requires_document": True},
]

WORKFLOW_BLUEPRINTS: dict[str, dict[str, Any]] = {
    "leave-request": {
        "name": "درخواست مرخصی",
        "states": [
            ("draft", "پیش‌نویس", True, False,
             {"strategy": "requester", "fallback_roles": ["employee"]}),
            ("pending-manager", "در انتظار تأیید مدیر مستقیم", False, False,
             {"strategy": "direct_manager", "fallback_roles": ["manager", "supervisor"]}),
            ("pending-hr", "در انتظار تأیید نهایی منابع انسانی", False, False,
             {"strategy": "role", "roles": ["hr"], "fallback_roles": ["manager", "workflow_admin"]}),
            ("approved", "تأییدشده", False, True),
            ("rejected", "ردشده", False, True),
        ],
        "transitions": [
            ("submit", "draft", "pending-manager",
             ["employee", "teacher", "supervisor", "manager", "hr", "workflow_admin"], "submit"),
            ("approve", "pending-manager", "pending-hr",
             ["manager", "supervisor", "workflow_admin"], "approve"),
            ("reject", "pending-manager", "rejected",
             ["manager", "supervisor", "workflow_admin"], "reject"),
            ("approve-final", "pending-hr", "approved",
             ["hr", "manager", "workflow_admin"], "approve"),
            ("reject-final", "pending-hr", "rejected",
             ["hr", "manager", "workflow_admin"], "reject"),
        ],
    },
    "timesheet-review": {
        "name": "بررسی ساعت کاری",
        "states": [
            ("submitted", "ثبت‌شده", True, False,
             {"strategy": "direct_manager", "fallback_roles": ["manager", "supervisor"]}),
            ("pending-correction", "نیازمند اصلاح", False, False,
             {"strategy": "requester", "fallback_roles": ["employee"]}),
            ("approved", "تأییدشده", False, True),
            ("rejected", "ردشده", False, True),
        ],
        "transitions": [
            ("review", "submitted", "approved",
             ["manager", "supervisor", "workflow_admin", "hr"], "approve"),
            ("reject", "submitted", "rejected",
             ["manager", "supervisor", "workflow_admin", "hr"], "reject"),
            ("return", "submitted", "pending-correction",
             ["manager", "supervisor", "workflow_admin", "hr"], "return"),
            ("resubmit", "pending-correction", "submitted",
             ["employee", "teacher", "supervisor", "manager"], "submit"),
        ],
    },
}


class Command(BaseCommand):
    help = "Seed staff reference data (leave types + approval workflows) — idempotent"

    def add_arguments(self, parser) -> None:
        parser.add_argument("--dry-run", action="store=True",
                            help="Validate without writing anything.")
        parser.add_argument("--force", action="store=True",
                            help="Reset transition role codes to the blueprint.")

    def _preflight(self) -> list[str]:
        problems: list[str] = []
        role_codes: set[str] = set()
        for blueprint in WORKFLOW_BLUEPRINTS.values():
            for _n, _f, _t, roles, *_rest in blueprint["transitions"]:
                role_codes.update(roles)
        existing = set(
            Role.objects.filter(code__in=role_codes).values_list("code", flat=True)
        )
        missing = sorted(role_codes - existing)
        if missing:
            problems.append(
                f"missing role(s): {', '.join(missing)} — run `seed_roles` first."
            )
        return problems

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        dry_run = bool(options.get("dry_run"))
        force = bool(options.get("force"))
        problems = self._preflight()
        if problems:
            raise CommandError(
                "seed_staff aborted (no database changes were made):\n  - "
                + "\n  - ".join(problems)
            )
        if dry_run:
            self.stdout.write(self.style.WARNING("[dry-run] validation OK"))
            return

        # ── Leave types ───────────────────────────────────────────────────
        for spec in LEAVE_TYPES:
            obj = LeaveType.objects.filter(code=spec["code"], is_deleted=False).first()
            if obj is None:
                obj = LeaveType(code=spec["code"])
                created = True
            else:
                created = False
            obj.name = spec["name"]
            obj.accrual = spec["accrual"]
            obj.default_days = spec["default_days"]
            obj.requires_document = spec["requires_document"]
            obj.is_active = True
            obj.is_deleted = False
            obj.deleted_at = None
            obj.save()
            self.stdout.write(
                f"[{'created' if created else 'updated'}] leave-type {obj.code}"
            )

        # ── Workflow definitions ──────────────────────────────────────────
        for code, blueprint in WORKFLOW_BLUEPRINTS.items():
            definition = WorkflowDefinition.objects.filter(
                code=code, is_active=True, is_deleted=False,
            ).first()
            if definition is None:
                definition = WorkflowDefinition.objects.create(
                    code=code, name=blueprint["name"], is_active=True,
                )
                self.stdout.write(f"[created] workflow {code}")
            else:
                self.stdout.write(f"[exists] workflow {code}")

            states: dict[str, State] = {}
            for state_spec in blueprint["states"]:
                state_code, state_name, is_initial, is_final = state_spec[:4]
                policy = state_spec[4] if len(state_spec) > 4 else {}
                state, created = State.objects.get_or_create(
                    workflow_definition=definition,
                    code=state_code,
                    defaults={
                        "name": state_name,
                        "is_initial": is_initial,
                        "is_final": is_final,
                        "assignment_policy": policy,
                    },
                )
                if not created and (
                    state.name != state_name
                    or state.is_initial != is_initial
                    or state.is_final != is_final
                ):
                    state.name = state_name
                    state.is_initial = is_initial
                    state.is_final = is_final
                    state.save(update_fields=["name", "is_initial", "is_final", "updated_at"])
                states[state_code] = state

            for t_name, from_code, to_code, roles, kind in blueprint["transitions"]:
                transition, created = Transition.objects.get_or_create(
                    workflow_definition=definition,
                    from_state=states[from_code],
                    name=t_name,
                    defaults={
                        "to_state": states[to_code],
                        "allowed_role_codes": roles,
                        "kind": kind,
                    },
                )
                if created:
                    self.stdout.write(f"[created] transition {code}:{t_name}")
                elif force:
                    transition.to_state = states[to_code]
                    transition.allowed_role_codes = roles
                    transition.kind = kind
                    transition.save(update_fields=[
                        "to_state", "allowed_role_codes", "kind", "updated_at",
                    ])
                    self.stdout.write(f"[forced] transition {code}:{t_name}")
        self.stdout.write(self.style.SUCCESS("staff reference data ready"))
