"""
Inbound call log domain — ثبت و پیگیری تماس‌های دریافتی موسسه.

Design rules (project architecture):

  * The caller is a free-form name+phone: a call may arrive from someone who
    is NOT yet a Person in the system (that is the whole point of the intake
    funnel). When the caller IS known, ``person`` links the identity instead
    of duplicating it — single source of truth.
  * ``receiver`` is the staff User who took the call; ``department`` is the
    org unit the call belongs to (education.Department when it maps, free
    text otherwise — same pattern as persons.StaffProfile).
  * Follow-up is first-class: ``follow_up_status`` + ``next_follow_up_at`` +
    ``assignee`` drive the "needs follow-up" report without parsing notes.
  * Status history is append-only (same pattern as staff.ReviewHistory).
"""
from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from apps.core.models import AppendOnlyDomainModel, DomainModel

_ALIVE = models.Q(is_deleted=False)

_PHONE_RE = RegexValidator(r"^[0-9+\-\s()]{3,20}$", "شماره تلفن معتبر نیست.")


class FollowUpStatus(models.TextChoices):
    NONE = "none", "بدون نیاز به پیگیری"
    PENDING = "pending", "نیازمند پیگیری"
    IN_PROGRESS = "in_progress", "در حال پیگیری"
    DONE = "done", "پیگیری شد"
    MISSED = "missed", "تماس مجدد ناموفق"


class CallResult(models.TextChoices):
    ANSWERED = "answered", "پاسخ داده شد"
    NO_ANSWER = "no_answer", "پاسخ داده نشد"
    BUSY = "busy", "اشغال"
    VOICEMAIL = "voicemail", "پیام صوتی"
    TRANSFERRED = "transferred", "ارجاع به بخش دیگر"
    FOLLOW_UP_AGREED = "follow_up_agreed", "قرار شد دوباره تماس گرفته شود"
    OTHER = "other", "سایر"


class CallSubject(DomainModel):
    """
    کاتالوگ موضوع‌های تماس — منبع حقیقتِ picklist.

    ``subject`` روی InboundCall متن آزاد می‌ماند (سرعت ثبت تماس)، اما این
    کاتالوگ گزینه‌های استاندارد را ارائه می‌کند و گزارش می‌تواند روی
    ``subject_code`` فیلتر کند تا توزیع موضوع‌ها پایدار بماند.
    """

    code = models.SlugField(max_length=64, db_index=True)
    name = models.CharField(max_length=128)
    department = models.CharField(max_length=128, blank=True, default="", db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        app_label = "calls"
        db_table = "calls_call_subject"
        verbose_name = "Call Subject (موضوع تماس)"
        verbose_name_plural = "Call Subjects (موضوع‌های تماس)"
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=["code"], condition=_ALIVE,
                name="uniq_calls_subject_code_alive",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        self.code = (self.code or "").strip().lower()


class InboundCall(DomainModel):
    """یک تماس دریافتی ثبت‌شده در موسسه."""

    class Direction(models.TextChoices):
        INBOUND = "inbound", "دریافتی"
        OUTBOUND = "outbound", "خروجی (پیگیری)"

    # ── تماس‌گیرنده ──────────────────────────────────────────────────────
    caller_name = models.CharField(
        max_length=256, blank=True, default="",
        help_text="نام تماس‌گیرنده (خالی = ناشناس).",
    )
    caller_phone = models.CharField(
        max_length=20, db_index=True, validators=[_PHONE_RE],
        help_text="شماره تماس گیرنده — پیش‌شماره و اعداد لاتین.",
    )
    person = models.ForeignKey(
        "persons.Person", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="inbound_calls",
        help_text="اگر تماس‌گیرنده شخص ثبت‌شده است، هویت اینجا وصل می‌شود (تکرار هویت ممنوع).",
    )
    # ── دریافت‌کننده ──────────────────────────────────────────────────────
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="received_calls", db_index=True,
    )
    department = models.CharField(max_length=128, blank=True, default="", db_index=True)
    department_ref = models.ForeignKey(
        "education.Department", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="inbound_calls",
        help_text="بخش مرتبط — وقتی به education.Department نگاشت می‌شود، گزارش یکپارچه است.",
    )
    # ── محتوا ─────────────────────────────────────────────────────────────
    direction = models.CharField(
        max_length=16, choices=Direction.choices, default=Direction.INBOUND, db_index=True,
    )
    called_at = models.DateTimeField(db_index=True, help_text="تاریخ و ساعت تماس")
    subject = models.CharField(
        max_length=256, db_index=True,
        help_text="موضوع تماس — متن کوتاه قابل فیلتر (مثلاً «استعلام شهریه»، «ثبت‌نام»، «غیبت»).",
    )
    description = models.TextField(blank=True, default="")
    result = models.CharField(
        max_length=24, choices=CallResult.choices, default=CallResult.ANSWERED, db_index=True,
    )
    # ── پیگیری ────────────────────────────────────────────────────────────
    follow_up_status = models.CharField(
        max_length=16, choices=FollowUpStatus.choices,
        default=FollowUpStatus.NONE, db_index=True,
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="assigned_call_followups", db_index=True,
        help_text="مسئول پیگیری (خالی = خود دریافت‌کننده).",
    )
    next_follow_up_at = models.DateTimeField(null=True, blank=True, db_index=True)
    follow_up_note = models.TextField(blank=True, default="")
    related_lead = models.ForeignKey(
        "leads.Lead", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="calls",
        help_text="اگر تماس به یک لید ارتباط دارد (قیف ورودی).",
    )
    subject_ref = models.ForeignKey(
        CallSubject, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="calls", db_index=True,
        help_text="موضوع استاندارد کاتالوگ — گزارش روی این کلید فیلتر می‌کند.",
    )

    class Meta:
        app_label = "calls"
        db_table = "calls_inbound_call"
        verbose_name = "Inbound Call (تماس دریافتی)"
        verbose_name_plural = "Inbound Calls (تماس‌های دریافتی)"
        ordering = ("-called_at",)
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(caller_phone=""),
                name="chk_calls_phone_required",
            ),
            models.CheckConstraint(
                condition=models.Q(next_follow_up_at__isnull=True)
                | models.Q(follow_up_status__in=["pending", "in_progress"]),
                name="chk_calls_followup_next_only_when_pending",
            ),
        ]
        indexes = [
            models.Index(fields=["called_at", "result"], name="calls_date_result_idx"),
            models.Index(fields=["receiver", "called_at"], name="calls_receiver_date_idx"),
            models.Index(fields=["follow_up_status", "next_follow_up_at"],
                         name="calls_followup_next_idx"),
            models.Index(fields=["subject", "called_at"], name="calls_subject_date_idx"),
            models.Index(fields=["department", "called_at"], name="calls_dept_date_idx"),
        ]

    def __str__(self) -> str:
        name = self.caller_name or "ناشناس"
        return f"{name} ({self.caller_phone}) → {self.subject}"

    @property
    def needs_follow_up(self) -> bool:
        return self.follow_up_status in {FollowUpStatus.PENDING, FollowUpStatus.IN_PROGRESS}

    @property
    def is_overdue_follow_up(self) -> bool:
        """Follow-up was promised but the window has passed."""
        return bool(
            self.needs_follow_up
            and self.next_follow_up_at
            and self.next_follow_up_at < timezone.now()
        )

    @property
    def caller_display(self) -> str:
        return self.caller_name.strip() or "ناشناس"

    def clean(self) -> None:
        if not (self.caller_phone or "").strip():
            raise ValidationError({"caller_phone": "شماره تماس الزامی است."})
        if self.assignee_id and self.assignee.is_active is False:
            raise ValidationError({"assignee": "کاربر انتخاب‌شده فعال نیست."})
        if self.next_follow_up_at and not self.needs_follow_up:
            raise ValidationError(
                {"next_follow_up_at": "تاریخ پیگیری فقط برای پیگیری‌های باز مجاز است."}
            )


class CallFollowUpLog(AppendOnlyDomainModel):
    """Append-only trail of follow-up attempts on one call."""

    call = models.ForeignKey(
        InboundCall, on_delete=models.CASCADE, related_name="follow_up_logs",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="call_follow_up_logs", db_index=True,
    )
    previous_status = models.CharField(max_length=16, choices=FollowUpStatus.choices)
    new_status = models.CharField(max_length=16, choices=FollowUpStatus.choices)
    note = models.TextField(blank=True, default="")
    next_follow_up_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "calls"
        db_table = "calls_follow_up_log"
        verbose_name = "Call Follow-up Log (تاریخچه پیگیری)"
        verbose_name_plural = "Call Follow-up Logs (تاریخچه‌های پیگیری)"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["call", "-created_at"], name="calls_log_call_created_idx"),
            models.Index(fields=["actor", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.call_id}: {self.previous_status}→{self.new_status}"


__all__ = [
    "CallFollowUpLog",
    "CallResult",
    "CallSubject",
    "FollowUpStatus",
    "InboundCall",
]
