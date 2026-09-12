from __future__ import annotations

from datetime import time

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.core.models import DomainModel
from apps.core.utils import persian_numbers


class AcademicTerm(DomainModel):
    """
    سال / ترم / نیم‌سال تحصیلی.
    مثال: «پاییز ۱۴۰۴»، «نیم‌سال اول ۱۴۰۴-۱۴۰۵»، «تابستان ۱۴۰۴»
    """

    title = models.CharField(
        max_length=256,
        help_text="عنوان ترم — مثال: پاییز ۱۴۰۴",
    )
    start_date = models.DateField(
        help_text="تاریخ شروع ترم (شمسی در ورودی/خروجی)",
    )
    end_date = models.DateField(
        help_text="تاریخ پایان ترم",
    )
    is_current = models.BooleanField(
        default=False,
        db_index=True,
        help_text="آیا این ترم جاری است؟ (فقط یک ترم می‌تواند current=True باشد)",
    )
    is_active = models.BooleanField(default=True, db_index=True)
    note = models.TextField(blank=True, default="")

    class Meta:
        app_label = "academics"
        db_table = "academics_term"
        verbose_name = "Academic Term (ترم تحصیلی)"
        verbose_name_plural = "Academic Terms (ترم‌های تحصیلی)"
        ordering = ("-start_date",)
        permissions = [
            ("manage_term", "مدیریت ترم‌های تحصیلی"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_date__gte=models.F("start_date")),
                name="chk_academics_term_dates",
            ),
            models.UniqueConstraint(
                fields=["is_current"],
                condition=models.Q(is_current=True),
                name="uniq_academics_current_term",
            ),
        ]
        indexes = [
            models.Index(fields=["is_current", "is_active"]),
            models.Index(fields=["start_date", "end_date"]),
        ]

    def __str__(self) -> str:
        return self.title

    @property
    def display_title(self) -> str:
        return persian_numbers(self.title)

    @property
    def start_date_jalali(self) -> str:
        from apps.core.utils import persian_date
        return persian_date(self.start_date)

    @property
    def end_date_jalali(self) -> str:
        from apps.core.utils import persian_date
        return persian_date(self.end_date)

    def clean(self) -> None:
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError("تاریخ پایان باید بعد از تاریخ شروع باشد.")

    def save(self, *args, **kwargs) -> None:
        if self.is_current:
            AcademicTerm.objects.filter(is_current=True).exclude(pk=self.pk).update(
                is_current=False, updated_at=timezone.now()
            )
        super().save(*args, **kwargs)


class ClassGroup(DomainModel):
    """کلاس / گروه آموزشی در یک ترم مشخص."""

    class WEEK_DAYS:
        VALUES = {"شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"}

    term = models.ForeignKey(
        AcademicTerm,
        on_delete=models.CASCADE,
        related_name="class_groups",
        help_text="ترم تحصیلی",
    )
    code = models.SlugField(
        max_length=64,
        help_text="کد کلاس — مثال: MATH-101-A, 7A-1404",
    )
    name = models.CharField(
        max_length=256,
        help_text="نام کلاس — مثال: ریاضی ۱ — گروه A",
    )
    teacher = models.ForeignKey(
        "persons.Person",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teaching_class_groups",
        limit_choices_to={"person_type": "teacher"},
        help_text="معلم / مدرس کلاس",
    )
    room = models.CharField(
        max_length=128,
        blank=True,
        default="",
        help_text="محل برگزاری — مثال: کلاس ۲۰۱، سالن A",
    )
    capacity = models.PositiveIntegerField(
        default=0,
        help_text="ظرفیت کلاس (۰ = نامحدود)",
    )
    schedule = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            'زمان‌بندی هفتگی. مثال:\n'
            '{"days": ["شنبه", "دوشنبه"], "start_time": "08:00", "end_time": "09:30"}'
        ),
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        app_label = "academics"
        db_table = "academics_class_group"
        verbose_name = "Class Group (کلاس)"
        verbose_name_plural = "Class Groups (کلاس‌ها)"
        ordering = ("term", "code")
        permissions = [
            ("manage_class_group", "مدیریت کلاس‌ها"),
            ("view_all_class_groups", "مشاهده همه کلاس‌ها"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["term", "code"],
                condition=models.Q(is_deleted=False),
                name="uniq_academics_class_group_code_per_term_alive",
            ),
        ]
        indexes = [
            models.Index(fields=["term", "is_active"]),
            models.Index(fields=["teacher", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.term.title})"

    @property
    def display_name(self) -> str:
        return persian_numbers(self.name)

    @property
    def display_capacity(self) -> str:
        return persian_numbers(self.capacity) if self.capacity else "نامحدود"

    @property
    def enrollment_count(self) -> int:
        return self.enrollments.filter(is_active=True).count()

    @property
    def enrollment_count_display(self) -> str:
        return persian_numbers(self.enrollment_count)

    def clean(self) -> None:
        self.code = (self.code or "").strip().lower()
        if not isinstance(self.schedule, dict):
            raise ValidationError({"schedule": "زمان‌بندی باید یک شیء JSON باشد."})
        if not self.schedule:
            return

        errors: dict[str, str] = {}
        days = self.schedule.get("days")
        start_time = self.schedule.get("start_time")
        end_time = self.schedule.get("end_time")
        if not isinstance(days, list) or not days:
            errors["schedule"] = "فیلد days باید لیستی غیرخالی از روزهای هفته باشد."
        elif any(day not in self.WEEK_DAYS.VALUES for day in days):
            errors["schedule"] = "یکی از روزهای هفته در schedule نامعتبر است."
        if not isinstance(start_time, str) or not isinstance(end_time, str):
            errors["schedule"] = "start_time و end_time باید به صورت HH:MM باشند."
        else:
            try:
                start = time.fromisoformat(start_time)
                end = time.fromisoformat(end_time)
                if start >= end:
                    errors["schedule"] = "ساعت پایان باید بعد از ساعت شروع باشد."
            except ValueError:
                errors["schedule"] = "قالب ساعت باید HH:MM یا HH:MM:SS باشد."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs) -> None:
        self.code = (self.code or "").strip().lower()
        super().save(*args, **kwargs)


class ClassEnrollment(DomainModel):
    """ثبت‌نام / عضویت یک دانش‌آموز در یک کلاس."""

    class_group = models.ForeignKey(
        ClassGroup,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    student = models.ForeignKey(
        "persons.Person",
        on_delete=models.CASCADE,
        related_name="class_enrollments",
        limit_choices_to={"person_type": "student"},
        help_text="دانش‌آموز",
    )
    enrollment_date = models.DateField(
        default=timezone.localdate,
        help_text="تاریخ ثبت‌نام",
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        app_label = "academics"
        db_table = "academics_class_enrollment"
        verbose_name = "Class Enrollment (ثبت‌نام)"
        verbose_name_plural = "Class Enrollments (ثبت‌نام‌ها)"
        ordering = ("class_group", "student")
        permissions = [
            ("manage_enrollment", "مدیریت ثبت‌نام‌ها"),
        ]
        constraints = [
            # ثبت‌نام فقط در میان ردیف‌های «زنده» یکتاست؛ پس از حذف نرم یک
            # ثبت‌نام، ثبت مجدد همان دانش‌آموز نباید IntegrityError بدهد (B5).
            models.UniqueConstraint(
                fields=["class_group", "student"],
                condition=models.Q(is_deleted=False),
                name="uniq_academics_enrollment_alive",
            ),
        ]
        indexes = [
            models.Index(fields=["student", "is_active"]),
            models.Index(fields=["class_group", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.student} → {self.class_group.name}"

    @property
    def enrollment_date_jalali(self) -> str:
        from apps.core.utils import persian_date
        return persian_date(self.enrollment_date)