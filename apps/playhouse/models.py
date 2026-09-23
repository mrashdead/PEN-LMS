"""
Playhouse domain models (خانه بازی).

Entities:
- ``PlayhouseConfig``: singleton site settings (15-minute price).
- ``PlayhouseMember``: a child that has visited the playhouse, optionally linked
  to an existing ``Person`` when that child is already enrolled in the system.
- ``PlayhouseSession``: one timed visit (entry → exit), driven by a live timer.
- ``PlayhouseInvoice``: the billed record (time + cafe items + payment).
- ``PlayhouseInvoiceItem``: cafe line items on an invoice.

The 15-minute billing block is a *decision recorded at invoice time*: the
session stores ``billable_minutes`` and the invoice snapshots ``price_per_15``
so later price changes never retroactively alter historical invoices.
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import DomainModel
from apps.persons.models import Person


def _fee_decimal(value: str | int | Decimal) -> Decimal:
    """Normalise any money-ish value to a 2-dp Decimal (avoid float drift)."""
    return Decimal(value) if isinstance(value, Decimal) else Decimal(str(value))


def round_to_nearest_15(minutes: int) -> int:
    """Round a minute count to the nearest 15-minute block (half-up)."""
    if minutes <= 0:
        return 0
    return int((Decimal(minutes) / Decimal(15)).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * 15)


class PlayhouseConfig(DomainModel):
    """Singleton holding playhouse billing settings (edited in admin or page)."""

    price_per_15_minutes = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=130000,
        help_text="هزینه هر ۱۵ دقیقه خانه بازی (تومان)",
    )

    # ─── ساعات کاری (کنترل دسترسی بر اساس ساعت) ───
    open_time = models.TimeField(
        null=True, blank=True,
        help_text="ساعت باز شدن خانه بازی (اختیاری)",
    )
    close_time = models.TimeField(
        null=True, blank=True,
        help_text="ساعت بسته شدن خانه بازی (اختیاری)",
    )
    is_open_now = models.BooleanField(
        default=True,
        help_text="اگر خاموش باشد، ثبت ورود جدید مسدود می‌شود",
    )

    class Meta:
        app_label = "playhouse"
        db_table = "playhouse_config"
        verbose_name = "تنظیمات خانه بازی"
        verbose_name_plural = "تنظیمات خانه بازی"

    def __str__(self) -> str:
        return f"Config {self.price_per_15_minutes:,} تومان / ۱۵ دقیقه"

    def is_within_working_hours(self, when=None) -> bool:
        """True if ``when`` (or now) falls inside [open, close)."""
        if not (self.open_time and self.close_time):
            return True
        if when is None:
            t = timezone.localtime().time()
        else:
            t = when.time() if hasattr(when, "time") else when
        return self.open_time <= t < self.close_time

    _singleton_pk: int | None = None

    @classmethod
    def get_solo(cls) -> "PlayhouseConfig":
        """Return the single config row, creating it lazily if absent."""
        if cls._singleton_pk is not None:
            try:
                return cls.objects.get(pk=cls._singleton_pk)
            except cls.DoesNotExist:
                cls._singleton_pk = None
        row = cls.objects.order_by("created_at").first()
        if row is None:
            row = cls.objects.create()
        cls._singleton_pk = row.pk
        return row


class PlayhouseMember(DomainModel):
    """
    A child who entered the playhouse.

    `person` is set when the child already exists as an enrolled ``Person``;
    otherwise the operator-typed basics are kept here so this child becomes a
    trackable, re-enrollable playhouse member even without a full enrollment.
    """

    person = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="playhouse_sessions",
        help_text="لینک به دانش‌آموز / هویت موجود در سیستم (اختیاری)",
    )
    first_name = models.CharField(max_length=128, db_index=True)
    last_name = models.CharField(max_length=128, db_index=True)
    age = models.PositiveSmallIntegerField(null=True, blank=True, help_text="سن بچه (سال)")
    guardian_mobile = models.CharField(
        max_length=20,
        blank=True,
        default="",
        db_index=True,
        help_text="شماره تماس والدین",
    )
    guardian_name = models.CharField(max_length=128, blank=True, default="")
    notes = models.TextField(blank=True, default="")

    class Meta:
        app_label = "playhouse"
        db_table = "playhouse_member"
        verbose_name = "عضو خانه بازی"
        verbose_name_plural = "اعضای خانه بازی"
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("person",),
                name="uniq_playhouse_member_person",
                condition=models.Q(person__isnull=False),
                violation_error_message="این شخص قبلاً به عنوان عضو خانه بازی ثبت شده است.",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def display_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_linked(self) -> bool:
        return self.person_id is not None


class PlayhouseSession(DomainModel):
    """
    One timed visit. Entry starts the clock (manually), exit stops it; the
    billed duration is derived from the two timestamps and rounded to the
    nearest 15-minute block at invoice time.
    """

    class Status(models.TextChoices):
        WAITING = "waiting", "در انتظار ورود"
        ACTIVE = "active", "داخل خانه بازی"
        PAUSED = "paused", "متوقف شده"
        FINISHED = "finished", "پایان یافته"
        CANCELLED = "cancelled", "لغو شده"

    member = models.ForeignKey(
        PlayhouseMember,
        on_delete=models.PROTECT,
        related_name="sessions",
    )
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="playhouse_sessions",
        help_text="اپراتور ثبت‌کننده (به‌صورت خودکار از کاربر جاری)",
    )
    session_date = models.DateField(null=True, blank=True, db_index=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.WAITING,
        db_index=True,
    )

    # ─── تایمر ───
    entry_at = models.DateTimeField(null=True, blank=True, help_text="زمان شروع (دستی)")
    paused_at = models.DateTimeField(null=True, blank=True, help_text="زمان توقف موقت تایمر")
    paused_seconds = models.PositiveIntegerField(
        default=0,
        help_text="مجموع ثانیه‌های توقف که از زمان قابل محاسبه کم می‌شود",
    )
    exit_at = models.DateTimeField(null=True, blank=True, help_text="زمان پایان (دستی)")
    #: Processing lock: guards against two operators ending the same session
    #: concurrently (each operator works their own sheet, but belts-and-braces).
    ended_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ended_playhouse_sessions",
    )

    # ─── صورتحساب ───
    #: Billed minutes snapshot (rounded to 15) decided when the invoice is
    #: created; kept on the session for reporting even if the invoice is voided.
    billable_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        app_label = "playhouse"
        db_table = "playhouse_session"
        verbose_name = "نوبت خانه بازی"
        verbose_name_plural = "نوبت‌های خانه بازی"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("session_date", "status")),
        ]

    def __str__(self) -> str:
        return f"{self.member} {self.get_status_display()}"

    # ─── transitions (validated in services; kept thin here) ───
    @property
    def elapsed_seconds(self) -> int:
        """Wall-clock seconds since entry, excluding manual pauses."""
        if not self.entry_at:
            return 0
        end = self.exit_at or self.paused_at or timezone.now()
        gross = int((end - self.entry_at).total_seconds())
        return max(0, gross - int(self.paused_seconds or 0))

    @property
    def elapsed_minutes(self) -> int:
        return int(self.elapsed_seconds // 60)

    @property
    def is_running(self) -> bool:
        return self.status == self.Status.ACTIVE

    @property
    def duration_label(self) -> str:
        """Human label like ``2:15`` (hh:mm) from elapsed minutes."""
        minutes = self.elapsed_minutes
        return f"{minutes // 60}:{minutes % 60:02d}"

    @property
    def elapsed_label(self) -> str:
        """Exact live timer label like ``02:15:08``."""
        seconds = self.elapsed_seconds
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @property
    def billable_label(self) -> str:
        m = self.billable_minutes
        return f"{m // 60}:{m % 60:02d}"


class PlayhouseInvoiceItem(DomainModel):
    """A cafe (or extra) line item on a playhouse invoice."""

    invoice = models.ForeignKey(
        "playhouse.PlayhouseInvoice",
        on_delete=models.CASCADE,
        related_name="items",
    )
    name = models.CharField(max_length=200, help_text="نام آیتم کافه")
    price = models.DecimalField(max_digits=12, decimal_places=0, help_text="قیمت آیتم (تومان)")

    class Meta:
        app_label = "playhouse"
        db_table = "playhouse_invoice_item"
        verbose_name = "آیتم فاکتور"
        verbose_name_plural = "آیتم‌های فاکتور"
        ordering = ("created_at",)

    def __str__(self) -> str:
        return f"{self.name} ({self.price:,})"


class PlayhouseInvoiceSeq(models.Model):
    """
    Per-(year, day) counter backing concurrency-safe invoice numbers.

    The row is locked with ``select_for_update()`` by the service layer on
    PostgreSQL (production). The unique constraint on this (year, day) pair
    plus a bounded retry on ``PlayhouseInvoice.invoice_number`` guards the
    SQLite test backend.
    """

    year = models.PositiveIntegerField()
    day = models.PositiveIntegerField()  # 1..31
    last_value = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "playhouse"
        db_table = "playhouse_invoice_seq"
        constraints = [
            models.UniqueConstraint(
                fields=["year", "day"],
                name="uniq_playhouse_invoice_seq",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.year}/{self.day}={self.last_value}"


class PlayhouseInvoice(DomainModel):
    """Financial record for a finished playhouse session."""

    class PaymentMethod(models.TextChoices):
        POS = "pos", "دستگاه پوز"
        CARD_TRANSFER = "card_transfer", "کارت به کارت"

    session = models.OneToOneField(
        PlayhouseSession,
        on_delete=models.PROTECT,
        related_name="invoice",
    )
    member = models.ForeignKey(
        PlayhouseMember,
        on_delete=models.PROTECT,
        related_name="invoices",
    )
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="playhouse_invoices",
    )

    #: Snapshot so a later config price change can't rewrite history.
    price_per_15_minutes = models.DecimalField(
        max_digits=12, decimal_places=0, default=0
    )
    billed_minutes = models.PositiveIntegerField(default=0)
    time_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0)

    invoice_number = models.CharField(max_length=32, unique=True, blank=True, db_index=True)

    payment_method = models.CharField(
        max_length=16,
        choices=PaymentMethod.choices,
        blank=True,
        default="",
        help_text="روش پرداخت انتخاب‌شده",
    )
    tracking_code = models.CharField(
        max_length=64, blank=True, default="", help_text="کد رهگیری پوز / کارت به کارت"
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    is_paid = models.BooleanField(default=False, db_index=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        app_label = "playhouse"
        db_table = "playhouse_invoice"
        verbose_name = "فاکتور خانه بازی"
        verbose_name_plural = "فاکتورهای خانه بازی"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("is_paid", "created_at")),
        ]

    def __str__(self) -> str:
        return f"فاکتور {self.invoice_number} — {self.total_amount:,} تومان"

    @property
    def cafe_total(self) -> Decimal:
        return sum((i.price for i in self.items.all()), _fee_decimal(0))

    @property
    def total_amount(self) -> Decimal:
        return self.time_amount + self.cafe_total
