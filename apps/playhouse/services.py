"""
Playhouse business logic (service layer).

All state transitions live here, fully validated and wrapped in atomic
transactions with row locking where a race could bite (ending a session,
creating an invoice). Views/pages only serialise HTTP input and call these.
"""
from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.playhouse.models import (
    PlayhouseConfig,
    PlayhouseInvoice,
    PlayhouseInvoiceItem,
    PlayhouseInvoiceSeq,
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
            session_date=session_date or date.today(),
            status=PlayhouseSession.Status.WAITING,
        )
        return session

    def _resolve_member(self, *, operator, first_name, last_name, age,
                        guardian_mobile, member_pk, person_pk=None,
                        national_code="", student_code="") -> PlayhouseMember:
        if member_pk:
            member = PlayhouseMember.objects.filter(pk=member_pk).first()
            if member is None:
                raise PlayhouseServiceError("عضو انتخاب‌شده پیدا نشد.")
            return member

        if person_pk:
            person = Person.objects.filter(
                pk=person_pk,
                person_type=Person.Type.STUDENT,
                is_active=True,
            ).first()
            if person is None:
                raise PlayhouseServiceError("دانش‌آموز انتخاب‌شده پیدا نشد.")
            member = PlayhouseMember.objects.filter(person=person).first()
            if member is not None:
                return member
            return PlayhouseMember.objects.create(
                person=person,
                first_name=person.first_name,
                last_name=person.last_name,
                age=age,
                guardian_mobile=(guardian_mobile or person.mobile or "").strip(),
            )

        person = self._maybe_link_person(first_name, last_name, guardian_mobile)
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
        if person is None and national_code and student_code:
            person = Person.objects.create(
                national_code=national_code.strip(),
                student_code=student_code.strip(),
                first_name=first_name.strip(),
                last_name=last_name.strip(),
                mobile=(guardian_mobile or "").strip(),
                person_type=Person.Type.STUDENT,
                registered_by=operator,
            )
        member = PlayhouseMember.objects.create(
            person=person,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            age=age,
            guardian_mobile=guardian_mobile.strip(),
        )
        return member

    def _maybe_link_person(self, first_name, last_name, guardian_mobile):
        """Best-effort: link to an existing Person on exact (first,last[,mobile])."""
        qs = Person.objects.filter(first_name__iexact=first_name.strip(),
                                   last_name__iexact=last_name.strip())
        if guardian_mobile:
            qs = qs.filter(mobile=guardian_mobile.strip())
        return qs.order_by("-created_at").first()

    # ─── تایمر ───
    @transaction.atomic
    def start_session(self, *, session, operator) -> PlayhouseSession:
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
            locked.entry_at = now
            locked.paused_seconds = 0
        elif locked.paused_at:
            locked.paused_seconds += max(0, int((now - locked.paused_at).total_seconds()))
        locked.paused_at = None
        locked.status = PlayhouseSession.Status.ACTIVE
        locked.save(update_fields=["entry_at", "paused_at", "paused_seconds", "status", "updated_at"])
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
    def end_session(self, *, session, operator) -> PlayhouseSession:
        """Stop the timer for good and compute the billable duration."""
        locked = PlayhouseSession.objects.select_for_update().get(pk=session.pk)
        if locked.status not in {
            PlayhouseSession.Status.ACTIVE,
            PlayhouseSession.Status.PAUSED,
            PlayhouseSession.Status.WAITING,
        }:
            raise PlayhouseServiceError("این نوبت قبلاً پایان یافته است.")
        now = timezone.now()
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
    def create_invoice(
        self,
        *,
        session,
        operator,
        cafe_items: list[dict] | None = None,
        payment_method: str = "",
        tracking_code: str = "",
        notes: str = "",
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
        if hasattr(locked, "invoice"):
            raise PlayhouseServiceError("برای این نوبت قبلاً فاکتور صادر شده است.")

        config = PlayhouseConfig.get_solo()
        time_amount = (Decimal(locked.billable_minutes) / Decimal(15)).quantize(Decimal("1")) * config.price_per_15_minutes

        invoice = self._create_with_unique_number(
            session=locked,
            operator=operator,
            price=config.price_per_15_minutes,
            time_amount=time_amount,
        )

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
                invoice=invoice, name=name, price=price
            )

        if payment_method or tracking_code:
            # record_payment re-fetches a locked instance and saves it; its
            # return value is the fresh, saved one — must use it, else the
            # caller sees a stale (unpaid) instance.
            invoice = self.record_payment(
                invoice=invoice,
                operator=operator,
                payment_method=payment_method,
                tracking_code=tracking_code,
                paid=bool(payment_method and tracking_code),
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
        if payment_method not in PlayhouseInvoice.PaymentMethod.values:
            raise PlayhouseServiceError("روش پرداخت نامعتبر است.")
        if paid:
            if not tracking_code:
                raise PlayhouseServiceError("برای پرداخت، کد رهگیری الزامی است.")
        locked.payment_method = payment_method
        locked.tracking_code = tracking_code
        locked.is_paid = paid
        locked.paid_at = timezone.now() if paid else None
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
