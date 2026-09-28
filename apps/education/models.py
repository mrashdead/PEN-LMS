"""
Education domain models (B3 / B4).

Relational, typed tables for the parts of the school domain that must be
queryable, uniqueness-constrained and reportable — the analysis report (§5)
is explicit that these must NOT live only as form-submission JSON:

    Course ─┬─ CourseLesson ── Lesson
            └─ CourseOffering ── ClassSession ── AttendanceRecord
                                    │
    Department ─ Lesson/Course      └─ (teacher, location, date+time window)

Design notes honoring the migration report:
  * Every entity keeps ``legacy_id`` for traceability with the ASP system
    (§14.7 quality-over-UI; §11 phase notes).
  * Course and CourseOffering are DISTINCT (a course is the bundle; an
    offering is one concrete run) — §5.
  * Attendance is one row per (session, student) with a live-only UNIQUE
    constraint so a student cannot be recorded twice for the same session
    (§5 AttendanceRecord; fixes B4's cross-submission double-record).
  * Timetable conflict prevention (room / teacher / class overlap) is done
    with transaction + ``select_for_update`` logical lock in ``services`` —
    the report lists "range/exclusion constraint OR transaction + logical
    lock" as acceptable (§5, §7).
"""
from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from apps.core.models import DomainModel
from apps.core.utils import persian_numbers

_ALIVE = models.Q(is_deleted=False)

#: Business codes (OFFERING-1403-PY01, CLS-PY-01) keep the user's exact
#: casing — hence CharField+validator instead of SlugField's lowercase.
_BUSINESS_CODE_RE = RegexValidator(
    r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$",
    "کد باید با حرف یا رقم شروع شود و فقط شامل حروف لاتین، رقم، «-»، «_» یا «.» باشد.",
)


def next_sequential_code(model, prefix: str, field: str = "code") -> str:
    """
    Generate the next ``<prefix>-0001`` business code for ``model``.

    Scans ALL rows via ``_base_manager`` (including soft-deleted) so a retired
    code is never reused — codes are unique keys, not display-only. Zero-padded
    to 4 digits.
    """
    last = 0
    qs = model._base_manager.filter(**{f"{field}__startswith": f"{prefix}-"})
    for value in qs.values_list(field, flat=True):
        tail = str(value).split("-", 1)[-1]
        if tail.isdigit():
            last = max(last, int(tail))
    return f"{prefix}-{last + 1:04d}"


class Department(DomainModel):
    """واحد / گروه آموزشی — منبع حقیقت برای «دپارتمان»، نه رشته‌ی آزاد."""

    code = models.SlugField(max_length=64, db_index=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="children",
    )
    is_active = models.BooleanField(default=True, db_index=True)
    legacy_id = models.CharField(
        max_length=64, blank=True, default="", db_index=True,
        help_text="شناسه در سیستم قدیمی (ASP) برای مهاجرت و تطبیق.",
    )

    class Meta:
        app_label = "education"
        db_table = "education_department"
        verbose_name = "Department (واحد آموزشی)"
        verbose_name_plural = "Departments (واحدهای آموزشی)"
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=["code"], condition=_ALIVE,
                name="uniq_edu_department_code_alive",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        self.code = (self.code or "").strip().lower()


class Location(DomainModel):
    """فضای فیزیکی برگزاری — اتاق/سالن/آزمایشگاه (academics.Location was absent)."""

    name = models.CharField(max_length=200)
    code = models.SlugField(max_length=64, db_index=True, blank=True)
    building = models.CharField(max_length=200, blank=True, default="")
    capacity = models.PositiveIntegerField(default=0, help_text="۰ = نامحدود")
    equipment = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)
    legacy_id = models.CharField(max_length=64, blank=True, default="", db_index=True)

    class Meta:
        app_label = "education"
        db_table = "education_location"
        verbose_name = "Location (فضای آموزشی)"
        verbose_name_plural = "Locations (فضاهای آموزشی)"
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=["code"], condition=_ALIVE & ~models.Q(code=""),
                name="uniq_edu_location_code_alive",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        self.code = (self.code or "").strip().lower()


class Lesson(DomainModel):
    """درس با سرفصل و مشخصات — نسخه‌دار (§5: «سرفصل نسخه‌دار»)."""

    class SpaceType(models.TextChoices):
        UNSPECIFIED = "", "نامشخص"
        CLASSROOM = "classroom", "کلاس"
        LAB = "lab", "آزمایشگاه"
        WORKSHOP = "workshop", "کارگاه"
        ONLINE = "online", "آنلاین"
        HALL = "hall", "سالن"

    title = models.CharField(max_length=256, help_text="عنوان فارسی درس")
    title_en = models.CharField(max_length=256, blank=True, default="", help_text="عنوان انگلیسی درس")
    code = models.SlugField(max_length=64, db_index=True, help_text="کد درس — خودکار ls-0001")
    description = models.TextField(blank=True, default="")
    syllabus = models.TextField(blank=True, default="", help_text="سرفصل/مباحث")
    duration_hours = models.PositiveIntegerField(default=0)
    audience_age = models.CharField(
        max_length=32, blank=True, default="",
        help_text="محدوده سنی مخاطبان — مثال: 10-15")
    space_type = models.CharField(
        max_length=16, choices=SpaceType.choices, blank=True, default="",
        help_text="نوع فضای آموزشی پیشنهادی")
    department = models.ForeignKey(
        Department, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="lessons",
    )
    prerequisites = models.ManyToManyField(
        "self", symmetrical=False, blank=True, related_name="prerequisite_of"
    )
    required_equipment = models.TextField(blank=True, default="")
    learning_resources = models.TextField(blank=True, default="")
    tuition = models.PositiveIntegerField(default=0, help_text="شهریه به تومان")
    is_active = models.BooleanField(default=True, db_index=True)
    version = models.PositiveIntegerField(default=1)
    legacy_id = models.CharField(max_length=64, blank=True, default="", db_index=True)

    class Meta:
        app_label = "education"
        db_table = "education_lesson"
        verbose_name = "Lesson (درس)"
        verbose_name_plural = "Lessons (درس‌ها)"
        ordering = ("code",)
        constraints = [
            models.UniqueConstraint(
                fields=["code"], condition=_ALIVE,
                name="uniq_edu_lesson_code_alive",
            ),
        ]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not (self.code or "").strip():
            self.code = next_sequential_code(Lesson, "ls")
        super().save(*args, **kwargs)

    def clean(self) -> None:
        self.code = (self.code or "").strip().lower()
        if self.duration_hours and self.duration_hours > 1000:
            raise ValidationError({"duration_hours": "ساعات تدریس غیرمنطقی است."})


class Course(DomainModel):
    """دوره = بسته‌ی آموزشیِ متصل به درس‌ها (نه خودِ برگزاری)."""

    title = models.CharField(max_length=256)
    code = models.SlugField(max_length=64, db_index=True, help_text="کد دوره — خودکار cs-0001")
    description = models.TextField(blank=True, default="")
    objectives = models.TextField(blank=True, default="")
    tuition = models.PositiveIntegerField(default=0, help_text="شهریه دوره به تومان")
    department = models.ForeignKey(
        Department, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="courses",
    )
    lessons = models.ManyToManyField(
        Lesson, through="CourseLesson", related_name="courses", blank=True
    )
    is_active = models.BooleanField(default=True, db_index=True)
    legacy_id = models.CharField(max_length=64, blank=True, default="", db_index=True)

    class Meta:
        app_label = "education"
        db_table = "education_course"
        verbose_name = "Course (دوره)"
        verbose_name_plural = "Courses (دوره‌ها)"
        ordering = ("code",)
        constraints = [
            models.UniqueConstraint(
                fields=["code"], condition=_ALIVE,
                name="uniq_edu_course_code_alive",
            ),
        ]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        # Keep the public course code consistent with Lesson/Offering: the
        # API and the workspace intentionally allow the field to be omitted.
        # An empty string is still subject to the partial unique constraint,
        # so generate the business key before the INSERT happens.
        if not (self.code or "").strip():
            self.code = next_sequential_code(Course, "cs")
        super().save(*args, **kwargs)

    def clean(self) -> None:
        self.code = (self.code or "").strip().lower()


class CourseLesson(DomainModel):
    """اتصال ترتیب‌دار دوره↔درس — ترتیب، اجباری‌بودن و ساعت را حفظ می‌کند (§5)."""

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="course_lessons"
    )
    lesson = models.ForeignKey(
        Lesson, on_delete=models.PROTECT, related_name="course_links"
    )
    order = models.PositiveSmallIntegerField(default=1)
    required = models.BooleanField(default=True)
    hours = models.PositiveIntegerField(default=0)

    class Meta:
        app_label = "education"
        db_table = "education_course_lesson"
        verbose_name = "Course Lesson (درس دوره)"
        verbose_name_plural = "Course Lessons (درس‌های دوره)"
        ordering = ("course", "order")
        constraints = [
            models.UniqueConstraint(
                fields=["course", "lesson"], condition=_ALIVE,
                name="uniq_edu_course_lesson_alive",
            ),
            models.UniqueConstraint(
                fields=["course", "order"], condition=_ALIVE,
                name="uniq_edu_course_lesson_order_alive",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.course_id}/{self.lesson_id}#{self.order}"


class CourseOffering(DomainModel):
    """برگزاری مشخص یک دوره: ظرفیت، بازه، محل، مدرس، وضعیت ثبت‌نام (§5)."""

    class Status(models.TextChoices):
        DRAFT = "draft", "پیش‌نویس"
        OPEN = "open", "باز (ثبت‌نام)"
        CLOSED = "closed", "بسته"
        RUNNING = "running", "در حال برگزاری"
        FINISHED = "finished", "پایان‌یافته"
        CANCELLED = "cancelled", "لغوشده"

    course = models.ForeignKey(
        Course, on_delete=models.PROTECT, related_name="offerings"
    )
    title = models.CharField(max_length=256, blank=True, default="")
    code = models.CharField(
        max_length=64, blank=True, default="",
        validators=[_BUSINESS_CODE_RE],
        help_text="عنوان/کد برگزاری — یکتا. مثال: OFFERING-1403-PY01؛ "
                  "اگر خالی بماند به‌صورت خودکار of-0001 ساخته می‌شود.",
    )
    department = models.ForeignKey(
        Department, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="offerings",
    )
    capacity = models.PositiveIntegerField(default=0, help_text="۰ = نامحدود")
    enrolled_count = models.PositiveIntegerField(default=0)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    location = models.ForeignKey(
        Location, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="offerings",
    )
    instructor = models.ForeignKey(
        "persons.Person", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="offered_courses", limit_choices_to={"person_type": "teacher"},
    )
    schedule = models.JSONField(
        default=dict, blank=True,
        help_text="زمان برگزاری پیشنهادی: {days: [\"sat\",\"wed\"], start: \"18:00\", end: \"20:00\"}",
    )
    total_sessions = models.PositiveSmallIntegerField(
        default=0,
        help_text="تعداد کل جلسات دوره (فرم تشکیل کلاس) — ۰ = توزیع بر اساس ساعات تدریس.",
    )
    auto_skip_holidays = models.BooleanField(
        default=True,
        help_text="در تولید خودکار، روزهای تعطیل رسمی/جمعه‌ها حذف می‌شوند.",
    )
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.DRAFT, db_index=True
    )
    tuition = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)
    legacy_id = models.CharField(max_length=64, blank=True, default="", db_index=True)

    class Meta:
        app_label = "education"
        db_table = "education_course_offering"
        verbose_name = "Course Offering (برگزاری دوره)"
        verbose_name_plural = "Course Offerings (برگزاری‌های دوره)"
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["code"], condition=_ALIVE & ~models.Q(code=""),
                name="uniq_edu_offering_code_alive",
            ),
            models.CheckConstraint(
                condition=models.Q(end_date__isnull=True)
                | models.Q(start_date__isnull=True)
                | models.Q(end_date__gte=models.F("start_date")),
                name="chk_edu_offering_dates",
            ),
            models.CheckConstraint(
                condition=models.Q(enrolled_count__lte=models.F("capacity"))
                | models.Q(capacity=0),
                name="chk_edu_offering_capacity",
            ),
        ]
        indexes = [
            models.Index(fields=["course", "status"]),
        ]

    def __str__(self) -> str:
        return self.code or self.title or f"{self.course} ({self.start_date})"

    def save(self, *args, **kwargs):
        # Offering code is a unique business key like lesson/course codes:
        # auto-filled (of-0001) when the form leaves it empty, never reused
        # after a soft delete (next_sequential_code scans _base_manager).
        if not (self.code or "").strip():
            self.code = next_sequential_code(CourseOffering, "of")
        super().save(*args, **kwargs)

    def clean(self) -> None:
        self.code = (self.code or "").strip()

    @property
    def lesson_links(self):
        """CourseLesson rows of this offering's course, in curriculum order."""
        return (
            self.course.course_lessons.filter(is_deleted=False)
            .select_related("lesson")
            .order_by("order")
        )

    @property
    def teaching_minutes(self) -> int:
        """Total scheduled teaching time of the offering, in minutes.

        Per-lesson hours come from the CourseLesson row when it carries one
        (the curriculum may override the lesson's own duration), otherwise
        from the lesson itself. Used by the class-formation engine to derive
        the session count (تعداد جلسات = مدت ÷ طول جلسه).
        """
        total = 0
        for link in self.lesson_links:
            total += (link.hours or (link.lesson.duration_hours if link.lesson_id else 0) or 0) * 60
        return total

    @property
    def seats_left(self) -> int | None:
        return None if not self.capacity else max(self.capacity - self.enrolled_count, 0)

    @property
    def seats_left_display(self) -> str:
        left = self.seats_left
        return "نامحدود" if left is None else persian_numbers(left)


class ClassSession(DomainModel):
    """یک جلسه‌ی واقعی و قطعی از یک درس/کلاس (§5: «گزارش روزانه از Meeting واقعی»)."""

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "برنامه‌ریزی‌شده"
        HELD = "held", "برگزارشده"
        CANCELLED = "cancelled", "لغوشده"

    # A session belongs EITHER to a course offering (course-run world) OR to a
    # plain academics class group (attendance-form world) — at least one must
    # be set (chk_edu_session_target). This lets the attendance form project
    # into real, uniqueness-protected sessions without inventing an offering.
    offering = models.ForeignKey(
        CourseOffering, null=True, blank=True, on_delete=models.CASCADE,
        related_name="sessions",
    )
    class_group = models.ForeignKey(
        "academics.ClassGroup", null=True, blank=True, on_delete=models.CASCADE,
        related_name="class_sessions",
        help_text="پل بین جلسه‌ی واقعی و گروه کلاسی academics (گزارش روزانه / فرم حضور)",
    )
    lesson = models.ForeignKey(
        Lesson, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="sessions",
    )
    # کد قطعی کلاس (فرم «تشکیل کلاس») — جلساتِ یک درسِ همان برگزاری یک کد
    # مشترک دارند؛ شماره‌گذاری جلسات در هر کدِ کلاس مستقل است (۱..N).
    class_code = models.CharField(
        max_length=64, blank=True, default="",
        validators=[_BUSINESS_CODE_RE],
        help_text="کد کلاس — مثال CLS-PY-01 (خالی = جلسات قدیمی/بدون کلاس)",
    )
    session_number = models.PositiveSmallIntegerField(default=1)
    title = models.CharField(max_length=256, blank=True, default="")
    topic = models.CharField(
        max_length=500, blank=True, default="",
        help_text="موضوع درس این جلسه — برای برنامه‌ریزی مدرس و مشاهدهٔ دانش‌آموز.",
    )
    session_date = models.DateField(db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    teacher = models.ForeignKey(
        "persons.Person", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="taught_sessions", limit_choices_to={"person_type": "teacher"},
    )
    location = models.ForeignKey(
        Location, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="sessions",
    )
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.SCHEDULED, db_index=True
    )
    legacy_id = models.CharField(max_length=64, blank=True, default="", db_index=True)

    class Meta:
        app_label = "education"
        db_table = "education_class_session"
        verbose_name = "Class Session (جلسه)"
        verbose_name_plural = "Class Sessions (جلسات)"
        ordering = ("session_date", "start_time")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_time__gt=models.F("start_time")),
                name="chk_edu_session_time_window",
            ),
            models.CheckConstraint(
                condition=models.Q(offering__isnull=False)
                | models.Q(class_group__isnull=False),
                name="chk_edu_session_target",
            ),
            # یک شماره جلسه در هر «کلاس» از یک برگزاری، یکتا در میان جلسات
            # زنده (§5 + فرم تشکیل کلاس). class_code خالی = رفتار قبلی
            # (شماره‌گذاری سراسری در برگزاری). جلسه‌های بدون offering
            # (پل فرم حضور/ClassGroup) با NULL مجازند.
            models.UniqueConstraint(
                fields=["offering", "class_code", "session_number"],
                condition=_ALIVE & models.Q(offering__isnull=False),
                name="uniq_edu_session_class_number_alive",
            ),
            # جلسه‌ی بر‌پایه‌ی ClassGroup (فرم حضور): یک (کلاس، تاریخ، شماره)
            # فقط یک جلسه‌ی واقعی — کلید استخراج‌شدنِ فرم حضور (B4).
            models.UniqueConstraint(
                fields=["class_group", "session_date", "session_number"],
                condition=_ALIVE & models.Q(class_group__isnull=False),
                name="uniq_edu_session_group_date_number_alive",
            ),
        ]
        indexes = [
            models.Index(fields=["session_date", "status"]),
            models.Index(fields=["teacher", "session_date"]),
            models.Index(fields=["location", "session_date"]),
            models.Index(fields=["class_group", "session_date"]),
        ]

    def __str__(self) -> str:
        return f"جلسه {self.session_number} — {self.session_date}"

    def clean(self) -> None:
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError({"end_time": "ساعت پایان باید بعد از شروع باشد."})


class SessionScheduleRevision(DomainModel):
    """Audit trail for schedule changes visible to learners and guardians."""

    session = models.ForeignKey(
        ClassSession, on_delete=models.CASCADE, related_name="schedule_revisions"
    )
    version = models.PositiveIntegerField(default=1)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="session_schedule_changes",
    )
    before = models.JSONField(default=dict, blank=True)
    after = models.JSONField(default=dict, blank=True)
    reason = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        app_label = "education"
        db_table = "education_session_schedule_revision"
        ordering = ("-version", "-created_at")
        constraints = [
            models.UniqueConstraint(
                fields=["session", "version"], condition=_ALIVE,
                name="uniq_edu_session_schedule_revision_alive",
            ),
        ]
        indexes = [
            models.Index(fields=["session", "-version"]),
        ]


class SessionMaterial(DomainModel):
    """A link or uploaded learning attachment belonging to one session."""

    class Kind(models.TextChoices):
        LINK = "link", "پیوند آموزشی"
        FILE = "file", "فایل"
        VIDEO = "video", "ویدئو"

    session = models.ForeignKey(
        ClassSession, on_delete=models.CASCADE, related_name="materials"
    )
    title = models.CharField(max_length=256)
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.LINK)
    url = models.URLField(blank=True, default="")
    file = models.FileField(
        upload_to="education/session-materials/", null=True, blank=True
    )
    sort_order = models.PositiveSmallIntegerField(default=1)
    is_visible = models.BooleanField(default=True, db_index=True)

    class Meta:
        app_label = "education"
        db_table = "education_session_material"
        ordering = ("sort_order", "created_at")
        indexes = [
            models.Index(fields=["session", "is_visible"]),
        ]

    def clean(self) -> None:
        if not (self.url or self.file):
            raise ValidationError("برای ضمیمه، پیوند یا فایل را وارد کنید.")

    @property
    def public_url(self) -> str:
        if self.url:
            return self.url
        try:
            return self.file.url if self.file else ""
        except ValueError:
            return ""


class AttendanceRecord(DomainModel):
    """حضور و غیاب هر دانش‌آموز در هر جلسه (§5؛ رفع دو‌ثبتی B4)."""

    class Status(models.TextChoices):
        PRESENT = "present", "حاضر"
        ABSENT = "absent", "غایب"
        LATE = "late", "تأخیر"
        EXCUSED = "excused", "موجه"

    session = models.ForeignKey(
        ClassSession, on_delete=models.CASCADE, related_name="attendances"
    )
    student = models.ForeignKey(
        "persons.Person", on_delete=models.CASCADE, related_name="attendance_records",
        limit_choices_to={"person_type": "student"},
    )
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PRESENT, db_index=True
    )
    note = models.CharField(max_length=500, blank=True, default="")
    recorded_by = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="recorded_attendances",
    )

    class Meta:
        app_label = "education"
        db_table = "education_attendance_record"
        verbose_name = "Attendance Record (حضور)"
        verbose_name_plural = "Attendance Records (حضور و غیاب)"
        ordering = ("session", "student")
        constraints = [
            # ستون فقرات رفع B4: یک شخص حداکثر یک رکورد حضور در هر جلسه.
            models.UniqueConstraint(
                fields=["session", "student"], condition=_ALIVE,
                name="uniq_edu_attendance_session_student_alive",
                violation_error_message="حضور این دانش‌آموز برای این جلسه قبلاً ثبت شده است.",
            ),
        ]
        indexes = [
            models.Index(fields=["student", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.student} → جلسه {self.session_id} [{self.status}]"


class GradeRecord(DomainModel):
    """ارزیابی توصیفی (قبول/مردود) با یادداشت اجباری مدرس (§5 «نمره توصیفی»)."""

    class Result(models.TextChoices):
        PASSED = "passed", "قبول"
        FAILED = "failed", "مردود"

    student = models.ForeignKey(
        "persons.Person", on_delete=models.CASCADE, related_name="grade_records",
        limit_choices_to={"person_type": "student"},
    )
    # grade may be attached either to a concrete session or to the whole
    # offering (final evaluation) — both are permitted, one must be present.
    session = models.ForeignKey(
        ClassSession, null=True, blank=True, on_delete=models.CASCADE,
        related_name="grades",
    )
    offering = models.ForeignKey(
        CourseOffering, null=True, blank=True, on_delete=models.CASCADE,
        related_name="grades",
    )
    lesson = models.ForeignKey(
        Lesson, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="grades",
    )
    result = models.CharField(
        max_length=16, choices=Result.choices, default=Result.PASSED, db_index=True
    )
    teacher_note = models.CharField(
        max_length=1000, help_text="یادداشت توصیفی مدرس — برای مردود اجباری است."
    )
    evaluated_by = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="evaluated_grades",
    )

    class Meta:
        app_label = "education"
        db_table = "education_grade_record"
        verbose_name = "Grade Record (ارزیابی)"
        verbose_name_plural = "Grade Records (ارزیابی‌ها)"
        ordering = ("-created_at",)
        constraints = [
            models.CheckConstraint(
                condition=models.Q(session__isnull=False) | models.Q(offering__isnull=False),
                name="chk_edu_grade_has_target",
            ),
            models.UniqueConstraint(
                fields=["student", "session", "lesson"], condition=_ALIVE,
                name="uniq_edu_grade_session_alive",
            ),
            models.UniqueConstraint(
                fields=["student", "offering"], condition=_ALIVE & models.Q(session__isnull=True),
                name="uniq_edu_grade_offering_final_alive",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.student} [{self.result}]"

    def clean(self) -> None:
        # §5: «علت قبول‌نشدن باید اجباری و قابل audit باشد».
        if self.result == self.Result.FAILED and not (self.teacher_note or "").strip():
            raise ValidationError(
                {"teacher_note": "برای نتیجه‌ی مردود، یادداشت مدرس الزامی است."}
            )


class OfferingEnrollment(DomainModel):
    """
    ثبت‌نام مالی یک دانش‌آموز در یک برگزاری — مبلغ/تخفیف/پرداخت.

    جدا از academics.ClassEnrollment (که فقط عضویت کلاس است): این جدول
    «تراکنش ثبت‌نام» است — مبلغ دوره، نوع و مقدار تخفیف، مبلغ نهایی، روش
    پرداخت (نقدی/پوز/چک) و جزئیات چک‌ها. مبالغ به تومان (عدد صحیح) ذخیره
    می‌شوند؛ جداکنندهٔ سه‌رقمی فقط نمایشی است.
    """

    class PaymentMethod(models.TextChoices):
        CASH = "cash", "نقدی"
        POS = "pos", "کارت‌خوان (POS)"
        CHEQUE = "cheque", "چک"

    class DiscountType(models.TextChoices):
        NONE = "none", "بدون تخفیف"
        PERCENT = "percent", "درصدی"
        AMOUNT = "amount", "مبلغ ثابت"

    class LifecycleStatus(models.TextChoices):
        PENDING = "pending", "در انتظار تأیید"
        CONFIRMED = "confirmed", "تأییدشده"
        CANCELLED = "cancelled", "لغوشده"
        PARTIALLY_REFUNDED = "partially_refunded", "عودت جزئی"
        REFUNDED = "refunded", "عودت کامل"

    offering = models.ForeignKey(
        CourseOffering, on_delete=models.PROTECT, related_name="enrollments"
    )
    student = models.ForeignKey(
        "persons.Person", on_delete=models.PROTECT, related_name="offerings_enrolled",
        limit_choices_to={"person_type": "student"},
    )
    # Snapshot of the offering's tuition at enroll time (course bundle price).
    course_amount = models.PositiveIntegerField(default=0, help_text="مبلغ دوره (تومان)")
    discount_type = models.CharField(
        max_length=10, choices=DiscountType.choices, default=DiscountType.NONE
    )
    discount_value = models.PositiveIntegerField(
        default=0, help_text="درصد (۰..۱۰۰) یا مبلغ تومان، بسته به نوع"
    )
    final_amount = models.PositiveIntegerField(
        default=0, help_text="مبلغ قابل‌پرداخت پس از تخفیف (تومان)"
    )
    payment_method = models.CharField(
        max_length=10, choices=PaymentMethod.choices, default=PaymentMethod.CASH
    )
    # Cheque details (only meaningful when payment_method == cheque).
    cheque_count = models.PositiveSmallIntegerField(default=0)
    cheques = models.JSONField(
        default=list, blank=True,
        help_text="فهرست چک‌ها: [{amount, payee, due_date, tracking_no}]",
    )
    reference = models.CharField(
        max_length=128, blank=True, default="",
        help_text="کد پیگیری/رسید پرداخت (نقدی/پوز).",
    )
    enrolled_at = models.DateField(default=timezone.localdate)
    is_active = models.BooleanField(default=True, db_index=True)
    lifecycle_status = models.CharField(
        max_length=24,
        choices=LifecycleStatus.choices,
        default=LifecycleStatus.CONFIRMED,
        db_index=True,
        help_text="وضعیت چرخهٔ ثبت‌نام مستقل از وضعیت عضویت نهایی در کلاس.",
    )
    final_class_enrollment = models.OneToOneField(
        "academics.ClassEnrollment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="source_offering_enrollment",
        help_text="عضویت قطعی در کلاس که پس از تشکیل کلاس ایجاد می‌شود.",
    )

    class Meta:
        app_label = "education"
        db_table = "education_offering_enrollment"
        verbose_name = "Offering Enrollment (ثبت‌نام)"
        verbose_name_plural = "Offering Enrollments (ثبت‌نام‌ها)"
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["offering", "student"], condition=_ALIVE,
                name="uniq_edu_offering_enrollment_alive",
                violation_error_message="این دانش‌آموز قبلاً در این برگزاری ثبت‌نام کرده است.",
            ),
        ]
        indexes = [
            models.Index(fields=["student", "is_active"]),
            models.Index(fields=["offering", "is_active"]),
            models.Index(fields=["offering", "enrolled_at"], name="edu_enroll_report_idx",
                         condition=models.Q(is_active=True, is_deleted=False)),
        ]

    def __str__(self) -> str:
        return f"{self.student} → {self.offering_id} [{self.final_amount}]"

    def compute_final(self) -> int:
        """Derive final_amount from course_amount + discount (single rule)."""
        base = self.course_amount or 0
        if self.discount_type == self.DiscountType.PERCENT:
            pct = max(0, min(int(self.discount_value or 0), 100))
            return base - int(round(base * pct / 100))
        if self.discount_type == self.DiscountType.AMOUNT:
            return max(base - int(self.discount_value or 0), 0)
        return base

    def clean(self) -> None:
        if self.final_class_enrollment_id:
            membership = self.final_class_enrollment
            if membership.student_id != self.student_id:
                raise ValidationError({"final_class_enrollment": "دانش‌آموز عضویت کلاس با ثبت‌نام یکسان نیست."})
            if membership.class_group.offering_id and membership.class_group.offering_id != self.offering_id:
                raise ValidationError({"final_class_enrollment": "کلاس به برگزاری دیگری تعلق دارد."})

        if self.discount_type == self.DiscountType.PERCENT and (self.discount_value or 0) > 100:
            raise ValidationError({"discount_value": "درصد تخفیف نمی‌تواند بیش از ۱۰۰ باشد."})
        if self.payment_method == self.PaymentMethod.CHEQUE:
            if not (self.cheques or []):
                raise ValidationError({"cheques": "برای پرداخت چک، حداقل یک چک وارد کنید."})
            if self.cheque_count and self.cheque_count != len(self.cheques):
                raise ValidationError({"cheque_count": "تعداد چک با فهرست چک‌ها هم‌خوان نیست."})
        self.final_amount = self.compute_final()


class EnrollmentRefund(DomainModel):
    """ثبت غیرقابل‌حذف رویدادهای عودت وجه ثبت‌نام."""

    class Status(models.TextChoices):
        REQUESTED = "requested", "درخواست‌شده"
        APPROVED = "approved", "تأییدشده"
        PROCESSED = "processed", "پردازش‌شده"
        REJECTED = "rejected", "ردشده"

    enrollment = models.ForeignKey(
        OfferingEnrollment,
        on_delete=models.PROTECT,
        related_name="refunds",
    )
    amount = models.PositiveIntegerField(help_text="مبلغ عودت به تومان")
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.REQUESTED,
        db_index=True,
    )
    reason = models.TextField(blank=True, default="")
    reference = models.CharField(max_length=128, blank=True, default="")
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="requested_enrollment_refunds",
    )
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_enrollment_refunds",
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        app_label = "education"
        db_table = "education_enrollment_refund"
        ordering = ("-created_at",)
        indexes = [
            models.Index(
                fields=["enrollment", "status"],
                name="edu_refund_enroll_status_idx",
            ),
            models.Index(
                fields=["status", "created_at"],
                name="edu_refund_status_created_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.enrollment_id} → {self.amount} [{self.status}]"

    @property
    def final_amount_jalali_date(self) -> str:
        from apps.core.utils import persian_date
        return persian_date(self.enrolled_at)


class EnrollmentWaitlist(DomainModel):
    """A student's queue position when an offering has no free seat."""

    class Status(models.TextChoices):
        WAITING = "waiting", "در صف انتظار"
        OFFERED = "offered", "صندلی آزاد شد"
        ENROLLED = "enrolled", "به ثبت‌نام تبدیل شد"
        DECLINED = "declined", "ردشده"
        CANCELLED = "cancelled", "لغوشده"

    offering = models.ForeignKey(
        CourseOffering, on_delete=models.PROTECT, related_name="waitlist_entries"
    )
    student = models.ForeignKey(
        "persons.Person", on_delete=models.PROTECT, related_name="enrollment_waitlists",
        limit_choices_to={"person_type": "student"},
    )
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.WAITING, db_index=True
    )
    requested_at = models.DateTimeField(default=timezone.now, db_index=True)
    offered_at = models.DateTimeField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    note = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        app_label = "education"
        db_table = "education_enrollment_waitlist"
        ordering = ("requested_at", "created_at")
        constraints = [
            models.UniqueConstraint(
                fields=["offering", "student"],
                condition=_ALIVE & models.Q(status__in=["waiting", "offered"]),
                name="uniq_edu_waitlist_active_student",
            ),
        ]
        indexes = [
            models.Index(fields=["offering", "status", "requested_at"]),
            models.Index(fields=["student", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.student} → {self.offering} [{self.status}]"


class ParentReportDelivery(DomainModel):
    """Audit/status record for PDF and parent SMS report delivery."""

    class Channel(models.TextChoices):
        PDF = "pdf", "PDF"
        SMS = "sms", "پیامک"

    class Status(models.TextChoices):
        QUEUED = "queued", "در صف ارسال"
        SENT = "sent", "ارسال‌شده"
        FAILED = "failed", "ناموفق"

    student = models.ForeignKey(
        "persons.Person", on_delete=models.CASCADE, related_name="report_deliveries"
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="requested_parent_reports",
    )
    channel = models.CharField(max_length=8, choices=Channel.choices, db_index=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.QUEUED, db_index=True)
    recipient = models.CharField(max_length=128, blank=True, default="")
    period_label = models.CharField(max_length=64, blank=True, default="")
    error = models.TextField(blank=True, default="")
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "education"
        db_table = "education_parent_report_delivery"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["student", "channel", "created_at"]),
            models.Index(fields=["status", "channel"]),
        ]


class AcademicHoliday(DomainModel):
    """
    تقویم تعطیلات — تنها منبع حقیقت «پرش روز» در موتور زمان‌بندی.

    سه دامنه (scope) با هم OR می‌شوند تا یک ردیف بتواند هم‌زمان چند نوع
    تعطیلی را پوشش دهد:

      official  تعطیل رسمی سراسری (۲۲ بهمن، عاشورا، ...)
      weekly    جمعه (و در مؤسسات دخترانه پنجشنبه) — روزهای هفته‌ی تکرارشونده
      institute تعطیلی خاص مؤسسه (ترمیم، مراسم، عید)

    ``date_from``/``date_to`` بازه‌ای است؛ یک هفته‌ی full-time در یک ردیف
    می‌نشیند. ``location`` خالی = همه‌ی فضاها؛ پر شده = فقط آن سالن/کلاس
    (مثلاً «اتاق ۳ پنجشنبه تعطیل است»).
    """

    class Scope(models.TextChoices):
        OFFICIAL = "official", "تعطیل رسمی"
        WEEKLY = "weekly", "تعطیل هفتگی"
        INSTITUTE = "institute", "تعطیل مؤسسه"

    name = models.CharField(max_length=200)
    scope = models.CharField(
        max_length=16, choices=Scope.choices, default=Scope.OFFICIAL, db_index=True
    )
    date_from = models.DateField(db_index=True)
    date_to = models.DateField(db_index=True, help_text="برای تک‌روز = date_from")
    weekday = models.PositiveSmallIntegerField(
        null=True, blank=True,
        choices=((5, "شنبه"), (6, "یکشنبه"), (0, "دوشنبه"), (1, "سه‌شنبه"),
                 (2, "چهارشنبه"), (3, "پنجشنبه"), (4, "جمعه")),
        help_text="فقط برای scope=weekly: روز هفته‌ی تکرارشونده (Python weekday).",
    )
    all_day = models.BooleanField(
        default=True, help_text="خیر = فقط بخشی از روز (ساعت‌ها را در note قید کنید)."
    )
    location = models.ForeignKey(
        Location, null=True, blank=True, on_delete=models.CASCADE,
        related_name="holidays",
        help_text="خالی = کل مؤسسه.",
    )
    note = models.CharField(max_length=256, blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)
    legacy_id = models.CharField(max_length=64, blank=True, default="", db_index=True)

    class Meta:
        app_label = "education"
        db_table = "education_academic_holiday"
        verbose_name = "Holiday (تعطیلات)"
        verbose_name_plural = "Holidays (تعطیلات)"
        ordering = ("date_from", "scope")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(date_to__gte=models.F("date_from")),
                name="chk_edu_holiday_date_range",
            ),
        ]
        indexes = [
            models.Index(fields=["date_from", "is_active"], name="edu_holiday_date_active_idx"),
            models.Index(fields=["scope", "weekday"], name="edu_holiday_scope_weekday_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.date_from})"

    def clean(self) -> None:
        if self.scope == self.Scope.WEEKLY and self.weekday is None:
            from django.core.exceptions import ValidationError
            raise ValidationError(
                {"weekday": "برای تعطیل هفتگی، روز هفته را مشخص کنید."}
            )
        # A weekly entry is a rule, not an event — collapse its range to avoid
        # the engine double-counting it across dates.
        if self.scope == self.Scope.WEEKLY:
            self.date_from = self.date_to = self.date_from or timezone.localdate()

    def covers(self, day) -> bool:
        """آیا این ردیف تاریخ ``day`` را تعطیل می‌کند؟"""
        if self.scope == self.Scope.WEEKLY:
            return self.weekday is not None and day.weekday() == self.weekday
        return self.date_from <= day <= (self.date_to or self.date_from)
