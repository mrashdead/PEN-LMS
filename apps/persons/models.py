from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
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
        GUARDIAN = "guardian", "ولی / سرپرست (والدین)"

    # ─── هویت ───
    national_code = models.CharField(
        max_length=10,
        db_index=True,
        help_text="کد ملی — شناسه یکتای شخص (یکتا در میان اشخاص زنده)",
    )
    first_name = models.CharField(max_length=128, db_index=True)
    last_name = models.CharField(max_length=128, db_index=True)
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

        # کد ملی: فقط ارقام و دقیقاً ۱۰ رقم.
        if not self.national_code:
            errors.setdefault("national_code", []).append("کد ملی الزامی است.")
        elif not self.national_code.isdigit():
            errors.setdefault("national_code", []).append("کد ملی باید فقط شامل ارقام باشد.")
        elif len(self.national_code) != 10:
            errors.setdefault("national_code", []).append("کد ملی باید ۱۰ رقمی باشد.")

        # موبایل حساب اصلی: دقیقاً ۱۱ رقم و با 09 شروع می‌شود.
        if not self.mobile:
            errors.setdefault("mobile", []).append("شماره موبایل الزامی است.")
        elif not self.mobile.isdigit() or len(self.mobile) != 11 or not self.mobile.startswith("09"):
            errors.setdefault("mobile", []).append(
                "شماره موبایل باید دقیقاً ۱۱ رقم و با ۰۹ شروع شود."
            )

        if self.email:
            try:
                validate_email(self.email)
            except ValidationError:
                errors.setdefault("email", []).append("قالب ایمیل معتبر نیست.")

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


# ─────────────────────────────────────────────────────────────────────────────
# نقشه‌ی مفهومی خواسته‌شده → پیاده‌سازی موجود
#
# درخواست «تفکیک مدل‌های ساختار کاربر» به شکل:
#     UserProfile، StudentProfile، GuardianProfile، TeacherProfile، StaffProfile
#
# در این پایگاه‌داده ریشه‌ی هویت یک جدول است (``Person``) و «پروفایل» یعنی
# *تخصصی‌سازی* همان شخص. دو دلیل فنی برای افزودن جدول توسیعه (extension) به‌جای
# پنج جدول موازی:
#
#   ۱) کد ملی / موبایل / آدرس یک‌بار ذخیره می‌شوند. اگر TeacherProfile و
#      StaffProfile هر دو ستون‌های هویت داشته باشند، یک مدرسِ کارمند دو ردیف
#      هویتی با دو کد ملی پیدا می‌کند — همان چیزی که §13-1
#      (``PersonTypeAssignment``) رد کرد.
#   ۲) یگانگی «شخص» شرط همه‌ی foreign keyهای دامنه است (ClassSession.teacher،
#      ClassEnrollment.student، AttendanceRecord.student، Workflow subject).
#      چند جدول شخص یعنی هر کدام از این کلیدها باید one-of-N را هندل کند.
#
# پس: ``Person`` = ریشه‌ی هویت (+ نقش از ``accounts.UserRole``)؛ جداول پایین
# فیلدهای *اختصاصی* هر نقش را نگه می‌دارند، یکی‌به‌یک و اختیاری. هر داده‌ی
# تکراری (duplicates) در ``Person`` می‌ماند و این جدول‌ها «اعتباری‌سازی» را از
# «هویت» جدا می‌کنند.
# ─────────────────────────────────────────────────────────────────────────────

_ALIVE = models.Q(is_deleted=False)

RELATION_FATHER = "father"
RELATION_MOTHER = "mother"
RELATION_GUARDIAN = "legal_guardian"
RELATION_OTHER = "other"


class StudentProfile(DomainModel):
    """پروفایل دانش‌آموز — فیلدهای تحصیلی/انضباطی که جای их در ``Person`` نیست."""

    person = models.OneToOneField(
        Person,
        on_delete=models.CASCADE,
        related_name="student_profile",
        limit_choices_to={"person_type": Person.Type.STUDENT},
    )
    grade_level = models.CharField(
        max_length=32, blank=True, default="",
        help_text="پایه/پادگان تحصیلی (نمایشی؛ ساختار درختی در education.Department).",
    )
    father_first_name = models.CharField(max_length=128, blank=True, default="")
    father_last_name = models.CharField(max_length=128, blank=True, default="")
    father_phone = models.CharField(max_length=11, blank=True, default="")
    mother_first_name = models.CharField(max_length=128, blank=True, default="")
    mother_last_name = models.CharField(max_length=128, blank=True, default="")
    mother_phone = models.CharField(max_length=11, blank=True, default="")
    class_section = models.CharField(max_length=32, blank=True, default="", help_text="شعبه کلاس")
    school_year = models.CharField(max_length=16, blank=True, default="", help_text="سال تحصیلی، مثال 1405-1406")
    enrollment_date = models.DateField(null=True, blank=True)
    birth_certificate_no = models.CharField(max_length=32, blank=True, default="")
    health_notes = models.TextField(
        blank=True, default="",
        help_text="محدودیت/بیماری اعلام‌شده — PII پزشکی؛ فقط حافظان کامل می‌بینند.",
    )
    has_special_needs = models.BooleanField(default=False)
    is_custody_case = models.BooleanField(
        default=False,
        help_text="وضعیت تکفل: دانش‌آموز تحت تکفل والد غیراز ولایت/قیم خاص است.",
    )
    custody_note = models.CharField(max_length=256, blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        app_label = "persons"
        db_table = "persons_student_profile"
        verbose_name = "Student Profile (پروفایل دانش‌آموز)"
        verbose_name_plural = "Student Profiles (پروفایل‌های دانش‌آموز)"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["grade_level", "is_active"],
                         name="persons_stu_grade_active_idx"),
        ]

    def __str__(self) -> str:
        return f"StudentProfile({self.person})"


class GuardianProfile(DomainModel):
    """
    پروفایل ولی/سرپرست — «کدام والد» و «چه سطح اختیاری».

    نام/کدملی/تماس در ``Person`` است (تکرار هویت ممنوع). این جدول رابطه‌ی
    خانوادگی و اختیارات را نگه می‌دارد و به یک ``StudentProfile`` راه نمی‌بندد؛
    پیوند «این والد ← این دانش‌آموز» در ``StudentGuardian`` است تا یک والد
    بتواند سرپرست چند دانش‌آموز باشد و یک دانش‌آموز چند ولی داشته باشد.
    """

    class Relation(models.TextChoices):
        FATHER = RELATION_FATHER, "پدر"
        MOTHER = RELATION_MOTHER, "مادر"
        LEGAL_GUARDIAN = RELATION_GUARDIAN, "قیم / سرپرست قانونی"
        OTHER = RELATION_OTHER, "سایر"

    person = models.OneToOneField(
        Person,
        on_delete=models.CASCADE,
        related_name="guardian_profile",
        limit_choices_to={"person_type": Person.Type.GUARDIAN},
    )
    occupation = models.CharField(max_length=128, blank=True, default="")
    education_level = models.CharField(max_length=64, blank=True, default="")
    preferred_contact = models.CharField(
        max_length=20, blank=True, default="",
        help_text="کانال ترجیحی اطلاع‌رسانی: sms / call / in_app",
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="ولی اصلی — مخاطب رسمی مؤسسه برای اعلان‌ها و صورت‌حساب.",
    )

    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        app_label = "persons"
        db_table = "persons_guardian_profile"
        verbose_name = "Guardian Profile (پروفایل ولی)"
        verbose_name_plural = "Guardian Profiles (پروفایل اولیا)"
        ordering = ("-is_primary", "person__last_name")

    def __str__(self) -> str:
        return f"GuardianProfile({self.person})"


class StudentGuardian(DomainModel):
    """
    پیوند دانش‌آموز ↔ ولی با «وضعیت تکفل» و سطح اختیارات.

    ``relation`` نسبت *این* پیوند است (پدر/مادر/قیم) — پس یکPerson ولی می‌تواند
    برای دو دانش‌آموز دو نسبت متفاوت داشته باشد و بالعکس. ``custody_status``
    وضعیت حقوقی تکفل را ثبت می‌کند (تحت‌تکفل / ولایت پدر / قیم court-ordered).
    """

    class Custody(models.TextChoices):
        UNDER_CUSTODY = "under_custody", "تحت تکفل"
        CUSTODY_OTHER = "custody_other", "تکفل با والد دیگر"
        FULL_GUARDIAN = "full_guardian", "ولایت/سرپرستی کامل"
        VISITATION_ONLY = "visitation", "فقط ملاقات (بدون حق امضا)"

    student = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name="guardians",
        limit_choices_to={"person_type": Person.Type.STUDENT},
    )
    guardian = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name="ward_links",
        limit_choices_to={"person_type": Person.Type.GUARDIAN},
    )
    relation = models.CharField(
        max_length=32, choices=GuardianProfile.Relation.choices,
        default=GuardianProfile.Relation.OTHER,
    )
    custody_status = models.CharField(
        max_length=20, choices=Custody.choices, default=Custody.UNDER_CUSTODY,
    )
    # سطح اختیار: امضای درخواست، مشاهده‌ی نمره، دریافت اعلان مالی.
    can_view_grades = models.BooleanField(default=True)
    can_view_attendance = models.BooleanField(default=True)
    can_submit_requests = models.BooleanField(default=True)
    can_receive_billing = models.BooleanField(default=False)
    phone_override = models.CharField(
        max_length=20, blank=True, default="",
        help_text="شماره تماس این رابطه (اگر با Person.mobile متفاوت است).",
    )
    is_active = models.BooleanField(default=True, db_index=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)

    class Meta:
        app_label = "persons"
        db_table = "persons_student_guardian"
        verbose_name = "Student-Guardian link (تکفل)"
        verbose_name_plural = "Student-Guardian links (تکفلات)"
        ordering = ("student", "relation")
        constraints = [
            models.UniqueConstraint(
                fields=["student", "guardian"], condition=_ALIVE,
                name="uniq_persons_student_guardian_alive",
                violation_error_message="این ولی قبلاً به این دانش‌آموز متصل شده است.",
            ),
            models.CheckConstraint(
                condition=~models.Q(student=models.F("guardian")),
                name="chk_persons_guardian_not_self",
            ),
        ]
        indexes = [
            models.Index(fields=["guardian", "is_active"], name="persons_sg_guardian_active_idx"),
            models.Index(fields=["student", "is_active"], name="persons_sg_student_active_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.guardian} --{self.get_relation_display()}--> {self.student}"


class StaffProfile(DomainModel):
    """
    پروفایل کارمند/مدرس — قرارداد، تخصص، سوابق و مدارک.

    ``person_type`` معلم و کارمند هر دو در ``Person`` «کارمند-گونه» هستند
    (کد پرسنلی الزامی)، پس این جدول با یک ``kind`` تفکیک می‌کند و یک جدول
    موازیِ دوم برای «مدرس» نمی‌سازد؛ این دقیقاً همان الگویی است که
    ``PersonTypeAssignment`` برای شخصِ چند-نوع پذیرفته است.
    """

    class Kind(models.TextChoices):
        TEACHING = "teaching", "مدرس (تدریس)"
        ADMINISTRATIVE = "administrative", "کارمند اداری"
        TECHNICAL = "technical", "کارمند فنی"

    person = models.OneToOneField(
        Person,
        on_delete=models.CASCADE,
        related_name="staff_profile",
        limit_choices_to={
            "person_type__in": [Person.Type.TEACHER, Person.Type.EMPLOYEE]
        },
    )
    kind = models.CharField(
        max_length=20, choices=Kind.choices, default=Kind.ADMINISTRATIVE,
        db_index=True,
    )
    contract_no = models.CharField(max_length=64, blank=True, default="", db_index=True)
    contract_type = models.CharField(
        max_length=32, blank=True, default="",
        help_text="نوع قرارداد: رسمی / پیمانی / حق‌التدریس / پروژه‌ای",
    )
    contract_start = models.DateField(null=True, blank=True)
    contract_end = models.DateField(null=True, blank=True, db_index=True)
    hourly_rate = models.PositiveIntegerField(
        default=0, help_text="حق‌التدریس هر ساعت (تومان) — ۰ = نامشخص/پرداخت ماهانه"
    )
    weekly_max_hours = models.PositiveSmallIntegerField(
        default=0, help_text="سقف ساعات هفتگی تدریس — ورودی موتور زمان‌بندی"
    )
    specialization = models.CharField(
        max_length=256, blank=True, default="",
        help_text="تخصص/حوزه‌ی تدریس (متن آزاد؛ دپارتمان مرجع از education.Department)",
    )
    department = models.ForeignKey(
        "education.Department",
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name="staff",
    )
    academic_degree = models.CharField(max_length=64, blank=True, default="")
    experience_years = models.PositiveSmallIntegerField(default=0)
    bio = models.TextField(blank=True, default="", help_text="سوابق و رزومه (خلاصه).")
    credentials = models.JSONField(
        default=list, blank=True,
        help_text="مدارک/گواهینامه‌ها: [{title, issuer, issued_at, file}]",
    )
    is_verified = models.BooleanField(
        default=False, help_text="مدارک توسط امور اداری بررسی/تأیید شده است."
    )

    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        app_label = "persons"
        db_table = "persons_staff_profile"
        verbose_name = "Staff/Teacher Profile (پروفایل کارمند/مدرس)"
        verbose_name_plural = "Staff/Teacher Profiles (پروفایل کارمندان/مدرسان)"
        ordering = ("kind", "person__last_name")
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(contract_end__isnull=True)
                    | models.Q(contract_start__isnull=True)
                    | models.Q(contract_end__gt=models.F("contract_start"))
                ),
                name="chk_persons_contract_end_after_start",
            ),
        ]
        indexes = [
            models.Index(fields=["kind", "is_active"], name="persons_sp_kind_active_idx"),
            models.Index(fields=["department"], name="persons_sp_department_idx"),
        ]

    def __str__(self) -> str:
        return f"StaffProfile({self.person}, {self.get_kind_display()})"
