"""
Transition Validator — لایه اعتبارسنجی خالص و تست‌پذیر

مسئولیت:
  بررسی ۵ شرط برای اجرای یک Transition:
    1) Instance در وضعیت RUNNING باشد
    2) Transition متعلق به همان WorkflowDefinition باشد
    3) Transition از State فعلی Instance باشد
    4) Actor حداقل یکی از نقش‌های مجاز را داشته باشد
    5) Guard condition (در صورت وجود) پاس شود

ویژگی:
  - Pure: هیچ side-effect و DB write ندارد
  - Testable: با Mock شیء می‌توان بدون دیتابیس تست کرد
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from django.conf import settings

if TYPE_CHECKING:
    from apps.workflow.models import Instance, Transition


@dataclass
class TransitionValidationResult:
    """نتیجه اعتبارسنجی — شامل isValid و لیست خطاها"""

    is_valid: bool
    errors: list[str] = field(default_factory=list)


class TransitionValidator:
    """
    Pure validation — no side-effects, no DB writes.
    Makes execute_transition() testable without mocking DB.
    """

    def validate(
        self,
        instance: "Instance",
        transition: "Transition",
        actor: settings.AUTH_USER_MODEL,  # type: ignore[valid-type]
    ) -> TransitionValidationResult:
        errors: list[str] = []

        # --- 1. Instance در حال اجراست؟ ---
        # نکته: مقدار "running" به‌صورت literal نگه داشته شده چون Instance
        # فقط در TYPE_CHECKING ایمپورت شده و ارجاع به Instance.Status.RUNNING
        # در runtime باعث NameError می‌شود.
        if str(instance.status) != "running":
            errors.append(
                f"Instance در وضعیت '{instance.status}' است، "
                f"وضعیت باید 'running' باشد."
            )

        # --- 2. Transition متعلق به همین Workflow است؟ ---
        if transition.workflow_definition_id != instance.workflow_definition_id:
            errors.append(
                "Transition متعلق به Workflow این Instance نیست."
            )

        # --- 3. Transition از State فعلی Instance است؟ ---
        if transition.from_state_id != instance.current_state_id:
            current_code = (
                instance.current_state.code if instance.current_state else "?"
            )
            errors.append(
                f"Transition '{transition.name}' از وضعیت جاری "
                f"'{current_code}' نیست."
            )

        # --- 4. Actor حداقل یک نقش مجاز دارد؟ ---
        if transition.allowed_role_codes:
            actor_roles = actor.role_codes()
            if not any(role in actor_roles for role in transition.allowed_role_codes):
                errors.append(
                    f"شما نقش مجاز برای این انتقال را ندارید. "
                    f"نقش‌های مورد نیاز: {transition.allowed_role_codes}."
                )

        # --- 5. Guard condition ---
        if transition.guard_expression and transition.guard_expression != {}:
            from apps.workflow.guards import GuardEvaluator

            guard_ok, guard_msg = GuardEvaluator().evaluate(
                guard=transition.guard_expression,
                instance=instance,
                actor=actor,
            )
            if not guard_ok:
                errors.append(guard_msg or "شرط تکمیلی (Guard) این انتقال را رد کرد.")

        return TransitionValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
        )