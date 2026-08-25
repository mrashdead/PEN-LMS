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
        PARENT = "parent", "والدین"

    # ─── هویت ───
    national_code = models.CharField(
        max_length=10,
        unique=True,
        db_index=True,
        help_text="کد ملی — شناسه یکتای شخص",
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
    person_type = models.CharField(
        max_length=32,
        choices=Type.choices,
        db_index=True,
    )

    # ─── مختص دانش‌آموز ───
    student_code = models.CharField(
        max_length=32,
        unique=True,
        null=True,
        blank=True,
        help_text="کد دانش‌آموزی (فقط برای student)",
    )

    # ─── مختص کارمند / معلم ───
    employee_code = models.CharField(
        max_length=32,
        unique=True,
        null=True,
        blank=True,
        help_text="کد پرسنلی (فقط برای employee/teacher)",
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

    def save(self, *args, **kwargs) -> None:
        self.national_code = (self.national_code or "").strip()
        self.first_name = (self.first_name or "").strip()
        self.last_name = (self.last_name or "").strip()
        self.mobile = (self.mobile or "").strip()
        super().save(*args, **kwargs)


class StudentParent(models.Model):
    """
    رابطهٔ والدین با فرزند (دانش‌آموز).
    هر دانش‌آموز می‌تواند چند والد داشته باشد و هر والد می‌تواند چند فرزند.
    """

    parent = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="parent_links",
        limit_choices_to={"person_type": Person.Type.PARENT},
    )
    student = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="parent_of",
        limit_choices_to={"person_type": Person.Type.STUDENT},
    )
    relation = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="نسبت: پدر، مادر، قیم، ...",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        app_label = "persons"
        db_table = "persons_student_parent"
        verbose_name = "Student-Parent relation"
        verbose_name_plural = "Student-Parent relations"
        constraints = [
            models.UniqueConstraint(
                fields=["parent", "student"],
                name="uniq_persons_student_parent",
            ),
        ]
        indexes = [
            models.Index(fields=["parent", "is_active"]),
            models.Index(fields=["student", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.parent} → {self.student} [{self.relation}]"

    @property
    def created_at_jalali(self) -> str:
        return persian_date(self.created_at)
