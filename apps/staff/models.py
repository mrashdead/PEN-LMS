"""
Staff operations domain models — ساعت کاری، مرخصی و گزارش کاری.

Design rules (project architecture):

  * Identity lives in ``persons.Person`` / ``accounts.User`` — these tables
    hold ONLY the operational record, never duplicated name/code/contact
    columns (same rule as persons.StudentProfile vs Person).
  * Approval is modelled with the SAME primitives as the workflow engine
    (status machine + append-only history + role codes), but the records are
    first-class relational rows so the reporting layer can aggregate them in
    SQL instead of walking JSON payloads.
  * Timesheet + leave + work-report share one ``ApprovalStateMachine`` shape
    (pending → approved|rejected) with an append-only status history table —
    one audit pattern for all three, not three ad-hoc status columns.
  * Soft-delete + UUID PK come from ``DomainModel``.
"""
from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.db import models
from django.utils import timezone

from apps.core.models import AppendOnlyDomainModel, DomainModel

_ALIVE = models.Q(is_deleted=False)

#: Roles that may approve/reject other people's records. Mirrors the
#: ``IsManagerOrAdmin`` trio plus ``supervisor`` (direct-line supervisor),
#: which the org chart uses as the first-level approver.
APPROVER_ROLES = ("manager", "workflow_admin", "hr", "supervisor")


# ─────────────────────────────────────────────────────────────────────────────
# Shared status / history
# ─────────────────────────────────────────────────────────────────────────────

class ReviewStatus(models.TextChoices):
    PENDING = "pending", "در انتظار بررسی"
    APPROVED = "approved", "تأییدشده"
    REJECTED = "rejected", "ردشده"
    CANCELLED = "cancelled", "لغوشده"


class ReviewHistory(AppendOnlyDomainModel):
    """
    Append-only status trail shared by timesheet rows, leave requests and
    work reports — one audit pattern, one table. ``record_type`` +
    ``record_id`` are a typed polymorphic link (a GenericForeignKey would buy
    nothing here: the set of owner models is closed and small, and a typed
    FK per owner would triple the tables for the same information).
    """

    class RecordType(models.TextChoices):
        TIMESHEET = "timesheet", "ساعت کاری"
        LEAVE = "leave", "مرخصی"
        WORK_REPORT = "work_report", "گزارش کاری"

    record_type = models.CharField(
        max_length=16, choices=RecordType.choices, db_index=True,
    )
    record_id = models.UUIDField(db_index=True)
    from_status = models.CharField(
        max_length=16, choices=ReviewStatus.choices, default=ReviewStatus.PENDING,
    )
    to_status = models.CharField(max_length=16, choices=ReviewStatus.choices)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="staff_review_actions", db_index=True,
    )
    comment = models.TextField(blank=True, default="")
    rejection_reason = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        app_label = "staff"
        db_table = "staff_review_history"
        verbose_name = "Review History (تاریخچه بررسی)"
        verbose_name_plural = "Review Histories (تاریخچه‌های بررسی)"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["record_type", "record_id", "-created_at"],
                         name="staff_rev_record_created_idx"),
            models.Index(fields=["actor", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.record_type}:{self.record_id} {self.from_status}→{self.to_status}"


def _log_transition(*, record_type: str, record_id, from_status: str, to_status: str,
                    actor, comment: str = "", rejection_reason: str = "",
                    metadata: dict | None = None) -> ReviewHistory:
    """Single write path for every status change (service layer calls this)."""
    return ReviewHistory.objects.create(
        record_type=record_type,
        record_id=record_id,
        from_status=from_status,
        to_status=to_status,
        actor=actor,
        comment=(comment or "").strip(),
        rejection_reason=(rejection_reason or "").strip(),
        metadata=metadata or {},
    )


# ─────────────────────────────────────────────────────────────────────────────
# ۱) ساعت کاری (timesheet)
# ─────────────────────────────────────────────────────────────────────────────

class TimesheetEntry(DomainModel):
    """
    یک روز کاری یک کاربر — ورود/خروج و مدت کارکرد.

    یک ردیف در روز برای هر کاربر مجاز است (unique partial index) تا
    ثبت دوباره‌ی همان روز امکان‌پذیر بماند ولی دو ردیف باز هم‌زمان نباشد.
    ساعت‌ها در ستون‌های زمانی جداگانه ذخیره می‌شوند تا مدت کارکرد در SQL
    محاسبه شود (گزارش‌گیری در حجم بالا).
    """

    class Kind(models.TextChoices):
        REGULAR = "regular", "عادی"
        OVERTIME = "overtime", "اضافه‌کار"
        HOLIDAY = "holiday", "تعطیلی کارگاهی"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="timesheet_entries", db_index=True,
    )
    person = models.ForeignKey(
        "persons.Person", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="timesheet_entries",
        help_text="پروفایل اشخاص کارمند/مدرس — مثل سایر ماژول‌ها، هویت اینجا تکرار نمی‌شود.",
    )
    work_date = models.DateField(db_index=True, help_text="تاریخ کاری (شمسی در ورودی/خروجی)")
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.REGULAR, db_index=True)
    check_in = models.DateTimeField(db_index=True, help_text="زمان ورود")
    check_out = models.DateTimeField(null=True, blank=True, db_index=True, help_text="زمان خروج")
    # Optional manual override of the worked duration (minutes) — when the
    # clock-out is missing/inaccurate an approver may set the effective value;
    # NULL means "derive from check_in/check_out".
    override_minutes = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="اصلاح دستی مدت کارکرد (دقیقه) — خالی = محاسبه از ورود/خروج.",
    )
    note = models.CharField(max_length=500, blank=True, default="")
    status = models.CharField(
        max_length=16, choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING, db_index=True,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="reviewed_timesheets",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, default="")

    class Meta:
        app_label = "staff"
        db_table = "staff_timesheet_entry"
        verbose_name = "Timesheet Entry (ساعت کاری)"
        verbose_name_plural = "Timesheet Entries (ساعت‌های کاری)"
        ordering = ("-work_date", "-check_in")
        constraints = [
            # یک ردیفِ زنده به ازای هر (کاربر، تاریخ، نوع) — ثبت مجددِ همان
            # روز بعد از حذف نرم باید مجاز باشد (B5).
            models.UniqueConstraint(
                fields=["user", "work_date", "kind"],
                condition=_ALIVE,
                name="uniq_staff_timesheet_user_date_kind_alive",
                violation_error_message="برای این کاربر در این روز قبلاً ساعت کاری ثبت شده است.",
            ),
            models.CheckConstraint(
                condition=models.Q(check_out__isnull=True)
                | models.Q(check_out__gt=models.F("check_in")),
                name="chk_staff_timesheet_checkout_after_checkin",
            ),
        ]
        indexes = [
            models.Index(fields=["work_date", "status"], name="staff_ts_date_status_idx"),
            models.Index(fields=["user", "work_date"], name="staff_ts_user_date_idx"),
            models.Index(fields=["status", "work_date"], name="staff_ts_status_date_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.user} — {self.work_date} [{self.status}]"

    @property
    def duration_minutes(self) -> int | None:
        """Effective worked minutes: override wins, else check_in→check_out."""
        if self.override_minutes is not None:
            return self.override_minutes
        if self.check_in and self.check_out:
            delta = self.check_out - self.check_in
            return max(int(delta.total_seconds() // 60), 0)
        return None

    @property
    def duration_hours(self) -> float | None:
        minutes = self.duration_minutes
        return None if minutes is None else round(minutes / 60, 2)

    @property
    def is_open(self) -> bool:
        return self.check_out is None

    def clean(self) -> None:
        if self.check_in and self.check_out and self.check_out <= self.check_in:
            raise ValidationError({"check_out": "زمان خروج باید بعد از ورود باشد."})
        if self.work_date and self.work_date > timezone.localdate():
            raise ValidationError({"work_date": "تاریخ کاری نمی‌تواند در آینده باشد."})


# ─────────────────────────────────────────────────────────────────────────────
# ۲) مرخصی (leave)
# ─────────────────────────────────────────────────────────────────────────────

class LeaveType(DomainModel):
    """نوع مرخصی — منبع حقیقت قابل انتخاب، نه رشته‌ی آزاد."""

    class Accrual(models.TextChoices):
        UNLIMITED = "unlimited", "نامحدود"
        ANNUAL = "annual", "سالانه (استحقاقی)"
        SICK = "sick", "استعلاجی"
        UNPAID = "unpaid", "بدون حقوق"

    code = models.SlugField(max_length=64, db_index=True)
    name = models.CharField(max_length=128)
    accrual = models.CharField(
        max_length=16, choices=Accrual.choices, default=Accrual.UNLIMITED, db_index=True,
    )
    default_days = models.PositiveSmallIntegerField(default=0)
    requires_document = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        app_label = "staff"
        db_table = "staff_leave_type"
        verbose_name = "Leave Type (نوع مرخصی)"
        verbose_name_plural = "Leave Types (انواع مرخصی)"
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=["code"], condition=_ALIVE,
                name="uniq_staff_leave_type_code_alive",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        self.code = (self.code or "").strip().lower()


class LeaveRequest(DomainModel):
    """
    درخواست مرخصی کارمند — دامنه‌ی «سیستم مرخصی».

    یکپارچه با گردش‌کار: یک ``workflow.Instance`` اختیاری به رکورد وصل می‌شود
    (الگوی EntityWorkflow) تا مسیر تأیید چندسطحی قابل پیکربندی بماند. این
    ردیف همچنان منبع حقیقت گزارش‌گیری است و Instance فقط مسیر است.
    """

    class Unit(models.TextChoices):
        DAY = "day", "روز"
        HALF_DAY = "half_day", "نیم‌روز"
        HOUR = "hour", "ساعت"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="leave_requests", db_index=True,
    )
    person = models.ForeignKey(
        "persons.Person", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="leave_requests",
    )
    leave_type = models.ForeignKey(
        LeaveType, on_delete=models.PROTECT, related_name="requests", db_index=True,
    )
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)
    unit = models.CharField(max_length=16, choices=Unit.choices, default=Unit.DAY, db_index=True)
    # Duration in the chosen unit, denormalized at validation time so reports
    # aggregate a numeric column instead of recomputing per-row calendar math.
    duration = models.DecimalField(
        max_digits=7, decimal_places=2, default=0,
        validators=[MaxValueValidator(366)],
        help_text="مدت مرخصی بر حسب unit (پس از اعتبارسنجی محاسبه می‌شود).",
    )
    description = models.TextField(blank=True, default="")
    attachment = models.FileField(
        upload_to="staff/leave/", null=True, blank=True,
        help_text="مدرک مرخصی استعلاجی (در صورت نیاز).",
    )
    status = models.CharField(
        max_length=16, choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING, db_index=True,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="reviewed_leave_requests",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, default="")
    workflow_instance = models.ForeignKey(
        "workflow.Instance", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="leave_requests",
        help_text="مسیر گردش‌کار اختیاری (تأیید چندسطحی). گزارش از همین ردیف می‌خواند.",
    )

    class Meta:
        app_label = "staff"
        db_table = "staff_leave_request"
        verbose_name = "Leave Request (درخواست مرخصی)"
        verbose_name_plural = "Leave Requests (درخواست‌های مرخصی)"
        ordering = ("-start_date",)
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_date__gte=models.F("start_date")),
                name="chk_staff_leave_date_range",
            ),
            models.CheckConstraint(
                condition=models.Q(duration__gte=0),
                name="chk_staff_leave_duration_positive",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "status"], name="staff_lr_user_status_idx"),
            models.Index(fields=["start_date", "end_date"], name="staff_lr_range_idx"),
            models.Index(fields=["status", "start_date"], name="staff_lr_status_start_idx"),
            models.Index(fields=["leave_type", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} — {self.start_date}..{self.end_date} [{self.status}]"

    @property
    def is_pending(self) -> bool:
        return self.status == ReviewStatus.PENDING

    @property
    def is_approved(self) -> bool:
        return self.status == ReviewStatus.APPROVED

    @property
    def duration_display(self) -> str:
        unit_label = dict(self.Unit.choices).get(self.unit, self.unit)
        return f"{self.duration} {dict(self.Unit.choices).get(self.unit, unit_label)}"

    def overlaps(self, start, end) -> bool:
        """Does [start, end] intersect this request's date range?"""
        return bool(self.start_date and self.end_date and start and end) and (
            self.start_date <= end and start <= self.end_date
        )

    def clean(self) -> None:
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "تاریخ پایان باید بعد از شروع باشد."})
        if self.unit == self.Unit.HALF_DAY and self.start_date != self.end_date:
            raise ValidationError(
                {"unit": "مرخصی نیم‌روز فقط برای یک روز مجاز است."}
            )
        if self.leave_type_id and self.leave_type.requires_document and not self.attachment:
            raise ValidationError({"attachment": "این نوع مرخصی نیازمند مدرک است."})


# ─────────────────────────────────────────────────────────────────────────────
# ۳) گزارش کاری روزانه (daily work report)
# ─────────────────────────────────────────────────────────────────────────────

class WorkReport(DomainModel):
    """
    گزارش کاری روزانه‌ی یک کارمند — تاریخ، فعالیت، توضیحات، مدت زمان.

    مرتبط می‌تواند به یک پروژه/برگزاری/کلاس باشد (optional generic link در
    سطح سرویس؛ اینجا FK پایه کافی است چون گزارش «کاری» است نه آموزشی).
    وضعیت review با همان ماشین مشترک pending/approved/rejected پیش می‌رود.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="work_reports", db_index=True,
    )
    person = models.ForeignKey(
        "persons.Person", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="work_reports",
    )
    report_date = models.DateField(db_index=True)
    title = models.CharField(max_length=256, help_text="عنوان فعالیت اصلی روز")
    description = models.TextField(blank=True, default="", help_text="توضیحات فعالیت")
    spent_minutes = models.PositiveIntegerField(
        default=0, help_text="مدت زمان صرف‌شده (دقیقه)",
    )
    status = models.CharField(
        max_length=16, choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING, db_index=True,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="reviewed_work_reports",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, default="")
    # Optional link to the timesheet row of the same day (single source of
    # truth for hours: report says what was DONE, timesheet says how LONG).
    timesheet = models.ForeignKey(
        TimesheetEntry, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="work_reports",
    )

    class Meta:
        app_label = "staff"
        db_table = "staff_work_report"
        verbose_name = "Work Report (گزارش کاری)"
        verbose_name_plural = "Work Reports (گزارش‌های کاری)"
        ordering = ("-report_date",)
        constraints = [
            models.CheckConstraint(
                condition=models.Q(spent_minutes__lte=24 * 60),
                name="chk_staff_report_minutes_in_day",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "report_date"], name="staff_wr_user_date_idx"),
            models.Index(fields=["report_date", "status"], name="staff_wr_date_status_idx"),
            models.Index(fields=["status", "report_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} — {self.report_date}: {self.title}"

    @property
    def spent_hours(self) -> float:
        return round((self.spent_minutes or 0) / 60, 2)

    def clean(self) -> None:
        if self.report_date and self.report_date > timezone.localdate():
            raise ValidationError({"report_date": "تاریخ گزارش نمی‌تواند در آینده باشد."})
        if not (self.title or "").strip():
            raise ValidationError({"title": "عنوان فعالیت الزامی است."})


__all__ = [
    "APPROVER_ROLES",
    "LeaveRequest",
    "LeaveType",
    "ReviewHistory",
    "ReviewStatus",
    "TimesheetEntry",
    "WorkReport",
]
