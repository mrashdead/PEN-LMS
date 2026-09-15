from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.core.models import DomainModel
from apps.core.utils import persian_date, persian_numbers


class Person(DomainModel):
    """
    هویت واقعی یک شخص — دانش‌آموز، معلم، کارمند، یا والدین.
    این فرم اصلی ثبت اطلاعات افراد است.
    """

    class Type(models.TextChoices):
        STUDENT = "student", "دانش‌آموز"
        TEACHER = "teacher", "معلم / مدرس"
        EMPLOYEE = "employee", "کارمند"

    # ─── هویت ───
    national_code = models.CharField(
        max_length=10,
        db_index=True,
        help_text="کد ملی — شناسه یکتای شخص (یکتا در میان اشخاص زنده)",
    )
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)
    father_name = models.CharField(max_length=128, blank=True, default="")
    birth_date = models.DateField(null=True, blank=True)

    class Gender(models.TextChoices):
        MALE = "male", "مرد"
        FEMALE = "female", "زن"
        NOT_SPECIFIED = "unspecified", "مشخص نشده"

    gender = models.CharField(
        max_length=16,
        choices=Gender.choices,
        default=Gender.NOT_SPECIFIED,
    )

    # ─── تماس ───
    mobile = models.CharField(max_length=20, db_index=True)
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=20, blank=True, default="", help_text="تلفن ثابت")
    address = models.TextField(blank=True, default="")
    postal_code = models.CharField(max_length=20, blank=True, default="")

    # ─── نوع ───
    # person_type is the PRIMARY type (backward compatible: admin pickers,
    # limit_choices_to, form relation filters). A person may hold ADDITIONAL
    # concurrent types via PersonTypeAssignment — e.g. teacher + employee in
    # ONE row (criterion §13-1). Always check `has_type()`/`type_codes()`
    # instead of person_type == X for business rules.
    person_type = models.CharField(
        max_length=32,
        choices=Type.choices,
        db_index=True,
    )

    # ─── مختص دانش‌آموز ───
    student_code = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        help_text="کد دانش‌آموزی (فقط برای student) — یکتا در میان اشخاص زنده",
    )

    # ─── مختص کارمند / معلم ───
    employee_code = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        help_text="کد پرسنلی (فقط برای employee/teacher) — یکتا در میان اشخاص زنده",
    )
    department = models.CharField(max_length=128, blank=True, default="")
    job_title = models.CharField(max_length=128, blank=True, default="")
    hire_date = models.DateField(null=True, blank=True)

    # ─── عکس ───
    photo = models.ImageField(
        upload_to="persons/photos/",
        null=True,
        blank=True,
    )

    # ─── وضعیت ───
    is_active = models.BooleanField(default=True, db_index=True)

    # ─── لینک به User (اختیاری — تا زمانی که مدیر دسترسی ندهد، null است) ───
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="person",
    )

    # ─── ثبّات ───
    registered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registered_persons",
    )

    class Meta:
        app_label = "persons"
        db_table = "persons_person"
        verbose_name = "Person (هویت)"
        verbose_name_plural = "Persons (اشخاص)"
        ordering = ("-created_at",)
        permissions = [
            ("view_person_detail", "مشاهده جزئیات کامل شخص"),
            ("view_person_list", "مشاهده لیست اشخاص"),
            ("create_user_for_person", "ساخت کاربر برای شخص"),
            ("view_grades_report", "مشاهده گزارش کارنامه"),
            ("view_attendance_report", "مشاهده گزارش حضورغیاب"),
            ("view_financial_report", "مشاهده گزارش مالی"),
        ]
        indexes = [
            models.Index(fields=["national_code"]),
            models.Index(fields=["person_type", "is_active"]),
            models.Index(fields=["last_name", "first_name"]),
            models.Index(fields=["mobile"]),
        ]
        constraints = [
            # کد ملی فقط در میان ردیف‌های «زنده» یکتاست؛ ردیف‌های حذف‌شده‌ی نرم
            # حق استفاده‌ی مجدد از کد ملی را از شخص جدید نمی‌گیرند (B5).
            models.UniqueConstraint(
                fields=["national_code"],
                condition=models.Q(is_deleted=False),
                name="uniq_persons_national_code_alive",
            ),
            models.UniqueConstraint(
                fields=["student_code"],
                condition=models.Q(is_deleted=False, student_code__isnull=False),
                name="uniq_persons_student_code_alive",
            ),
            models.UniqueConstraint(
                fields=["employee_code"],
                condition=models.Q(is_deleted=False, employee_code__isnull=False),
                name="uniq_persons_employee_code_alive",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} ({self.get_person_type_display()})"

    @property
    def birth_date_jalali(self) -> str:
        return persian_date(self.birth_date)

    @property
    def hire_date_jalali(self) -> str:
        return persian_date(self.hire_date)

    @property
    def display_name(self) -> str:
        return persian_numbers(f"{self.first_name} {self.last_name}")

    @property
    def display_national_code(self) -> str:
        return persian_numbers(self.national_code)

    @property
    def display_mobile(self) -> str:
        return persian_numbers(self.mobile)

    # ─── چند-نوعی (criterion §13-1) ────────────────────────────────────────
    def type_codes(self) -> set[str]:
        """
        همه‌ی نوع‌های فعلی شخص: نوع اصلی + انتساب‌های فعالِ زمانی.
        (اگر جدول انتساب هنوز ساخته نشده باشد فقط نوع اصلی برمی‌گردد.)
        """
        codes = {self.person_type} if self.person_type else set()
        try:
            now = timezone.now()
            codes |= set(
                self.type_assignments.filter(
                    is_active=True, is_deleted=False
                ).filter(
                    models.Q(valid_from__isnull=True) | models.Q(valid_from__lte=now)
                ).filter(
                    models.Q(valid_to__isnull=True) | models.Q(valid_to__gte=now)
                ).values_list("type", flat=True)
            )
        except Exception:  # table not yet migrated in this environment
            pass
        return codes

    def has_type(self, code: str) -> bool:
        return (code or "").strip().lower() in self.type_codes()

    @property
    def person_types_display(self) -> str:
        choices = dict(Person.Type.choices)
        return " / ".join(choices.get(c, c) for c in sorted(self.type_codes()))

    def is_teacher(self) -> bool:
        return self.has_type(Person.Type.TEACHER)

    def is_student(self) -> bool:
        return self.has_type(Person.Type.STUDENT)

    def is_employee(self) -> bool:
        return self.has_type(Person.Type.EMPLOYEE)

    def clean(self) -> None:
        errors: dict[str, list[str]] = {}

        # کد ملی: فقط ارقام
        if self.national_code:
            if not self.national_code.isdigit():
                errors.setdefault("national_code", []).append("کد ملی باید فقط شامل ارقام باشد.")
            if len(self.national_code) != 10:
                errors.setdefault("national_code", []).append("کد ملی باید ۱۰ رقمی باشد.")

        # اعتبارسنجی person_type
        if self.person_type == Person.Type.STUDENT and not self.student_code:
            errors.setdefault("student_code", []).append("برای دانش‌آموز کد دانش‌آموزی الزامی است.")

        if self.person_type in (Person.Type.EMPLOYEE, Person.Type.TEACHER):
            if not self.employee_code:
                errors.setdefault("employee_code", []).append("برای کارمند/معلم کد پرسنلی الزامی است.")

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.national_code = (self.national_code or "").strip()
        self.first_name = (self.first_name or "").strip()
        self.last_name = (self.last_name or "").strip()
        self.mobile = (self.mobile or "").strip()

        # فیلدهای یکتا و اختیاری باید به جای "" مقدار NULL بگیرند
        self.student_code = (self.student_code or "").strip() or None
        self.employee_code = (self.employee_code or "").strip() or None

        super().save(*args, **kwargs)


class PersonTypeAssignment(DomainModel):
    """
    انتساب نوع تخصصی زمان‌دار (criterion §13-1 / گزارش §4):

    یک Person می‌تواند هم‌زمان چند نوع داشته باشد (مثلاً مدرس + کارمند)
    بدون ساخت دو ردیف Person. نوع اصلی (person_type) سرجایش می‌ماند و
    سازگاری کامل با همه‌ی selectorهای موجود را حفظ می‌کند؛ این جدول
    نوع‌های *اضافی* و بازه‌ی اعتبارشان را نگه می‌دارد.
    """

    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="type_assignments",
    )
    type = models.CharField(
        max_length=32,
        choices=Person.Type.choices,
        db_index=True,
    )
    is_active = models.BooleanField(default=True, db_index=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_person_types",
    )

    class Meta:
        app_label = "persons"
        db_table = "persons_person_type_assignment"
        verbose_name = "Person Type Assignment (انتساب نوع)"
        verbose_name_plural = "Person Type Assignments (انتساب‌های نوع)"
        ordering = ("person", "type")
        constraints = [
            models.UniqueConstraint(
                fields=["person", "type"],
                condition=models.Q(is_deleted=False),
                name="uniq_persons_type_assignment_alive",
            ),
        ]
        indexes = [
            models.Index(fields=["person", "is_active"]),
            models.Index(fields=["type", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.person} [{self.type}]"
