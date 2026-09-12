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

from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import DomainModel
from apps.core.utils import persian_numbers

_ALIVE = models.Q(is_deleted=False)


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

    title = models.CharField(max_length=256)
    code = models.SlugField(max_length=64, db_index=True)
    description = models.TextField(blank=True, default="")
    syllabus = models.TextField(blank=True, default="", help_text="سرفصل/مباحث")
    duration_hours = models.PositiveIntegerField(default=0)
    department = models.ForeignKey(
        Department, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="lessons",
    )
    prerequisites = models.ManyToManyField(
        "self", symmetrical=False, blank=True, related_name="prerequisite_of"
    )
    assessment_method = models.CharField(
        max_length=32, blank=True, default="",
        help_text="written/oral/project/none",
    )
    required_equipment = models.TextField(blank=True, default="")
    learning_resources = models.TextField(blank=True, default="")
    tuition = models.PositiveIntegerField(default=0)
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

    def clean(self) -> None:
        self.code = (self.code or "").strip().lower()
        if self.duration_hours and self.duration_hours > 1000:
            raise ValidationError({"duration_hours": "ساعات تدریس غیرمنطقی است."})


class Course(DomainModel):
    """دوره = بسته‌ی آموزشیِ متصل به درس‌ها (نه خودِ برگزاری)."""

    title = models.CharField(max_length=256)
    code = models.SlugField(max_length=64, db_index=True)
    description = models.TextField(blank=True, default="")
    objectives = models.TextField(blank=True, default="")
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
        return self.title or f"{self.course} ({self.start_date})"

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
    session_number = models.PositiveSmallIntegerField(default=1)
    title = models.CharField(max_length=256, blank=True, default="")
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
            # یک شماره جلسه در هر برگزاری، یکتا در میان جلسات زنده (§5).
            # جلسه‌های بدون offering (پل فرم حضور/ClassGroup) با NULL مجازند.
            models.UniqueConstraint(
                fields=["offering", "session_number"],
                condition=_ALIVE & models.Q(offering__isnull=False),
                name="uniq_edu_session_number_alive",
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
