"""
Workflow Engine Service — هسته موتور گردش کار

مسئولیت:
  - create_instance: ایجاد نمونه جدید از یک فرآیند
  - get_available_transitions: انتقال‌های مجاز برای کاربر در یک Instance
  - execute_transition: اجرای یک انتقال با قفل تراکنشی
  - عملیات معنایی سطح‌بالا: approve / reject / return_to_previous /
    complete / send_copy / delegate / assign (همه از execute_transition و
    اعتبارسنج‌های همان می‌گذرند — هیچ میان‌بری امنیتی وجود ندارد)
  - cancel_instance: لغو یک Instance
  - link_entity / get_linked_entity: اتصال Instance به موجودیت دامنه

Side-effects مجاز در تراکنش انتقال: ActionLog، ApprovalRecord،
NotificationOutbox (صف اعلان — ارسال واقعی بیرون از تراکنش).

Thread-safety:
  تمام متدهایی که دیتا می‌نویسند داخل @transaction.atomic
  و با select_for_update روی ردیف‌های مربوطه قفل می‌گیرند.
"""
from __future__ import annotations

import logging
import uuid
from datetime import timedelta
from typing import Iterable, Optional

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, models, transaction
from django.utils import timezone

from apps.workflow.models import (
    ActionLog,
    ApprovalRecord,
    Instance,
    InstanceCopy,
    NotificationOutbox,
    RequestSequence,
    State,
    Transition,
    WorkflowDefinition,
)
from apps.workflow.validators import TransitionValidator

logger = logging.getLogger(__name__)

ELEVATED_WORKFLOW_ROLES = {"manager", "workflow_admin", "hr"}

#: name-fallback matchers for the semantic ops (kind is the canonical flag).
_ACTION_NAME_ALIASES: dict[str, set[str]] = {
    "approve": {"approve", "approved", "accept", "confirm"},
    "reject": {"reject", "rejected", "deny", "denied"},
    "return": {"return", "back", "send_back", "return_to_previous"},
    "complete": {"complete", "done", "finish", "end"},
}


def _next_tracking_number() -> str:
    """
    Reserve the next human Tracking ID: ``REQ-<gregorian-year>-000123``.

    The counter is GLOBAL per year, not per workflow code. The number itself
    only encodes a year, so a per-code counter hands ``REQ-2026-000001`` to
    the first instance of EVERY process — and Instance.tracking_number is
    live-unique (migration 0008 proved it on real data with a UniqueViolation
    while creating the index). One counter per year makes uniqueness
    structural; the workflow type is a JOIN away whenever it matters.

    PostgreSQL: the year row is locked with select_for_update. SQLite
    (tests): row locking is a no-op, so the caller's transaction + the
    live-unique constraint are the source of truth — a collision raises
    IntegrityError and the engine never silently reuses a tracking number.

    Year is Gregorian on purpose: the same convention as
    forms.next_submission_number, so an instance and its linked submission
    created in the same moment share a year prefix.
    """
    year = timezone.now().year
    try:
        with transaction.atomic():
            sequence, _created = RequestSequence.objects.get_or_create(
                year=year, defaults={"last_value": 0},
            )
    except IntegrityError:
        # Concurrent creation of the year row — take the winner.
        sequence = RequestSequence.objects.get(year=year)
    sequence = RequestSequence.objects.select_for_update().get(pk=sequence.pk)
    sequence.last_value = (sequence.last_value or 0) + 1
    sequence.save(update_fields=["last_value", "updated_at"])
    return f"REQ-{year}-{sequence.last_value:06d}"


class WorkflowEngineError(Exception):

    """Base exception for all workflow engine errors."""


class InvalidTransitionError(WorkflowEngineError):
    """Transition not allowed — role, state, or guard failure."""


class WorkflowNotActiveError(WorkflowEngineError):
    """Workflow definition is not active."""


class InstanceNotRunningError(WorkflowEngineError):
    """Instance is not in running state."""


class WorkflowEngineService:
    """
    Core service for executing workflow transitions.
    Thread-safe: uses select_for_update inside transactions.
    """

    # ------------------------------------------------------------------
    # Create Instance
    # ------------------------------------------------------------------

    @transaction.atomic
    def create_instance(
        self,
        workflow_code: str,
        requester: settings.AUTH_USER_MODEL,  # type: ignore[valid-type]
        title: str,
        description: str = "",
        subject_person=None,
    ) -> Instance:
        """
        ایجاد یک نمونه جدید از فرآیند.

        مراحل:
          1. قفل و بارگذاری WorkflowDefinition
          2. یافتن State اولیه (is_initial)
          3. ساخت Instance (با subject_person برای اعلان‌ها)
          4. ثبت ActionLog اولین اقدام
          5. ساخت WorkflowTask برای کاربران مجاز State اولیه

        Args:
            workflow_code: کد WorkflowDefinition (مثلاً leave-request)
            requester: کاربر درخواست‌دهنده
            title: عنوان درخواست
            description: توضیحات (اختیاری)
            subject_person: شخص هدف (Person) — گیرنده‌ی اصلی اعلان‌ها.
                از داده‌ی فرم استخراج می‌شود (یکپارچه‌سازی فرم و گردش‌کار).

        Returns:
            Instance ایجادشده
        """
        # 1. قفل WorkflowDefinition
        wf = (
            WorkflowDefinition.objects.select_for_update()
            .filter(code=workflow_code.strip().lower(), is_active=True)
            .first()
        )
        if not wf:
            if WorkflowDefinition.objects.filter(
                code=workflow_code.strip().lower(), is_deleted=False,
            ).exists():
                raise WorkflowNotActiveError(f"فرآیند '{workflow_code}' فعال نیست.")
            raise WorkflowEngineError(f"فرآیند '{workflow_code}' یافت نشد.")

        # 2. یافتن State اولیه
        initial_state = (
            State.objects.select_for_update()
            .filter(workflow_definition=wf, is_initial=True)
            .first()
        )
        if not initial_state:
            raise WorkflowEngineError(
                f"فرآیند '{workflow_code}' State اولیه (is_initial) ندارد."
            )

        # 3. ساخت Instance — allocate the human Tracking ID inside the same
        #    atomic block as the row, so a rolled-back create also rolls back
        #    the sequence bump (no gap, no reuse).
        instance = Instance.objects.create(
            workflow_definition=wf,
            current_state=initial_state,
            requester=requester,
            title=title,
            description=description,
            status=Instance.Status.RUNNING,
            tracking_number=_next_tracking_number(),
            subject_person=subject_person,
        )

        # 4. ثبت ActionLog
        ActionLog.objects.create(
            instance=instance,
            from_state=None,
            to_state=initial_state,
            action="create",
            actor=requester,
            comment="ایجاد درخواست",
        )

        # 5. ساخت تسک‌های اولیه
        self._create_tasks_for_state(instance, initial_state, assigned_by=requester)

        logger.info(
            "Instance %s created for workflow '%s' by user %s",
            instance.id, workflow_code, requester,
        )
        return instance

    # ------------------------------------------------------------------
    # Get Available Transitions
    # ------------------------------------------------------------------

    def get_available_transitions(
        self,
        instance: Instance,
        actor: settings.AUTH_USER_MODEL,  # type: ignore[valid-type]
    ) -> list[Transition]:
        """
        بازگرداندن Transition‌های مجاز برای یک کاربر در یک Instance.

        فیلترها:
          - Instance باید RUNNING باشد
          - Transition باید از State فعلی Instance باشد
          - کاربر باید نقش مجاز داشته باشد
          - Guard condition (در صورت وجود) باید پاس شود

        Args:
            instance: Instance مورد نظر
            actor: کاربر درخواست‌کننده

        Returns:
            لیست Transitionهای مجاز (می‌تواند خالی باشد)
        """
        if instance.status != Instance.Status.RUNNING:
            return []

        if not instance.current_state_id:
            return []

        # دریافت همه Transitionهای ممکن از State فعلی
        transitions = list(
            Transition.objects.filter(
                workflow_definition=instance.workflow_definition,
                from_state=instance.current_state,
            ).select_related("to_state")
        )

        # اعتبارسنجی هر Transition با TransitionValidator
        validator = TransitionValidator()
        allowed: list[Transition] = []
        for t in transitions:
            result = validator.validate(instance, t, actor)
            if result.is_valid and self._actor_can_act_on_state(instance, actor):
                allowed.append(t)

        return allowed

    # ------------------------------------------------------------------
    # Execute Transition
    # ------------------------------------------------------------------

    @transaction.atomic
    def execute_transition(
        self,
        instance_id: uuid.UUID,
        transition_id: uuid.UUID,
        actor: settings.AUTH_USER_MODEL,  # type: ignore[valid-type]
        comment: str = "",
        metadata: Optional[dict] = None,
        idempotency_key: Optional[str] = None,
    ) -> Instance:
        """
        اجرای یک Transition روی یک Instance.
        این متد کل عملیات را در یک تراکنش اتمی انجام می‌دهد.

        مراحل:
          0. Replay-check روی idempotency_key (§13-3)
          1. قفل Instance
          2. بارگذاری Transition
          3. اعتبارسنجی با TransitionValidator
          4. به‌روزرسانی State Instance
          5. ثبت ActionLog (با کلید)
          6. بستن تسک‌های قدیمی
          7. ساخت تسک‌های جدید (اگر State نهایی نباشد)
          8. صف اعلان‌ها

        Args:
            instance_id: PK Instance
            transition_id: PK Transition
            actor: کاربر اجراکننده
            comment: کامنت (اختیاری)
            metadata: دیتای اضافی (اختیاری)
            idempotency_key: کلید یکتای کلاینت (اختیاری) — اجرای دوباره با
                همان کلید، وضعیت فعلی را بازمی‌گرداند نه خطا.

        Returns:
            Instance به‌روزرسانی‌شده
        """
        # 0. Replay-safety: a recorded key means a retry of a COMMITTED
        # action — return the current state instead of an error. A key bound
        # to a DIFFERENT instance is a client bug → hard reject (the DB
        # unique constraint remains the arbiter for concurrent races).
        if idempotency_key:
            existing = ActionLog.objects.filter(
                idempotency_key=idempotency_key
            ).select_related("instance").first()
            if existing is not None:
                if existing.instance_id != instance_id:
                    raise WorkflowEngineError(
                        "این کلید اقدام قبلاً برای درخواست دیگری استفاده شده است."
                    )
                logger.info(
                    "Replayed action for key %s -> instance %s",
                    idempotency_key, existing.instance_id,
                )
                return existing.instance

        # 1. قفل Instance
        instance = (
            Instance.objects.select_for_update()
            .filter(pk=instance_id)
            .first()
        )
        if not instance:
            raise WorkflowEngineError(f"Instance {instance_id} یافت نشد.")

        # 1b. Re-check the key AFTER acquiring the instance lock: a concurrent
        # identical request may have committed while we were waiting. Without
        # this, the loser of the race would surface a confusing
        # InvalidTransitionError instead of a clean replay.
        if idempotency_key:
            existing = ActionLog.objects.filter(
                idempotency_key=idempotency_key
            ).first()
            if existing is not None:
                if existing.instance_id != instance_id:
                    raise WorkflowEngineError(
                        "این کلید اقدام قبلاً برای درخواست دیگری استفاده شده است."
                    )
                logger.info(
                    "Replayed action for key %s (post-lock) -> instance %s",
                    idempotency_key, existing.instance_id,
                )
                return Instance.objects.get(pk=existing.instance_id)

        # 2. بارگذاری Transition
        try:
            transition = Transition.objects.select_for_update().get(pk=transition_id)
        except Transition.DoesNotExist:
            raise WorkflowEngineError(f"Transition {transition_id} یافت نشد.")

        if not self._actor_can_act_on_state(instance, actor):
            raise InvalidTransitionError("این درخواست در کارتابل شما قرار ندارد.")

        # 3. اعتبارسنجی با TransitionValidator (pure) + الزام کامنت (B6)
        validator = TransitionValidator()
        result = validator.validate(instance, transition, actor)
        if not result.is_valid:
            raise InvalidTransitionError("; ".join(result.errors))
        if transition.requires_comment and not (comment or "").strip():
            raise InvalidTransitionError(
                "برای این اقدام، وارد کردن توضیح الزامی است."
            )

        # 4. به‌روزرسانی State
        old_state = instance.current_state
        new_state = transition.to_state
        instance.current_state = new_state

        # تعیین وضعیت نهایی — kind معنایی انتقال مرجع است، با fallback به نام
        semantic = (transition.kind or "").strip().lower()
        action_l = transition.name.strip().lower()
        if new_state.is_final:
            if semantic == "reject" or action_l in ("reject", "rejected", "cancel", "cancelled"):
                instance.status = Instance.Status.REJECTED
            else:
                instance.status = Instance.Status.COMPLETED

        instance.save(update_fields=["current_state", "status", "updated_at"])

        # 5. ثبت ActionLog
        try:
            with transaction.atomic():
                action_log = ActionLog.objects.create(
                    instance=instance,
                    from_state=old_state,
                    to_state=new_state,
                    action=transition.name,
                    actor=actor,
                    comment=comment,
                    metadata=metadata or {},
                    idempotency_key=idempotency_key or None,
                )
        except IntegrityError as exc:
            # The client key was already used by a committed action (possibly
            # on another instance — a client bug). Abort the WHOLE transition:
            # the outer @transaction.atomic rolls back the state change too,
            # so a key can never apply two different transitions.
            if idempotency_key:
                raise WorkflowEngineError(
                    "این کلید اقدام قبلاً استفاده شده است (تلاش مجدد)."
                ) from exc
            raise

        # 5b. رکورد تایید مستقل از status (§14.5 / B6): هر انتقالِ تایید یا
        # رد، یک ApprovalRecord امضاشده تولید می‌کند (نقش، زمان، وضعیت).
        if semantic in ("approve", "reject") or action_l in ("approve", "reject"):
            roles = set()
            if hasattr(actor, "role_codes"):
                roles = actor.role_codes()
            ApprovalRecord.objects.create(
                instance=instance,
                transition=transition,
                approver=actor,
                role_code=(
                    "workflow_admin"
                    if "workflow_admin" in roles
                    else ", ".join(sorted(roles & set(transition.allowed_role_codes)))
                ) if transition.allowed_role_codes else ", ".join(sorted(roles)),
                action="approve" if (
                    semantic == "approve" or action_l in ("approve", "accept", "confirmed")
                ) else "reject",
                comment=comment,
                state=old_state,
            )

        # 6. بستن تسک‌های PENDING وضعیت قبلی
        from apps.tasks.models import WorkflowTask

        WorkflowTask.objects.filter(
            instance=instance,
            state=old_state,
            status=WorkflowTask.Status.PENDING,
        ).update(
            status=WorkflowTask.Status.COMPLETED,
            completed_at=timezone.now(),
            updated_at=timezone.now(),
        )

        # 7. ساخت تسک برای وضعیت جدید (اگر نهایی نباشد) — با due_date از
        # State.default_due_hours (B6: قبلاً due_date هرگز ست نمی‌شد).
        if not new_state.is_final:
            self._create_tasks_for_state(instance, new_state, assigned_by=actor)

        # 8. صف اعلان‌ها (outbox) — بعد از ساخت تسک‌ها، چون گیرندگانِ
        # task_created از دارندگان تسک وضعیت جدید خوانده می‌شوند. هیچ ارسال
        # بیرونی اینجا انجام نمی‌شود.
        self._enqueue_notifications(
            instance, transition, actor, comment, event_id=action_log.pk,
        )

        logger.info(
            "Instance %s: transition '%s' by user %s -> %s",
            instance_id, transition.name, actor, instance.status,
        )
        return instance

    # ------------------------------------------------------------------
    # Cancel Instance
    # ------------------------------------------------------------------

    @transaction.atomic
    def cancel_instance(
        self,
        instance_id: uuid.UUID,
        actor: settings.AUTH_USER_MODEL,  # type: ignore[valid-type]
        reason: str = "",
    ) -> Instance:
        """
        لغو یک Instance در حال اجرا.

        فقط درخواست‌دهنده یا کاربر با نقش workflow_admin مجاز به لغو هستند.

        Args:
            instance_id: PK Instance
            actor: کاربر درخواست‌دهنده
            reason: دلیل لغو (اختیاری)

        Returns:
            Instance به‌روزرسانی‌شده
        """
        instance = (
            Instance.objects.select_for_update()
            .filter(pk=instance_id)
            .first()
        )
        if not instance:
            raise WorkflowEngineError(f"Instance {instance_id} یافت نشد.")
        if instance.status != Instance.Status.RUNNING:
            raise InstanceNotRunningError(
                f"Instance {instance_id} در وضعیت '{instance.status}' است، "
                f"فقط Instanceهای RUNNING قابل لغو هستند."
            )

        # بررسی دسترسی
        actor_roles = actor.role_codes()
        is_requester = instance.requester_id == actor.pk
        is_admin = "workflow_admin" in actor_roles

        if not (is_requester or is_admin):
            raise InvalidTransitionError(
                "فقط درخواست‌دهنده یا کاربر با نقش workflow_admin "
                "می‌تواند یک Instance را لغو کند."
            )

        instance.status = Instance.Status.CANCELLED
        instance.save(update_fields=["status", "updated_at"])

        # ثبت ActionLog
        ActionLog.objects.create(
            instance=instance,
            from_state=instance.current_state,
            to_state=None,
            action="cancel",
            actor=actor,
            comment=reason or "لغو توسط کاربر",
        )

        # بستن تسک‌های PENDING
        from apps.tasks.models import WorkflowTask

        WorkflowTask.objects.filter(
            instance=instance,
            status=WorkflowTask.Status.PENDING,
        ).update(
            status=WorkflowTask.Status.SKIPPED,
            updated_at=timezone.now(),
        )

        return instance

    # ------------------------------------------------------------------
    # Entity Linking
    # ------------------------------------------------------------------

    @transaction.atomic
    def link_entity(
        self,
        instance_id: uuid.UUID,
        entity: object,
    ) -> object:
        """
        اتصال یک موجودیت دامنه (CourseOffering, Lead, ...) به Instance
        از طریق EntityWorkflow.

        هر موجودیت فقط به یک Instance می‌تواند متصل شود
        (اجرا توسط UniqueConstraint).

        Args:
            instance_id: PK Instance
            entity: شیء موجودیت دامنه

        Returns:
            شیء EntityWorkflow ایجاد/به‌روزرسانی‌شده
        """
        from apps.workflow.models import EntityWorkflow

        instance = (
            Instance.objects.select_for_update()
            .filter(pk=instance_id)
            .first()
        )
        if not instance:
            raise WorkflowEngineError(f"Instance {instance_id} یافت نشد.")

        ct = ContentType.objects.get_for_model(entity)
        link, created = EntityWorkflow.objects.update_or_create(
            content_type=ct,
            object_id=str(entity.pk),
            defaults={"instance": instance},
        )

        logger.info(
            "%s %s به Instance %s",
            "متصل شد" if created else "اتصال به‌روزرسانی شد",
            f"{ct.model}({entity.pk})",
            instance_id,
        )
        return link

    def get_linked_entity(
        self,
        instance: Instance,
        model_class=None,
    ):
        """
        دریافت موجودیت دامنه متصل به یک Instance.

        Args:
            instance: Instance
            model_class: (اختیاری) کلاس موجودیت برای فیلتر کردن

        Returns:
            اولین موجودیت متصل، یا None
        """
        from apps.workflow.models import EntityWorkflow

        qs = instance.entity_links.select_related("content_type")
        if model_class:
            ct = ContentType.objects.get_for_model(model_class)
            qs = qs.filter(content_type=ct)
        for link in qs:
            entity = link.entity
            if entity is not None:
                return entity
        return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _actor_can_act_on_state(instance: Instance, actor) -> bool:
        """Enforce user assignment only for states with an explicit policy.

        Legacy workflow definitions have an empty policy and retain their old
        role-based behavior.  New definitions opt into queue/individual task
        semantics by setting ``State.assignment_policy``; a workflow admin is
        always allowed to recover an unassigned or stuck request.
        """
        policy = getattr(instance.current_state, "assignment_policy", None) or {}
        if not policy:
            return True
        if getattr(actor, "has_role", lambda _code: False)("workflow_admin"):
            return True
        from apps.tasks.models import WorkflowTask

        return WorkflowTask.objects.filter(
            instance=instance,
            state=instance.current_state,
            assignee=actor,
            status=WorkflowTask.Status.PENDING,
            is_deleted=False,
        ).exists()

    @staticmethod
    def _eligible_user_ids(role_codes: set[str]) -> list:
        from apps.accounts.models import UserRole

        if not role_codes:
            return []
        now = timezone.now()
        return list(
            UserRole.objects.filter(
                role__code__in=role_codes,
                is_active=True,
                role__is_active=True,
                role__is_deleted=False,
                user__is_active=True,
                user__is_deleted=False,
            )
            .filter(models.Q(valid_from__isnull=True) | models.Q(valid_from__lte=now))
            .filter(models.Q(valid_to__isnull=True) | models.Q(valid_to__gte=now))
            .values_list("user_id", flat=True)
            .distinct()
        )

    def _resolve_policy_assignees(self, instance: Instance, state: State, outgoing) -> list:
        """Resolve one or more users from a state assignment policy."""
        from apps.accounts.models import User
        from apps.tasks.models import WorkflowTask

        policy = state.assignment_policy or {}
        strategy = str(policy.get("strategy") or "role").strip().lower()
        fallback_roles = {str(code).strip().lower() for code in (policy.get("fallback_roles") or [])}
        outgoing_roles = {
            code
            for transition in outgoing
            for code in (transition.allowed_role_codes or [])
        }

        user_ids: list = []
        if strategy in {"requester", "self"}:
            user_ids = [instance.requester_id]
        elif strategy in {"subject_user", "subject"}:
            subject_user_id = getattr(instance.subject_person, "user_id", None)
            user_ids = [subject_user_id] if subject_user_id else []
        elif strategy in {"direct_manager", "supervisor"}:
            manager_id = getattr(instance.requester, "manager_id", None)
            user_ids = [manager_id] if manager_id else []
        elif strategy in {"explicit_user", "user"}:
            explicit_id = policy.get("user_id")
            user_ids = [explicit_id] if explicit_id else []
        else:
            configured_roles = {
                str(code).strip().lower()
                for code in (policy.get("roles") or outgoing_roles)
            }
            user_ids = self._eligible_user_ids(configured_roles)

        if not user_ids and fallback_roles:
            user_ids = self._eligible_user_ids(fallback_roles)
        if not user_ids and strategy not in {"requester", "self", "subject_user", "subject", "explicit_user", "user"}:
            user_ids = self._eligible_user_ids(outgoing_roles)

        # Discard malformed/non-existent ids and inactive users before choosing.
        user_ids = list(
            User.objects.filter(
                pk__in=[uid for uid in user_ids if uid],
                is_active=True,
                is_deleted=False,
            ).values_list("pk", flat=True)
        )
        if not user_ids:
            return []
        if str(policy.get("multiple") or "one").lower() == "all":
            return user_ids

        # A deterministic lightest-load choice prevents fan-out while keeping
        # assignment fair when several supervisors/managers are eligible.
        load = {
            uid: WorkflowTask.objects.filter(
                assignee_id=uid,
                status=WorkflowTask.Status.PENDING,
                is_deleted=False,
            ).count()
            for uid in user_ids
        }
        return [min(user_ids, key=lambda uid: (load[uid], str(uid)))]

    def _create_tasks_for_state(
        self,
        instance: Instance,
        state: State,
        assigned_by: Optional[settings.AUTH_USER_MODEL] = None,  # type: ignore[valid-type]
    ) -> None:
        """
        ساخت WorkflowTask برای همه کاربرانی که نقش مجاز برای
        Transitionهای خروجی از این State را دارند.

        Args:
            instance: Instance
            state: State فعلی
            assigned_by: کاربری که تسک را ارجاع می‌دهد (اختیاری)
        """
        from apps.tasks.models import WorkflowTask

        # یافتن همه Transitionهای خروجی از این State
        outgoing = Transition.objects.filter(
            workflow_definition=instance.workflow_definition,
            from_state=state,
        )

        # جمع‌آوری نقش‌های مجاز یکتا
        role_codes: set[str] = set()
        for t in outgoing:
            if t.allowed_role_codes:
                role_codes.update(t.allowed_role_codes)

        policy = state.assignment_policy or {}
        if not role_codes and not policy:
            logger.warning(
                "هیچ نقش مجازی برای Transitionهای State '%s' تعریف نشده؛ "
                "تسکی ساخته نشد.",
                state.code,
            )
            return

        if policy:
            user_ids = self._resolve_policy_assignees(instance, state, outgoing)
        else:
            # Legacy definitions retain the previous fan-out behavior. New
            # definitions should always declare a policy and therefore use a
            # queue/individual assignment instead.
            role_codes.add("workflow_admin")
            user_ids = self._eligible_user_ids(role_codes)

        tasks: list[WorkflowTask] = []
        # due_date is derived from the State's default_due_hours (B6 — was
        # never set before). None when the state declares no SLA.
        due = (
            timezone.now() + timedelta(hours=state.default_due_hours)
            if getattr(state, "default_due_hours", None)
            else None
        )
        for uid in user_ids:
            tasks.append(
                WorkflowTask(
                    instance=instance,
                    state=state,
                    assignee_id=uid,
                    assigned_by=assigned_by,
                    status=WorkflowTask.Status.PENDING,
                    due_date=due,
                )
            )

        if tasks:
            WorkflowTask.objects.bulk_create(tasks, ignore_conflicts=True)
            logger.info(
                "%d تسک برای Instance %s در State '%s' ساخته شد.",
                len(tasks), instance.id, state.code,
            )
        else:
            logger.warning(
                "هیچ کاربری برای نقش‌های %s در State '%s' یافت نشد.",
                role_codes, state.code,
            )

    # ------------------------------------------------------------------
    # Notification outbox (B6)
    # ------------------------------------------------------------------

    def _enqueue_notifications(
        self,
        instance: Instance,
        transition: Transition,
        actor,
        comment: str,
        *,
        event_id,
    ) -> None:
        """
        Enqueue IN_APP notifications for the new task holders and the original
        requester. This writes only outbox rows — the actual email/SMS delivery
        happens in a worker AFTER the commit, so a broken mailer can never roll
        back a successful transition (report §6/§13).
        """
        from apps.tasks.models import WorkflowTask

        recipients: set = set()
        new_task_users = WorkflowTask.objects.filter(
            instance=instance,
            state=instance.current_state,
            status=WorkflowTask.Status.PENDING,
        ).values_list("assignee_id", flat=True)
        recipients.update(new_task_users)
        if instance.requester_id:
            recipients.add(instance.requester_id)
        # گیرنده‌ی اصلی اعلان‌ها: شخص هدف (subject_person).
        # از داده‌ی فرم استخراج می‌شود — یکپارچه‌سازی فرم و گردش‌کار.
        # actor (فردی که اقدام کرده) اعلان نمی‌گیرد، حتی اگر subject باشد.
        subject = instance.subject_person
        if subject is not None and subject.user_id:
            recipients.add(subject.user_id)
        recipients.discard(getattr(actor, "pk", None))

        template = "task_created"
        if (transition.kind or "").strip().lower() in ("approve", "reject"):
            template = "approved" if (transition.kind or "").lower() == "approve" else "rejected"

        outbox = [
            NotificationOutbox(
                instance=instance,
                recipient_id=uid,
                channel=NotificationOutbox.Channel.IN_APP,
                template=template,
                payload={
                    "title": instance.title,
                    "actor": getattr(actor, "username", str(actor)),
                    "transition": transition.name,
                    "comment": comment,
                },
                delivery_key=f"workflow-transition:{event_id}:{uid}",
            )
            for uid in recipients
        ]
        if outbox:
            NotificationOutbox.objects.bulk_create(outbox)

    # ------------------------------------------------------------------
    # Semantic operations (report §14.4 / B6)
    # ------------------------------------------------------------------
    #
    # These are thin, named entry points over execute_transition(). They never
    # bypass validation: each resolves the single matching AVAILABLE transition
    # for the actor (role + guard + state still enforced by the engine), then
    # delegates. If the actor lacks permission for that action, no matching
    # transition exists and InvalidTransitionError is raised.

    def _find_transition_by_kind(
        self, instance_id, actor, kind: str
    ) -> Transition:
        instance = Instance.objects.filter(pk=instance_id).first()
        if instance is None:
            raise WorkflowEngineError(f"Instance {instance_id} یافت نشد.")
        candidates = self.get_available_transitions(instance, actor)
        wanted_names = _ACTION_NAME_ALIASES.get(kind, set())
        for t in candidates:
            if (t.kind or "").strip().lower() == kind or t.name.strip().lower() in wanted_names:
                return t
        raise InvalidTransitionError(
            f"هیچ انتقال مجاز «{kind}» برای شما در وضعیت فعلی وجود ندارد."
        )

    def approve(self, instance_id, actor, comment="", metadata=None, idempotency_key=None) -> Instance:
        t = self._find_transition_by_kind(instance_id, actor, "approve")
        return self.execute_transition(instance_id, t.pk, actor, comment, metadata, idempotency_key)

    def reject(self, instance_id, actor, comment="", metadata=None, idempotency_key=None) -> Instance:
        t = self._find_transition_by_kind(instance_id, actor, "reject")
        return self.execute_transition(instance_id, t.pk, actor, comment, metadata, idempotency_key)

    def return_to_previous(self, instance_id, actor, comment="", metadata=None, idempotency_key=None) -> Instance:
        t = self._find_transition_by_kind(instance_id, actor, "return")
        return self.execute_transition(instance_id, t.pk, actor, comment, metadata, idempotency_key)

    def complete(self, instance_id, actor, comment="", metadata=None, idempotency_key=None) -> Instance:
        t = self._find_transition_by_kind(instance_id, actor, "complete")
        return self.execute_transition(instance_id, t.pk, actor, comment, metadata, idempotency_key)

    def save_draft(self, *args, **kwargs):  # pragma: no cover - forms owns drafts
        raise NotImplementedError(
            "Drafts are owned by the forms engine (FormSubmissionService); "
            "the workflow engine starts on submit."
        )

    @transaction.atomic
    def send_copy(
        self,
        instance_id,
        sender,
        recipient_ids: Iterable,
        note: str = "",
    ) -> int:
        """
        رونوشت (send_copy): notify recipients for awareness WITHOUT assigning
        work. Returns the number of new copy rows created.
        """
        instance = Instance.objects.select_for_update().filter(pk=instance_id).first()
        if instance is None:
            raise WorkflowEngineError(f"Instance {instance_id} یافت نشد.")
        created = 0
        for rid in recipient_ids:
            _copy, was_created = InstanceCopy.objects.get_or_create(
                instance=instance, recipient_id=rid, sender=sender,
                defaults={"note": note},
            )
            if was_created:
                created += 1
                NotificationOutbox.objects.create(
                    instance=instance,
                    recipient_id=rid,
                    channel=NotificationOutbox.Channel.IN_APP,
                    template="copy_received",
                    payload={"title": instance.title, "sender": getattr(sender, "username", str(sender)), "note": note},
                    delivery_key=f"workflow-copy:{_copy.pk}:{rid}",
                )
        logger.info("Instance %s: %d copies by %s", instance_id, created, sender)
        return created

    @transaction.atomic
    def delegate(
        self,
        instance_id,
        delegator,
        recipient,
        comment: str = "",
    ) -> None:
        """
        تفویض/ارجاع (delegate): تسک‌های PENDINGِ واگذارکننده روی وضعیت فعلی
        به گیرنده منتقل می‌شود (گیرنده جایگزین می‌شود). یک ActionLog ثبت و
        به گیرنده اعلان صف می‌شود.
        """
        from apps.accounts.models import User
        from apps.tasks.models import WorkflowTask

        instance = Instance.objects.select_for_update().filter(pk=instance_id).first()
        if instance is None:
            raise WorkflowEngineError(f"Instance {instance_id} یافت نشد.")
        recipient_id = getattr(recipient, "pk", recipient)
        target = User.objects.filter(
            pk=recipient_id, is_active=True, is_deleted=False,
        ).first()
        if target is None or target.pk == getattr(delegator, "pk", None):
            raise InvalidTransitionError("گیرندهٔ ارجاع معتبر نیست.")

        state_roles = Transition.objects.filter(
            workflow_definition=instance.workflow_definition,
            from_state=instance.current_state,
        ).values_list("allowed_role_codes", flat=True)
        eligible_codes = {code for role_list in state_roles for code in (role_list or [])}
        eligible_codes.add("workflow_admin")
        if not (target.role_codes() & eligible_codes):
            raise InvalidTransitionError(
                "گیرنده باید در وضعیت فعلی یکی از نقش‌های مجاز را داشته باشد."
            )

        pending = WorkflowTask.objects.filter(
            instance=instance,
            state=instance.current_state,
            assignee=delegator,
            status=WorkflowTask.Status.PENDING,
        )
        if not pending.exists():
            raise InvalidTransitionError(
                "تسک فعالی برای واگذاری در وضعیت فعلی ندارید."
            )
        existing_recipient_task = WorkflowTask.objects.filter(
            instance=instance,
            state=instance.current_state,
            assignee_id=recipient_id,
            status=WorkflowTask.Status.PENDING,
            is_deleted=False,
        ).exists()
        if existing_recipient_task:
            # The recipient already holds the unique actionable task for this
            # state. Retire the delegator's duplicate assignment as coalesced.
            now = timezone.now()
            updated = pending.update(
                status=WorkflowTask.Status.SKIPPED,
                completed_at=now,
                updated_at=now,
            )
        else:
            updated = pending.update(assignee_id=recipient_id, updated_at=timezone.now())

        action_log = ActionLog.objects.create(
            instance=instance,
            from_state=instance.current_state,
            to_state=instance.current_state,
            action="delegate",
            actor=delegator,
            comment=comment or f"ارجاع به {target.username}",
            metadata={"tasks_moved": updated, "recipient": str(recipient_id)},
        )
        NotificationOutbox.objects.create(
            instance=instance,
            recipient_id=recipient_id,
            channel=NotificationOutbox.Channel.IN_APP,
            template="delegated_to_you",
            payload={"title": instance.title, "from": getattr(delegator, "username", str(delegator))},
            delivery_key=f"workflow-delegation:{action_log.pk}:{recipient_id}",
        )
        logger.info("Instance %s: %d tasks delegated to %s", instance_id, updated, recipient_id)
        return updated

    def assign(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError(
            "Assignment to a specific user is 'delegate'; auto-assignment "
            "happens on transition via _create_tasks_for_state."
        )
