"""
Workflow Engine Service — هسته موتور گردش کار

مسئولیت:
  - create_instance: ایجاد نمونه جدید از یک فرآیند
  - get_available_transitions: انتقال‌های مجاز برای کاربر در یک Instance
  - execute_transition: اجرای یک انتقال با قفل تراکنشی
  - cancel_instance: لغو یک Instance
  - link_entity / get_linked_entity: اتصال Instance به موجودیت دامنه

Thread-safety:
  تمام متدهایی که دیتا می‌نویسند داخل @transaction.atomic
  و با select_for_update روی ردیف‌های مربوطه قفل می‌گیرند.
"""
from __future__ import annotations

import logging
import uuid
from typing import Optional

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.utils import timezone

from apps.workflow.models import ActionLog, Instance, State, Transition, WorkflowDefinition
from apps.workflow.validators import TransitionValidator

logger = logging.getLogger(__name__)


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
    ) -> Instance:
        """
        ایجاد یک نمونه جدید از فرآیند.

        مراحل:
          1. قفل و بارگذاری WorkflowDefinition
          2. یافتن State اولیه (is_initial)
          3. ساخت Instance
          4. ثبت ActionLog اولین اقدام
          5. ساخت WorkflowTask برای کاربران مجاز State اولیه

        Args:
            workflow_code: کد WorkflowDefinition (مثلاً leave-request)
            requester: کاربر درخواست‌دهنده
            title: عنوان درخواست
            description: توضیحات (اختیاری)

        Returns:
            Instance ایجادشده
        """
        # 1. قفل WorkflowDefinition
        wf = (
            WorkflowDefinition.objects.select_for_update()
            .filter(code=workflow_code.strip().lower())
            .first()
        )
        if not wf:
            raise WorkflowEngineError(f"فرآیند '{workflow_code}' یافت نشد.")
        if not wf.is_active:
            raise WorkflowNotActiveError(f"فرآیند '{workflow_code}' فعال نیست.")

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

        # 3. ساخت Instance
        instance = Instance.objects.create(
            workflow_definition=wf,
            current_state=initial_state,
            requester=requester,
            title=title,
            description=description,
            status=Instance.Status.RUNNING,
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
            if result.is_valid:
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
    ) -> Instance:
        """
        اجرای یک Transition روی یک Instance.
        این متد کل عملیات را در یک تراکنش اتمی انجام می‌دهد.

        مراحل:
          1. قفل Instance
          2. بارگذاری Transition
          3. اعتبارسنجی با TransitionValidator
          4. به‌روزرسانی State Instance
          5. ثبت ActionLog
          6. بستن تسک‌های قدیمی
          7. ساخت تسک‌های جدید (اگر State نهایی نباشد)

        Args:
            instance_id: PK Instance
            transition_id: PK Transition
            actor: کاربر اجراکننده
            comment: کامنت (اختیاری)
            metadata: دیتای اضافی (اختیاری)

        Returns:
            Instance به‌روزرسانی‌شده
        """
        # 1. قفل Instance
        instance = (
            Instance.objects.select_for_update()
            .filter(pk=instance_id)
            .first()
        )
        if not instance:
            raise WorkflowEngineError(f"Instance {instance_id} یافت نشد.")

        # 2. بارگذاری Transition
        try:
            transition = Transition.objects.select_for_update().get(pk=transition_id)
        except Transition.DoesNotExist:
            raise WorkflowEngineError(f"Transition {transition_id} یافت نشد.")

        # 3. اعتبارسنجی با TransitionValidator (pure)
        validator = TransitionValidator()
        result = validator.validate(instance, transition, actor)
        if not result.is_valid:
            raise InvalidTransitionError("; ".join(result.errors))

        # 4. به‌روزرسانی State
        old_state = instance.current_state
        new_state = transition.to_state
        instance.current_state = new_state

        # تعیین وضعیت نهایی
        if new_state.is_final:
            if transition.name.lower() in ("reject", "rejected", "cancel", "cancelled"):
                instance.status = Instance.Status.REJECTED
            else:
                instance.status = Instance.Status.COMPLETED

        instance.save(update_fields=["current_state", "status", "updated_at"])

        # 5. ثبت ActionLog
        ActionLog.objects.create(
            instance=instance,
            from_state=old_state,
            to_state=new_state,
            action=transition.name,
            actor=actor,
            comment=comment,
            metadata=metadata or {},
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

        # 7. ساخت تسک برای وضعیت جدید (اگر نهایی نباشد)
        if not new_state.is_final:
            self._create_tasks_for_state(instance, new_state, assigned_by=actor)

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
        from apps.accounts.models import UserRole
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

        if not role_codes:
            logger.warning(
                "هیچ نقش مجازی برای Transitionهای State '%s' تعریف نشده؛ "
                "تسکی ساخته نشد.",
                state.code,
            )
            return

        # یافتن کاربران دارای این نقش‌ها (با اعتبارسنجی تاریخ)
        now = timezone.now()
        user_ids = list(
            UserRole.objects.filter(
                role__code__in=role_codes,
                is_active=True,
                role__is_active=True,
                role__is_deleted=False,
                user__is_active=True,
                user__is_deleted=False,
            )
            .filter(
                models.Q(valid_from__isnull=True) | models.Q(valid_from__lte=now)
            )
            .filter(models.Q(valid_to__isnull=True) | models.Q(valid_to__gte=now))
            .values_list("user_id", flat=True)
            .distinct()
        )

        tasks: list[WorkflowTask] = []
        for uid in user_ids:
            tasks.append(
                WorkflowTask(
                    instance=instance,
                    state=state,
                    assignee_id=uid,
                    assigned_by=assigned_by,
                    status=WorkflowTask.Status.PENDING,
                )
            )

        if tasks:
            WorkflowTask.objects.bulk_create(tasks)
            logger.info(
                "%d تسک برای Instance %s در State '%s' ساخته شد.",
                len(tasks), instance.id, state.code,
            )
        else:
            logger.warning(
                "هیچ کاربری برای نقش‌های %s در State '%s' یافت نشد.",
                role_codes, state.code,
            )