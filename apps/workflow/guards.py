"""
Guard Evaluator — موتور ارزیابی شرط‌های پیشرفته برای Transitionها

این ماژول شرط‌های JSON ذخیره‌شده در Transition.guard_expression را ارزیابی می‌کند.
هر شرط از نوع خاصی است که توسط handler مربوطه پردازش می‌شود.

انواع شرط:
  - always_true: همیشه مجاز (پیش‌فرض)
  - role_not_in: اگر instance.<field> نقش مشخصی داشته باشد → رد
  - field_equals: instance.<field> == value
  - field_not_equals: instance.<field> != <source>
  - entity_field_lt: entity.<field> < entity.<other_field>
  - همه کاربری (all): همه زیرشرط‌ها باید پاس شوند (AND)
  - حداقل یکی (any): حداقل یک زیرشرط باید پاس شود (OR)

قوانین امنیتی:
  - نوع ناشناخته = رد (fail-closed)
  - خالی / {} = always_true
  - فیلد ناموجود = رد
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from django.conf import settings

if TYPE_CHECKING:
    from apps.workflow.models import Instance

logger = logging.getLogger(__name__)


class GuardDeniedError(Exception):
    """هنگام مسدود شدن Transition توسط Guard پرتاب می‌شود."""


class GuardEvaluator:
    """
    موتور ارزیابی شرط‌های پیشرفته.

    evaluate(guard, instance, actor) -> (allowed: bool, reason: str)
      allowed = True → Transition مجاز است
      allowed = False → Transition مسدود است، reason علت را توضیح می‌دهد
    """

    def evaluate(
        self,
        guard: dict[str, Any],
        instance: "Instance",
        actor: settings.AUTH_USER_MODEL,  # type: ignore[valid-type]
    ) -> tuple[bool, str]:
        guard_type = guard.get("type", "always_true")

        # یافتن handler متناسب با نوع شرط
        handler = getattr(self, f"_handle_{guard_type}", None)
        if handler is None:
            logger.warning("نوع شرط ناشناخته: %s — رد کردن", guard_type)
            return False, (
                f"نوع شرط '{guard_type}' ناشناخته است "
                f"(طبق سیاست، شرط ناشناخته = رد)."
            )

        try:
            return handler(guard, instance, actor)
        except Exception as e:
            logger.exception("خطا در ارزیابی شرط: %s", e)
            return False, f"خطا در ارزیابی شرط: {e}"

    # ------------------------------------------------------------------
    #  Handlers
    # ------------------------------------------------------------------

    def _handle_always_true(
        self,
        guard: dict[str, Any],
        instance: "Instance",
        actor: settings.AUTH_USER_MODEL,
    ) -> tuple[bool, str]:
        """همیشه مجاز — برای شرط‌های خالی / {}"""
        return True, ""

    def _handle_role_not_in(
        self,
        guard: dict[str, Any],
        instance: "Instance",
        actor: settings.AUTH_USER_MODEL,
    ) -> tuple[bool, str]:
        """
        رد Transition اگر instance.<field> (یک User) یکی از نقش‌های مشخص را داشته باشد.

        مثال:
          {"type": "role_not_in", "roles": ["manager"], "field": "requester"}
          یعنی: اگر instance.requester نقش manager دارد → رد کن

        کاربرد: مدیر نتواند درخواست خودش را تأیید کند.
        (با field_not_equals هم可实现 ولی این خواناتر است.)
        """
        roles: list[str] = guard.get("roles", [])
        field: str = guard.get("field", "")
        if not roles or not field:
            return False, "role_not_in: فیلد 'roles' یا 'field' وجود ندارد."

        target_user = self._resolve_field(instance, field)
        if target_user is None:
            return False, f"role_not_in: فیلد '{field}' یافت نشد یا User نیست."

        try:
            user_roles = target_user.role_codes()
        except AttributeError:
            return False, f"role_not_in: فیلد '{field}' متد role_codes() ندارد."

        for role in roles:
            if role in user_roles:
                return False, (
                    f"کاربر '{getattr(target_user, 'username', target_user)}' "
                    f"دارای نقش '{role}' است — این انتقال مسدود شد."
                )
        return True, ""

    def _handle_field_equals(
        self,
        guard: dict[str, Any],
        instance: "Instance",
        actor: settings.AUTH_USER_MODEL,
    ) -> tuple[bool, str]:
        """
        مقایسه instance.<field> == value.

        مثال:
          {"type": "field_equals", "field": "requester_id", "value": "some-uuid"}
        """
        field: str = guard.get("field", "")
        expected: Any = guard.get("value")
        if not field:
            return False, "field_equals: فیلد 'field' وجود ندارد."

        actual = self._resolve_field(instance, field)
        if actual is None and expected is not None:
            return False, f"field_equals: فیلد '{field}' یافت نشد."

        if str(actual) != str(expected):
            return False, (
                f"field_equals: مقدار مورد انتظار '{expected}' "
                f"با مقدار واقعی '{actual}' مطابقت ندارد."
            )
        return True, ""

    def _handle_field_not_equals(
        self,
        guard: dict[str, Any],
        instance: "Instance",
        actor: settings.AUTH_USER_MODEL,
    ) -> tuple[bool, str]:
        """
        مقایسه instance.<field> != <source>.

        source می‌تواند:
          - "actor.<attr>" → مثلاً "actor.id"
          - یک فیلد خود Instance → مثلاً "requester_id"

        مثال:
          {"type": "field_not_equals", "field": "requester_id", "source": "actor.id"}
          یعنی: اگر درخواست‌دهنده == اجراکننده → رد کن

        کاربرد: جلوگیری از self-approve (مدیر نتواند درخواست خودش را تأیید کند).
        """
        field: str = guard.get("field", "")
        source_path: str = guard.get("source", "")
        if not field or not source_path:
            return False, "field_not_equals: فیلد 'field' یا 'source' وجود ندارد."

        lhs = self._resolve_field(instance, field)
        rhs = self._resolve_source(source_path, instance, actor)

        if lhs is None and rhs is not None:
            return False, f"field_not_equals: فیلد '{field}' یافت نشد."
        if rhs is None:
            return False, f"field_not_equals: منبع '{source_path}' یافت نشد."

        if str(lhs) == str(rhs):
            return False, (
                f"field_not_equals: '{field}' == '{source_path}' "
                f"(هر دو '{lhs}') — این دو نباید برابر باشند."
            )
        return True, ""

    def _handle_entity_field_lt(
        self,
        guard: dict[str, Any],
        instance: "Instance",
        actor: settings.AUTH_USER_MODEL,
    ) -> tuple[bool, str]:
        """
        مقایسه دو فیلد روی موجودیت دامنه متصل (از طریق EntityWorkflow):
          entity.<field> < entity.<other_field>

        مثال:
          {"type": "entity_field_lt", "field": "enrolled_count", "other_field": "capacity"}
          یعنی: اگر تعداد ثبت‌نام‌ها >= ظرفیت → رد کن

        کاربرد: مسدود کردن تأیید برگزاری دوره وقتی ظرفیت پر است.
        نیاز به EntityWorkflow لینک شده دارد.
        """
        field: str = guard.get("field", "")
        other_field: str = guard.get("other_field", "")
        if not field or not other_field:
            return False, "entity_field_lt: فیلد 'field' یا 'other_field' وجود ندارد."

        entity = self._get_linked_entity(instance)
        if entity is None:
            return False, "entity_field_lt: هیچ موجودیت دامنه‌ای به این Instance متصل نیست."

        lhs = getattr(entity, field, None)
        rhs = getattr(entity, other_field, None)
        if lhs is None:
            return False, f"entity_field_lt: فیلد '{field}' روی موجودیت یافت نشد."
        if rhs is None:
            return False, f"entity_field_lt: فیلد '{other_field}' روی موجودیت یافت نشد."

        try:
            lhs_val, rhs_val = float(lhs), float(rhs)
        except (ValueError, TypeError):
            return False, f"entity_field_lt: مقادیر عددی نیستند ({lhs}, {rhs})."

        if not (lhs_val < rhs_val):
            name = getattr(entity, "display_name", getattr(entity, "name", str(entity)))
            return False, (
                f"entity_field_lt: '{field}' ({lhs_val}) کمتر از "
                f"'{other_field}' ({rhs_val}) نیست.\n"
                f"موجودیت: {name}"
            )
        return True, ""

    def _handle_all(
        self,
        guard: dict[str, Any],
        instance: "Instance",
        actor: settings.AUTH_USER_MODEL,
    ) -> tuple[bool, str]:
        """
        همه زیرشرط‌ها باید پاس شوند (AND منطقی).

        مثال:
          {"type": "all", "guards": [
            {"type": "field_not_equals", "field": "requester_id", "source": "actor.id"},
            {"type": "entity_field_lt", "field": "enrolled_count", "other_field": "capacity"},
          ]}
        """
        sub_guards: list[dict] = guard.get("guards", [])
        if not sub_guards:
            return True, ""
        for sub in sub_guards:
            ok, msg = self.evaluate(sub, instance, actor)
            if not ok:
                return False, f"[ALL] یک شرط پاس نشد: {msg}"
        return True, ""

    def _handle_any(
        self,
        guard: dict[str, Any],
        instance: "Instance",
        actor: settings.AUTH_USER_MODEL,
    ) -> tuple[bool, str]:
        """
        حداقل یکی از زیرشرط‌ها باید پاس شود (OR منطقی).

        مثال:
          {"type": "any", "guards": [
            {"type": "field_equals", "field": "role", "value": "admin"},
            {"type": "field_equals", "field": "role", "value": "supervisor"},
          ]}
        """
        sub_guards: list[dict] = guard.get("guards", [])
        if not sub_guards:
            return True, ""
        errors: list[str] = []
        for sub in sub_guards:
            ok, msg = self.evaluate(sub, instance, actor)
            if ok:
                return True, ""
            errors.append(msg)
        return False, f"[ANY] هیچ‌کدام از شرط‌ها پاس نشد: {'; '.join(errors)}"

    # ------------------------------------------------------------------
    #  Helpers
    # ------------------------------------------------------------------

    def _resolve_field(self, obj: Any, field_path: str) -> Any:
        """
        پیمایش یک مسیر نقطه‌گذاری شده روی یک شیء.
        مثال: obj.requester.id → 3 مرحله getattr
        """
        parts = field_path.split(".")
        current = obj
        for part in parts:
            try:
                current = getattr(current, part)
            except AttributeError:
                return None
            if callable(current):
                current = current()
        return current

    def _resolve_source(
        self,
        source_path: str,
        instance: "Instance",
        actor: settings.AUTH_USER_MODEL,
    ) -> Any:
        """
        حل منبع مقایسه.
        اگر با "actor." شروع شود → از actor خوانده می‌شود.
        در غیر این صورت → از instance خوانده می‌شود.
        """
        if source_path.startswith("actor."):
            attr = source_path[len("actor."):]
            return getattr(actor, attr, None)
        return self._resolve_field(instance, source_path)

    def _get_linked_entity(self, instance: "Instance") -> Any:
        """
        دریافت اولین موجودیت دامنه متصل به این Instance.
        از instance.entity_links استفاده می‌کند (قابل prefetch).
        """
        try:
            links = instance.entity_links.all()
        except AttributeError:
            return None
        for link in links:
            try:
                entity = link.entity
                if entity is not None:
                    return entity
            except Exception:
                continue
        return None