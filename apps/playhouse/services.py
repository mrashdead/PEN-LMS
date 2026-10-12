"""
Playhouse business logic (service layer).

All state transitions live here, fully validated and wrapped in atomic
transactions with row locking where a race could bite (ending a session,
creating an invoice). Views/pages only serialise HTTP input and call these.
"""
from __future__ import annotations

import logging
import uuid
from datetime import date
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.playhouse.models import (
    PlayhouseConfig,
    PlayhouseInvoice,
    PlayhouseInvoiceItem,
    PlayhouseInvoiceSeq,
    PlayhouseCafeOrder,
    PlayhouseCafeOrderItem,
    PlayhousePayment,
    PlayhouseMember,
    PlayhouseSession,
)
from apps.persons.models import Person

logger = logging.getLogger(__name__)

NUMBER_RETRY_LIMIT = 5


class PlayhouseServiceError(Exception):
    """Domain-level validation failure surfaced as an HTTP 400 by the API layer."""


class PlayhouseService:
    """Stateless facade over playhouse operations (injected via ``services``)."""

    # ─── ورود ───
    @transaction.atomic
    def create_session(
        self,
        *,
        operator,
        first_name: str,
        last_name: str,
        age: int | None = None,
        guardian_mobile: str = "",
        session_date: date | None = None,
        member_pk: int | None = None,
        person_pk=None,
        national_code: str = "",
        student_code: str = "",
    ) -> PlayhouseSession:
        """
        Create a playhouse entry.

        When ``member_pk`` is given the operator picked an existing member;
        otherwise a ``PlayhouseMember`` is created (and, if a matching Person
        exists, linked to it — see ``_maybe_link_person``).
        """
        config = PlayhouseConfig.get_solo()
        if not config.is_open_now:
            raise PlayhouseServiceError(
                "خانه بازی اکنون باز نیست — ثبت ورود جدید مسدود است."
            )
        if not config.is_within_working_hours():
            raise PlayhouseServiceError(
                "خارج از ساعات کاری خانه بازی — ثبت ورود مجاز نیست."
            )
        member = self._resolve_member(
            operator=operator,
            first_name=first_name,
            last_name=last_name,
            age=age,
            guardian_mobile=guardian_mobile,
            member_pk=member_pk,
            person_pk=person_pk,
            national_code=national_code,
            student_code=student_code,
        )
        session = PlayhouseSession.objects.create(
            member=member,
            operator=operator,
            session_date=session_date or timezone.localdate(),
            status=PlayhouseSession.Status.WAITING,
        )
        return session

    def _resolve_member(self, *, operator, first_name, last_name, age,
                        guardian_mobile, member_pk, person_pk=None,
                        national_code="", student_code="") -> PlayhouseMember:
        if member_pk:
            member = PlayhouseMember.objects.select_related("person").filter(pk=member_pk).first()
            if member is None:
                raise PlayhouseServiceError("عضو انتخاب‌شده پیدا نشد.")
            entered_code = (national_code or "").strip()
            if member.person_id:
                person_code = (member.person.national_code or "").strip()
                if entered_code and person_code and entered_code != person_code:
                    raise PlayhouseServiceError("کد ملی با پرونده دانش‌آموز انتخاب‌شده مطابقت ندارد.")
                if entered_code and not person_code:
                    if Person.objects.filter(national_code=entered_code, is_deleted=False).exclude(pk=member.person_id).exists():
                        raise PlayhouseServiceError("این کد ملی به پرونده شخص دیگری متصل است.")
                    member.person.national_code = entered_code
                    member.person.is_temporary = False
                    member.person.save(update_fields=["national_code", "is_temporary", "updated_at"])
                member.national_code = person_code or entered_code or member.national_code
            elif entered_code:
                member.national_code = entered_code
            if member.national_code:
                member.save(update_fields=["national_code", "updated_at"])
            return member

        if person_pk:
            person = Person.objects.filter(
                pk=person_pk,
                person_type=Person.Type.STUDENT,
                is_active=True,
            ).first()
            if person is None:
                raise PlayhouseServiceError("دانش‌آموز انتخاب‌شده پیدا نشد.")
            entered_code = (national_code or "").strip()
            if entered_code and entered_code != person.national_code:
                raise PlayhouseServiceError("کد ملی با پرونده دانش‌آموز انتخاب‌شده مطابقت ندارد.")
            member = PlayhouseMember.objects.filter(person=person).first()
            if member is not None:
                if member.national_code != person.national_code:
                    member.national_code = person.national_code
                    member.save(update_fields=["national_code", "updated_at"])
                return member
            return PlayhouseMember.objects.create(
                person=person,
                temporary_id=person.temporary_id,
                first_name=person.first_name,
                last_name=person.last_name,
                national_code=person.national_code,
                age=age,
                guardian_mobile=(guardian_mobile or person.mobile or "").strip(),
            )

        person = self._maybe_link_person(first_name, last_name, guardian_mobile) if not national_code else None
        if person is None and national_code:
            person = Person.objects.filter(
                national_code=national_code.strip(),
                is_active=True,
                is_deleted=False,
            ).first()
        if person is None and student_code:
            person = Person.objects.filter(
                student_code=student_code.strip(),
                is_active=True,
                is_deleted=False,
            ).first()
        if person is None:
            person = Person.objects.create(
                national_code=national_code.strip() or None,
                student_code=student_code.strip() or None,
                first_name=first_name.strip(),
                last_name=last_name.strip(),
                mobile=(guardian_mobile or "").strip(),
                person_type=Person.Type.STUDENT,
                registered_by=operator,
                temporary_id=uuid.uuid4() if not national_code.strip() else None,
                is_temporary=not bool(national_code.strip()),
            )
        member_code = (person.national_code if person else national_code) or ""
        if person is not None:
            member = PlayhouseMember.objects.filter(person=person).first()
            if member is not None:
                if member.national_code != member_code:
                    member.national_code = member_code
                if not member.temporary_id and person.temporary_id:
                    member.temporary_id = person.temporary_id
                member.save(update_fields=["national_code", "temporary_id", "updated_at"])
                return member

        if national_code:
            member_query = PlayhouseMember.objects.filter(
                national_code=national_code.strip(),
            )
            if person is not None:
                member_query = member_query.filter(person__isnull=True)
            existing_member = member_query.first()
            if existing_member is not None:
                changed_fields = []
                if person is not None:
                    existing_member.person = person
                    changed_fields.append("person")
                if person is not None and person.temporary_id:
                    existing_member.temporary_id = person.temporary_id
                    changed_fields.append("temporary_id")
                if existing_member.national_code != member_code:
                    existing_member.national_code = member_code
                    changed_fields.append("national_code")
                if changed_fields:
                    existing_member.save(update_fields=[*changed_fields, "updated_at"])
                return existing_member
        member = PlayhouseMember.objects.create(
            person=person,
            temporary_id=person.temporary_id if person and person.is_temporary else None,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            national_code=member_code.strip(),
            age=age,
            guardian_mobile=guardian_mobile.strip(),
        )
        return member

    def _maybe_link_person(self, first_name, last_name, guardian_mobile):
        """Link only on exact name + contact; names alone are ambiguous."""
        if not (guardian_mobile or "").strip():
            return None
        qs = Person.objects.filter(first_name__iexact=first_name.strip(),
                                   last_name__iexact=last_name.strip(),
                                   mobile=guardian_mobile.strip())
        return qs.order_by("-created_at").first()

    @transaction.atomic
    def update_member(self, *, member, data) -> PlayhouseMember:
        """Edit identity/profile fields while leaving every session untouched."""
        locked = PlayhouseMember.objects.select_for_update().select_related("person").get(pk=member.pk)
        person = locked.person
        if person is None:
            # Compatibility for legacy rows that predate canonical Person links.
            person = Person.objects.create(
                national_code=locked.national_code or None,
                first_name=locked.first_name,
                last_name=locked.last_name,
                mobile=locked.guardian_mobile,
                person_type=Person.Type.STUDENT,
                is_temporary=not bool(locked.national_code),
                temporary_id=locked.temporary_id or uuid.uuid4(),
            )
            locked.person = person
            locked.temporary_id = person.temporary_id

        national_code = data.get("national_code", person.national_code or "")
        national_code = national_code or None
        target = None
        if national_code:
            target = Person.objects.select_for_update().filter(
                national_code=national_code, is_deleted=False
            ).exclude(pk=person.pk).first()
        if target:
            linked_elsewhere = PlayhouseMember.objects.filter(person=target).exclude(pk=locked.pk).exists()
            if linked_elsewhere:
                raise PlayhouseServiceError("این کد ملی به پرونده دیگری در سوابق خانه بازی متصل است.")
            # Move the stable temporary identifier to the existing canonical
            # person so the member/session history continues through one link.
            if person.temporary_id and not target.temporary_id:
                target.temporary_id = person.temporary_id
            # Retain the provisional Person row for audit/history while
            # moving the stable identifier and member link to the canonical
            # official record.
            person.is_deleted = True
            person.is_active = False
            person.temporary_id = None
            person.save(update_fields=["is_deleted", "is_active", "temporary_id", "updated_at"])
            person = target
            locked.person = target

        for key in ("first_name", "last_name", "student_code"):
            if key in data:
                setattr(person, key, data[key] or (None if key == "student_code" else ""))
        if "guardian_mobile" in data:
            person.mobile = data["guardian_mobile"]
        if national_code != person.national_code:
            person.national_code = national_code
        person.is_temporary = not bool(person.national_code)
        if person.is_temporary and not person.temporary_id:
            person.temporary_id = uuid.uuid4()
        person.save()

        locked.first_name = person.first_name
        locked.last_name = person.last_name
        locked.national_code = person.national_code or ""
        locked.temporary_id = person.temporary_id
        for key in ("age", "guardian_mobile", "guardian_name"):
            if key in data:
                setattr(locked, key, data[key])
        locked.save()
        return locked

    # ─── تایمر ───
    @transaction.atomic
    def start_session(self, *, session, operator, entry_at=None) -> PlayhouseSession:
        """Start a waiting session or resume one paused by the operator."""
        locked = PlayhouseSession.objects.select_for_update().get(pk=session.pk)
        if locked.status not in {
            PlayhouseSession.Status.WAITING,
            PlayhouseSession.Status.PAUSED,
        }:
            raise PlayhouseServiceError(
                "فقط نوبت‌های «در انتظار ورود» یا «متوقف شده» قابل شروع هستند."
            )
        now = timezone.now()
        if locked.status == PlayhouseSession.Status.WAITING:
            if entry_at:
                parsed = parse_datetime(entry_at) if isinstance(entry_at, str) else entry_at
                if parsed is None:
                    raise PlayhouseServiceError("زمان شروع نامعتبر است.")
                if timezone.is_naive(parsed):
                    parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
                if parsed > now:
                    raise PlayhouseServiceError("زمان شروع نمی‌تواند در آینده باشد.")
                locked.entry_at = parsed
                locked.session_date = timezone.localdate(parsed)
            else:
                locked.entry_at = now
            locked.paused_seconds = 0
        elif locked.paused_at:
            locked.paused_seconds += max(0, int((now - locked.paused_at).total_seconds()))
        locked.paused_at = None
        locked.status = PlayhouseSession.Status.ACTIVE
        locked.save(update_fields=["entry_at", "session_date", "paused_at", "paused_seconds", "status", "updated_at"])
        return locked

    @transaction.atomic
    def stop_session(self, *, session, operator) -> PlayhouseSession:
        """Pause the timer without ending the visit or losing elapsed time."""
        locked = PlayhouseSession.objects.select_for_update().get(pk=session.pk)
        if locked.status != PlayhouseSession.Status.ACTIVE:
            raise PlayhouseServiceError("فقط نوبت‌های فعال قابل توقف هستند.")
        locked.paused_at = timezone.now()
        locked.status = PlayhouseSession.Status.PAUSED
        locked.save(update_fields=["paused_at", "status", "updated_at"])
        return locked

    @transaction.atomic
    def end_session(self, *, session, operator, exit_at=None) -> PlayhouseSession:
        """Stop the timer for good and compute the billable duration."""
        locked = PlayhouseSession.objects.select_for_update().get(pk=session.pk)
        if locked.status not in {
            PlayhouseSession.Status.ACTIVE,
            PlayhouseSession.Status.PAUSED,
            PlayhouseSession.Status.WAITING,
        }:
            raise PlayhouseServiceError("این نوبت قبلاً پایان یافته است.")
        if locked.status == PlayhouseSession.Status.WAITING and not locked.entry_at:
            raise PlayhouseServiceError("برای پایان حضور، ابتدا زمان واقعی ورود را ثبت کنید.")
        now = timezone.now()
        if exit_at:
            parsed = parse_datetime(exit_at) if isinstance(exit_at, str) else exit_at
            if parsed is None:
                raise PlayhouseServiceError("زمان پایان نامعتبر است.")
            if timezone.is_naive(parsed):
                parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
            now = parsed
        if locked.entry_at and now < locked.entry_at:
            raise PlayhouseServiceError("زمان پایان نمی‌تواند قبل از زمان شروع باشد.")
        if now > timezone.now():
            raise PlayhouseServiceError("زمان پایان نمی‌تواند در آینده باشد.")
        if locked.status == PlayhouseSession.Status.PAUSED and locked.paused_at:
            locked.paused_seconds += max(0, int((now - locked.paused_at).total_seconds()))
        locked.exit_at = now
        locked.paused_at = None
        locked.billable_minutes = self._compute_billable_minutes(locked)
        locked.ended_by = operator
        locked.status = PlayhouseSession.Status.FINISHED
        locked.save(update_fields=[
            "exit_at", "paused_at", "paused_seconds", "billable_minutes", "ended_by", "status", "updated_at",
        ])
        return locked

    @staticmethod
    def _compute_billable_minutes(session: PlayhouseSession) -> int:
        """Raw elapsed minutes rounded to the nearest 15-minute block."""
        if not session.entry_at:
            return 0
        raw = int(session.elapsed_seconds // 60)
        from apps.playhouse.models import round_to_nearest_15
        return round_to_nearest_15(max(0, raw))

    @transaction.atomic
    def cancel_session(self, *, session, operator) -> PlayhouseSession:
        locked = PlayhouseSession.objects.select_for_update().get(pk=session.pk)
        if locked.status in {PlayhouseSession.Status.FINISHED,
                             PlayhouseSession.Status.CANCELLED}:
            raise PlayhouseServiceError("این نوبت قابل لغو نیست.")
        locked.status = PlayhouseSession.Status.CANCELLED
        locked.exit_at = timezone.now()
        locked.paused_at = None
        locked.save(update_fields=["status", "exit_at", "paused_at", "updated_at"])
        return locked

    # ─── فاکتور ───
    @transaction.atomic
    def create_cafe_order(self, *, session, operator, items, payments=None, kitchen_note=""):
        """Append a cafe order and optional split payments to an active visit."""
        locked = PlayhouseSession.objects.select_for_update().get(pk=session.pk)
        if locked.status not in {PlayhouseSession.Status.ACTIVE, PlayhouseSession.Status.PAUSED}:
            raise PlayhouseServiceError("ثبت سفارش فقط برای مراجعه داخل خانه‌بازی ممکن است.")
        if not items:
            raise PlayhouseServiceError("حداقل یک آیتم برای سفارش وارد کنید.")
        order = PlayhouseCafeOrder.objects.create(
            session=locked, created_by=operator, kitchen_note=(kitchen_note or "").strip()
        )
        for item in items:
            name = str(item.get("name") or "").strip()
            try:
                price = Decimal(str(item.get("unit_price", item.get("price"))))
                quantity = int(item.get("quantity", 1))
            except (ValueError, TypeError, ArithmeticError):
                raise PlayhouseServiceError("تعداد یا قیمت یکی از آیتم‌ها نامعتبر است.")
            if not name or price < 0 or quantity < 1 or quantity > 99:
                raise PlayhouseServiceError("نام، قیمت و تعداد آیتم‌ها را بررسی کنید.")
            PlayhouseCafeOrderItem.objects.create(
                order=order, name=name, unit_price=price, quantity=quantity,
                note=str(item.get("note") or "").strip(),
            )
        rows = self._create_payments(session=locked, operator=operator, payments=payments or [], cafe_order=order)
        current_orders_total = sum(
            (item.line_total for item in PlayhouseCafeOrderItem.objects.filter(
                order__session=locked,
                order__status__in=[PlayhouseCafeOrder.Status.NEW, PlayhouseCafeOrder.Status.PREPARING, PlayhouseCafeOrder.Status.READY],
            )), Decimal("0")
        )
        current_paid = sum(
            (row.amount for row in PlayhousePayment.objects.filter(session=locked, reversed_at__isnull=True)), Decimal("0")
        )
        if current_paid > current_orders_total:
            raise PlayhouseServiceError("مبلغ پرداخت از جمع سفارش‌های کافه بیشتر است.")
        return order

    @transaction.atomic
    def add_session_payments(self, *, session, operator, payments):
        locked = PlayhouseSession.objects.select_for_update().get(pk=session.pk)
        if locked.status == PlayhouseSession.Status.CANCELLED:
            raise PlayhouseServiceError("برای مراجعه لغوشده پرداخت ثبت نمی‌شود.")
        if not payments:
            raise PlayhouseServiceError("حداقل یک مبلغ پرداخت وارد کنید.")
        invoice = locked.invoice
        if locked.status == PlayhouseSession.Status.FINISHED and not invoice:
            raise PlayhouseServiceError("ابتدا فاکتور مراجعه را صادر یا اصلاح کنید.")
        if invoice:
            if invoice.is_paid and not invoice.session.payments.filter(reversed_at__isnull=True).exists():
                raise PlayhouseServiceError("این فاکتور قدیمی پرداخت‌شده است و پرداخت تازه نمی‌پذیرد.")
        rows = self._create_payments(session=locked, operator=operator, payments=payments)
        if invoice:
            if invoice.paid_amount > invoice.total_amount:
                raise PlayhouseServiceError("مبلغ پرداخت از مانده فاکتور بیشتر است.")
            invoice.is_paid = invoice.total_amount > 0 and invoice.paid_amount >= invoice.total_amount
            invoice.paid_at = timezone.now() if invoice.is_paid else None
            invoice.save(update_fields=["is_paid", "paid_at", "updated_at"])
        else:
            cafe_total = sum((item.line_total for item in PlayhouseCafeOrderItem.objects.filter(
                order__session=locked,
                order__status__in=[PlayhouseCafeOrder.Status.NEW, PlayhouseCafeOrder.Status.PREPARING, PlayhouseCafeOrder.Status.READY],
            )), Decimal("0"))
            current_paid = sum((row.amount for row in PlayhousePayment.objects.filter(
                session=locked, reversed_at__isnull=True
            )), Decimal("0"))
            if current_paid > cafe_total:
                raise PlayhouseServiceError("مبلغ پرداخت از جمع سفارش‌های فعال کافه بیشتر است.")
        return rows

    def _create_payments(self, *, session, operator, payments, cafe_order=None):
        rows = []
        for payment in payments:
            method = str(payment.get("method") or "")
            try:
                amount = Decimal(str(payment.get("amount")))
            except (ValueError, TypeError, ArithmeticError):
                raise PlayhouseServiceError("مبلغ پرداخت نامعتبر است.")
            tracking_code = str(payment.get("tracking_code") or "").strip()
            if method not in PlayhousePayment.Method.values or amount <= 0:
                raise PlayhouseServiceError("روش یا مبلغ پرداخت نامعتبر است.")
            if method == PlayhousePayment.Method.CARD_TRANSFER and not tracking_code:
                raise PlayhouseServiceError("برای کارت‌به‌کارت کد رهگیری لازم است.")
            invoice = None
            try:
                invoice = session.invoice
            except PlayhouseInvoice.DoesNotExist:
                pass
            rows.append(PlayhousePayment.objects.create(
                session=session, invoice=invoice, created_by=operator,
                cafe_order=cafe_order, method=method, amount=amount, tracking_code=tracking_code,
            ))
        return rows

    @transaction.atomic
    def set_cafe_order_status(self, *, order, operator, status_value):
        locked = PlayhouseCafeOrder.objects.select_for_update().get(pk=order.pk)
        if locked.status in {PlayhouseCafeOrder.Status.CANCELLED, PlayhouseCafeOrder.Status.READY}:
            raise PlayhouseServiceError("وضعیت این سفارش دیگر قابل تغییر نیست.")
        if status_value not in {PlayhouseCafeOrder.Status.PREPARING, PlayhouseCafeOrder.Status.READY}:
            raise PlayhouseServiceError("وضعیت سفارش نامعتبر است.")
        locked.status = status_value
        if status_value == PlayhouseCafeOrder.Status.READY:
            locked.ready_at = timezone.now()
            locked.ready_by = operator
        locked.save(update_fields=["status", "ready_at", "ready_by", "updated_at"])
        return locked

    @transaction.atomic
    def cancel_cafe_order(self, *, order, operator, note=""):
        locked = PlayhouseCafeOrder.objects.select_for_update().select_related("session").get(pk=order.pk)
        if locked.status == PlayhouseCafeOrder.Status.CANCELLED:
            raise PlayhouseServiceError("این سفارش قبلاً لغو شده است.")
        if not (note or "").strip():
            raise PlayhouseServiceError("برای لغو سفارش، دلیل را ثبت کنید.")
        if locked.session.status == PlayhouseSession.Status.FINISHED:
            raise PlayhouseServiceError("سفارش پس از صدور فاکتور قابل لغو نیست.")
        if locked.payments.filter(reversed_at__isnull=True).exists():
            raise PlayhouseServiceError("ابتدا پرداخت‌های این سفارش را با ذکر دلیل برگشت بزنید.")
        locked.status = PlayhouseCafeOrder.Status.CANCELLED
        locked.cancelled_at = timezone.now()
        locked.cancelled_by = operator
        locked.cancellation_note = (note or "").strip()
        locked.save(update_fields=["status", "cancelled_at", "cancelled_by", "cancellation_note", "updated_at"])
        return locked

    @transaction.atomic
    def void_invoice(self, *, invoice, operator, note):
        """Void a bill without deleting it; payment rows can be carried to a replacement bill."""
        locked = PlayhouseInvoice.objects.select_for_update().get(pk=invoice.pk)
        reason = (note or "").strip()
        if not reason:
            raise PlayhouseServiceError("برای ابطال فاکتور، دلیل را ثبت کنید.")
        if locked.is_voided:
            raise PlayhouseServiceError("این فاکتور قبلاً باطل شده است.")
        locked.is_voided = True
        locked.voided_at = timezone.now()
        locked.voided_by = operator
        locked.void_note = reason
        locked.is_paid = False
        locked.save(update_fields=["is_voided", "voided_at", "voided_by", "void_note", "is_paid", "updated_at"])
        return locked

    @transaction.atomic
    def reverse_payment(self, *, payment, operator, note):
        locked = PlayhousePayment.objects.select_for_update().select_related("invoice").get(pk=payment.pk)
        reason = (note or "").strip()
        if not reason:
            raise PlayhouseServiceError("برای برگشت پرداخت، دلیل را ثبت کنید.")
        if locked.reversed_at:
            raise PlayhouseServiceError("این پرداخت قبلاً برگشت خورده است.")
        locked.reversed_at = timezone.now()
        locked.reversed_by = operator
        locked.reversal_note = reason
        locked.save(update_fields=["reversed_at", "reversed_by", "reversal_note", "updated_at"])
        invoice = locked.invoice
        if invoice and not invoice.is_voided:
            invoice.is_paid = invoice.total_amount > 0 and invoice.paid_amount >= invoice.total_amount
            invoice.paid_at = timezone.now() if invoice.is_paid else None
            invoice.save(update_fields=["is_paid", "paid_at", "updated_at"])
        return locked

    @transaction.atomic
    def create_invoice(
        self,
        *,
        session,
        operator,
        cafe_items: list[dict] | None = None,
        payment_method: str = "",
        tracking_code: str = "",
        notes: str = "",
        discount_amount: int | Decimal = 0,
        discount_note: str = "",
    ) -> PlayhouseInvoice:
        """
        Build the invoice for a finished session.

        Billing: ``billed_minutes`` from the session (already rounded to 15),
        multiplied by the *current* config price — snapshotted onto the
        invoice so later config edits are non-destructive.
        """
        locked = PlayhouseSession.objects.select_for_update().get(pk=session.pk)
        if locked.status != PlayhouseSession.Status.FINISHED:
            raise PlayhouseServiceError(
                "برای صدور فاکتور، نوبت باید «پایان یافته» باشد."
            )
        if locked.invoices.filter(is_voided=False).exists():
            raise PlayhouseServiceError("برای این نوبت قبلاً فاکتور صادر شده است.")

        config = PlayhouseConfig.get_solo()
        time_amount = (Decimal(locked.billable_minutes) / Decimal(15)).quantize(Decimal("1")) * config.price_per_15_minutes

        invoice = self._create_with_unique_number(
            session=locked,
            operator=operator,
            price=config.price_per_15_minutes,
            time_amount=time_amount,
        )

        try:
            orders = PlayhouseCafeOrder.objects.filter(
                session=locked, status__in=[PlayhouseCafeOrder.Status.NEW, PlayhouseCafeOrder.Status.PREPARING, PlayhouseCafeOrder.Status.READY]
            ).prefetch_related("items")
            for order in orders:
                for order_item in order.items.all():
                    PlayhouseInvoiceItem.objects.create(
                        invoice=invoice, name=order_item.name,
                        price=order_item.unit_price, quantity=order_item.quantity,
                    )
        except Exception:
            raise

        for item in cafe_items or []:
            name = (item.get("name") or "").strip()
            price_raw = item.get("price")
            if not name or price_raw is None:
                continue
            try:
                price = Decimal(str(price_raw))
            except (ValueError, ArithmeticError):
                continue
            PlayhouseInvoiceItem.objects.create(
                invoice=invoice, name=name, price=price,
            )

        try:
            discount = Decimal(str(discount_amount or 0))
        except (ValueError, ArithmeticError):
            raise PlayhouseServiceError("مبلغ تخفیف نامعتبر است.")
        if discount < 0 or discount > invoice.time_amount + invoice.cafe_total:
            raise PlayhouseServiceError("مبلغ تخفیف از مبلغ فاکتور بیشتر است.")
        invoice.discount_amount = discount
        invoice.discount_note = (discount_note or "").strip()
        invoice.save(update_fields=["discount_amount", "discount_note", "updated_at"])
        already_paid = sum((row.amount for row in PlayhousePayment.objects.filter(
            session=locked, reversed_at__isnull=True
        )), Decimal("0"))
        if already_paid > invoice.total_amount:
            raise PlayhouseServiceError("تخفیف باعث می‌شود مبلغ پرداخت‌شده از مبلغ فاکتور بیشتر شود.")
        PlayhousePayment.objects.filter(session=locked, invoice__isnull=True).update(invoice=invoice)
        invoice.is_paid = invoice.total_amount > 0 and invoice.paid_amount >= invoice.total_amount
        invoice.paid_at = timezone.now() if invoice.is_paid and invoice.total_amount > 0 else None
        invoice.save(update_fields=["is_paid", "paid_at", "updated_at"])

        if payment_method or tracking_code:
            # record_payment re-fetches a locked instance and saves it; its
            # return value is the fresh, saved one — must use it, else the
            # caller sees a stale (unpaid) instance.
            invoice = self.record_payment(
                invoice=invoice,
                operator=operator,
                payment_method=payment_method,
                tracking_code=tracking_code,
                paid=bool(payment_method and (tracking_code or payment_method == PlayhouseInvoice.PaymentMethod.CASH)),
            )
        return invoice

    @transaction.atomic
    def _create_with_unique_number(self, *, session, operator, price, time_amount) -> PlayhouseInvoice:
        """Insert the invoice, retrying ONLY on an invoice-number collision.

        The number comes from a per-(year, day) counter held with
        ``select_for_update()``. On SQLite the counter lock is a no-op, so the
        unique constraint on ``invoice_number`` plus this bounded retry is the
        final source of truth.
        """
        last_error: IntegrityError | None = None
        for attempt in range(NUMBER_RETRY_LIMIT):
            try:
                with transaction.atomic():
                    number = self._next_invoice_number()
                    return PlayhouseInvoice.objects.create(
                        session=session,
                        member=session.member,
                        operator=operator,
                        price_per_15_minutes=price,
                        billed_minutes=session.billable_minutes,
                        time_amount=time_amount,
                        invoice_number=number,
                    )
            except IntegrityError as exc:
                if "invoice_number" not in str(exc):
                    raise
                last_error = exc
                logger.warning(
                    "invoice_number collision (attempt %d/%d)", attempt + 1, NUMBER_RETRY_LIMIT
                )
        raise PlayhouseServiceError(
            f"تخصیص شماره فاکتور پس از {NUMBER_RETRY_LIMIT} بار تلاش ممکن نشد."
        ) from last_error

    @transaction.atomic
    def _next_invoice_number(self) -> str:
        """Reserve the next sequence value for today and build PH-YYYYMMDD-NNNN."""
        now = timezone.now()
        year, day = now.year, now.day
        try:
            with transaction.atomic():
                seq, _created = PlayhouseInvoiceSeq.objects.get_or_create(
                    year=year, day=day, defaults={"last_value": 0}
                )
        except IntegrityError:
            # concurrent creation — take the winner
            seq = PlayhouseInvoiceSeq.objects.get(year=year, day=day)
        seq = PlayhouseInvoiceSeq.objects.select_for_update().get(pk=seq.pk)
        seq.last_value = (seq.last_value or 0) + 1
        seq.save(update_fields=["last_value", "updated_at"])
        return f"PH-{year:04d}{day:02d}-{seq.last_value:04d}"

    @transaction.atomic
    def record_payment(
        self,
        *,
        invoice,
        operator,
        payment_method: str = "",
        tracking_code: str = "",
        paid: bool = True,
    ) -> PlayhouseInvoice:
        locked = PlayhouseInvoice.objects.select_for_update().get(pk=invoice.pk)
        if locked.is_voided:
            raise PlayhouseServiceError("برای فاکتور باطل‌شده نمی‌توان پرداخت ثبت کرد.")
        if locked.is_paid and not locked.session.payments.filter(reversed_at__isnull=True).exists():
            raise PlayhouseServiceError("این فاکتور قبلاً پرداخت شده است.")
        if payment_method not in PlayhouseInvoice.PaymentMethod.values:
            raise PlayhouseServiceError("روش پرداخت نامعتبر است.")
        if paid:
            if payment_method != PlayhouseInvoice.PaymentMethod.CASH and not tracking_code:
                raise PlayhouseServiceError("برای پرداخت، کد رهگیری الزامی است.")
            allocated = sum((p.amount for p in locked.session.payments.filter(reversed_at__isnull=True)), Decimal("0"))
            remaining = max(Decimal("0"), locked.total_amount - allocated)
            if remaining > 0:
                PlayhousePayment.objects.create(
                    session=locked.session, invoice=locked, created_by=operator,
                    method=payment_method, amount=remaining, tracking_code=tracking_code,
                )
        locked.payment_method = payment_method
        locked.tracking_code = tracking_code
        locked.is_paid = locked.paid_amount >= locked.total_amount if paid else False
        locked.paid_at = timezone.now() if locked.is_paid else None
        locked.save(update_fields=[
            "payment_method", "tracking_code", "is_paid", "paid_at", "updated_at",
        ])
        return locked

    # ─── تنظیمات ───
    @transaction.atomic
    def update_config(
        self,
        *,
        operator,
        price_per_15_minutes,
        open_time=None,
        close_time=None,
        is_open_now: bool = True,
    ) -> "PlayhouseConfig":
        """Update the singleton billing settings (manager-only by permission)."""
        config = PlayhouseConfig.get_solo()
        try:
            price = Decimal(str(price_per_15_minutes))
        except (ValueError, ArithmeticError):
            raise PlayhouseServiceError("قیمت واردشده معتبر نیست.")
        if price < 0:
            raise PlayhouseServiceError("قیمت نمی‌تواند منفی باشد.")
        if open_time and close_time and close_time <= open_time:
            raise PlayhouseServiceError("ساعت بسته شدن باید بعد از ساعت باز شدن باشد.")

        config.price_per_15_minutes = price
        config.open_time = open_time or None
        config.close_time = close_time or None
        config.is_open_now = is_open_now
        config.save(update_fields=[
            "price_per_15_minutes", "open_time", "close_time", "is_open_now", "updated_at",
        ])
        # invalidate the cached singleton pk so later reads re-fetch
        PlayhouseConfig._singleton_pk = None
        return config
