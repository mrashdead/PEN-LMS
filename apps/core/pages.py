"""
Server-rendered pages for the dashboard shell (persons / education / reports).

Design: a single config-driven resource engine. Each "resource" (persons,
lessons, courses, offerings, sessions) is described by a declarative dict that
both the Django template and the client JS read — one template
(`resource.html`) and one script (`resource.js`) render list + filters +
create/detail modals for every resource. The server stays the source of
truth: the JS only calls the existing DRF endpoints; it never encodes
permissions or validation beyond what the API enforces.

Reports page is provided by ``apps.reports`` and consumes its read-only
reporting API; the education report endpoints remain available for legacy
consumers.
"""
from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.views.generic import TemplateView

# Roles that may see the education/admin surfaces (mirrors the read side of
# apps.core.permissions.IsAcademicManager; writes are gated by the API itself).
_STAFF_ROLES = {"teacher", "manager", "workflow_admin", "hr", "employee", "supervisor"}
_WRITE_ROLES = {"manager", "workflow_admin", "supervisor"}
# Org-intelligence screens (chart/permissions/responsibilities/delegation).
_ORG_ROLES = {"manager", "workflow_admin", "hr"}
# System-admin-only resources (full PII, e.g. persons). Narrower than _ORG_ROLES.
_SYS_ADMIN_ROLES = {"manager", "workflow_admin"}
# If a teacher ALSO holds any of these, they are not "teacher-only" and keep
# full staff access; a pure teacher (none of these) is restricted to the
# teacher portal. Mirrors context_processors.is_teacher_only.
_TEACHER_BLOCKED_ROLES = {"manager", "workflow_admin", "hr", "employee", "supervisor"}

#: Declarative resource configs. `columns`/`form`/`detail` drive the generic UI.
RESOURCE_CONFIG: dict[str, dict] = {
    "departments": {
        "title": "دپارتمان‌ها",
        "icon": "network",
        "api": "/api/education/departments/",
        "canCreate": True,
        "canEdit": True,
        "columns": [
            {"field": "code", "label": "کد"},
            {"field": "name", "label": "نام دپارتمان"},
            {"field": "is_active", "label": "فعال", "type": "bool"},
        ],
        "form": [
            {"name": "code", "label": "کد دپارتمان", "type": "text", "dir": "ltr", "required": True,
             "hint": "کلید یکتا — مثال: math, language"},
            {"name": "name", "label": "نام دپارتمان", "type": "text", "required": True},
            {"name": "parent", "label": "دپارتمان والد", "type": "lookup",
             "endpoint": "/api/education/departments/", "labelField": "name"},
            {"name": "description", "label": "توضیحات", "type": "textarea"},
        ],
        "detail": [
            {"field": "code", "label": "کد"},
            {"field": "name", "label": "نام"},
            {"field": "description", "label": "توضیحات"},
            {"field": "is_active", "label": "فعال", "type": "bool"},
        ],
    },
    "persons": {
        "title": "اشخاص",
        "icon": "users",
        "api": "/api/persons/",
        "searchParam": "search",
        "searchPlaceholder": "نام، کد ملی، موبایل، کد دانش‌آموزی/پرسنلی…",
        "canCreate": True,
        "hasActions": True,  # persons: create-user / assign-type
        "adminOnly": True,   # full PII — elevated roles only (see ResourcePage)
        "filters": [
            {"param": "person_type", "label": "نوع", "type": "select", "options": [
                {"value": "", "label": "همه انواع"},
                {"value": "student", "label": "دانش‌آموز"},
                {"value": "teacher", "label": "معلم / مدرس"},
                {"value": "employee", "label": "کارمند"},
            ]},
            {"param": "is_active", "label": "وضعیت", "type": "select", "options": [
                {"value": "", "label": "همه"},
                {"value": "true", "label": "فعال"},
                {"value": "false", "label": "غیرفعال"},
            ]},
        ],
        "columns": [
            {"field": "display_national_code", "label": "کد ملی"},
            {"field": "first_name", "label": "نام"},
            {"field": "last_name", "label": "نام خانوادگی"},
            {"field": "person_type_display", "label": "نوع", "type": "badge"},
            {"field": "display_mobile", "label": "موبایل"},
            {"field": "has_user", "label": "کاربر", "type": "bool"},
        ],
        "form": [
            {"name": "first_name", "label": "نام", "type": "text", "required": True},
            {"name": "last_name", "label": "نام خانوادگی", "type": "text", "required": True},
            {"name": "national_code", "label": "کد ملی", "type": "text", "required": True, "dir": "ltr", "hint": "۱۰ رقم"},
            {"name": "father_name", "label": "نام پدر", "type": "text"},
            {"name": "person_type", "label": "نوع شخص", "type": "select", "required": True, "options": [
                {"value": "student", "label": "دانش‌آموز"},
                {"value": "teacher", "label": "معلم / مدرس"},
                {"value": "employee", "label": "کارمند"},
            ]},
            {"name": "grant_role", "label": "نقش رهبری (برای کارمند)", "type": "select",
             "when": {"person_type": ["employee"]}, "options": [
                {"value": "", "label": "— بدون نقش اضافه (کارمند عادی) —"},
                {"value": "supervisor", "label": "سرپرست"},
                {"value": "manager", "label": "مدیر"},
            ], "hint": "سرپرست فقط توسط مدیر؛ مدیر فقط توسط مدیر سیستم قابل اعطا است."},
            {"name": "birth_date", "label": "تاریخ تولد", "type": "jalali-date"},
            {"name": "gender", "label": "جنسیت", "type": "select", "options": [
                {"value": "unspecified", "label": "مشخص نشده"},
                {"value": "male", "label": "مرد"},
                {"value": "female", "label": "زن"},
            ]},
            {"name": "mobile", "label": "شماره تماس", "type": "text", "dir": "ltr", "required": True},
            {"name": "email", "label": "ایمیل", "type": "email", "dir": "ltr"},
            {"name": "address", "label": "آدرس منزل", "type": "textarea"},
            {"name": "student_code", "label": "کد دانش‌آموزی", "type": "text", "dir": "ltr", "when": {"person_type": ["student"]}},
            {"name": "employee_code", "label": "کد پرسنلی", "type": "text", "dir": "ltr", "when": {"person_type": ["employee", "teacher"]}},
            {"name": "department", "label": "دپارتمان", "type": "text", "when": {"person_type": ["employee", "teacher"]}},
            {"name": "job_title", "label": "سمت", "type": "text", "when": {"person_type": ["employee", "teacher"]}},
        ],
        "detail": [
            {"field": "display_name", "label": "نام کامل"},
            {"field": "display_national_code", "label": "کد ملی"},
            {"field": "person_types_display", "label": "نوع(ها)"},
            {"field": "father_name", "label": "نام پدر"},
            {"field": "birth_date", "label": "تاریخ تولد"},
            {"field": "gender_display", "label": "جنسیت"},
            {"field": "display_mobile", "label": "موبایل"},
            {"field": "email", "label": "ایمیل"},
            {"field": "address", "label": "آدرس"},
            {"field": "student_code", "label": "کد دانش‌آموزی"},
            {"field": "employee_code", "label": "کد پرسنلی"},
            {"field": "department", "label": "دپارتمان"},
            {"field": "job_title", "label": "سمت"},
            {"field": "username", "label": "نام کاربری"},
            {"field": "is_active", "label": "فعال", "type": "bool"},
        ],
    },
    "lessons": {
        "title": "درس‌ها",
        "icon": "book-open",
        "api": "/api/education/lessons/",
        "canCreate": True,
        "canEdit": True,
        "columns": [
            {"field": "code", "label": "کد"},
            {"field": "title", "label": "عنوان درس"},
            {"field": "duration_hours", "label": "مدت (ساعت)"},
            {"field": "space_type", "label": "فضا"},
            {"field": "tuition", "label": "شهریه", "type": "money", "suffix": "ت"},
            {"field": "is_active", "label": "فعال", "type": "bool"},
        ],
        "form": [
            # code is auto-generated (ls-0001) server-side — not shown.
            {"name": "title", "label": "عنوان درس (فارسی)", "type": "text", "required": True},
            {"name": "title_en", "label": "عنوان درس (انگلیسی)", "type": "text", "dir": "ltr"},
            {"name": "syllabus", "label": "سرفصل‌ها", "type": "textarea"},
            {"name": "duration_hours", "label": "مدت زمان (ساعت)", "type": "number"},
            {"name": "description", "label": "توضیحات درس", "type": "textarea"},
            {"name": "audience_age", "label": "محدوده سنی", "type": "text", "dir": "ltr",
             "placeholder": "10-15", "hint": "مثال: 10-15"},
            {"name": "prerequisites", "label": "پیش‌نیازها", "type": "check-lookup",
             "endpoint": "/api/education/lessons/", "labelField": "title"},
            {"name": "space_type", "label": "نوع فضای آموزشی (پیشنهادی)", "type": "select", "options": [
                {"value": "", "label": "نامشخص"},
                {"value": "classroom", "label": "کلاس"},
                {"value": "lab", "label": "آزمایشگاه"},
                {"value": "workshop", "label": "کارگاه"},
                {"value": "online", "label": "آنلاین"},
                {"value": "hall", "label": "سالن"},
            ]},
            {"name": "required_equipment", "label": "تجهیزات مورد نیاز", "type": "textarea"},
            {"name": "learning_resources", "label": "منابع آموزشی", "type": "textarea"},
            {"name": "tuition", "label": "شهریه", "type": "money", "unit": "تومان"},
        ],
        "detail": [
            {"field": "code", "label": "کد"},
            {"field": "title", "label": "عنوان (فارسی)"},
            {"field": "title_en", "label": "عنوان (انگلیسی)"},
            {"field": "syllabus", "label": "سرفصل‌ها"},
            {"field": "duration_hours", "label": "مدت (ساعت)"},
            {"field": "description", "label": "توضیحات"},
            {"field": "audience_age", "label": "محدوده سنی"},
            {"field": "space_type", "label": "نوع فضا"},
            {"field": "required_equipment", "label": "تجهیزات"},
            {"field": "learning_resources", "label": "منابع"},
            {"field": "tuition", "label": "شهریه", "type": "money", "suffix": "تومان"},
            {"field": "is_active", "label": "فعال", "type": "bool"},
        ],
    },
    "courses": {
        "title": "دوره‌ها",
        "icon": "library",
        "api": "/api/education/courses/",
        "canCreate": True,
        "canEdit": True,
        "columns": [
            {"field": "code", "label": "کد"},
            {"field": "title", "label": "عنوان دوره"},
            {"field": "total_tuition", "label": "شهریهٔ کل", "type": "money", "suffix": "ت"},
            {"field": "is_active", "label": "فعال", "type": "bool"},
        ],
        "form": [
            # code auto (cs-0001) server-side — not shown.
            {"name": "title", "label": "عنوان دوره", "type": "text", "required": True},
            {"name": "department", "label": "دپارتمان", "type": "lookup",
             "endpoint": "/api/education/departments/", "labelField": "name"},
            {"name": "description", "label": "توضیحات دوره", "type": "textarea"},
            {"name": "objectives", "label": "اهداف یادگیری", "type": "textarea"},
            {"name": "lessons", "label": "درس‌ها", "type": "check-lookup", "required": True,
             "endpoint": "/api/education/lessons/", "labelField": "title"},
        ],
        "detail": [
            {"field": "code", "label": "کد"},
            {"field": "title", "label": "عنوان"},
            {"field": "description", "label": "توضیحات"},
            {"field": "objectives", "label": "اهداف"},
            {"field": "lesson_titles", "label": "درس‌ها", "type": "list"},
            {"field": "total_tuition", "label": "شهریهٔ کل (مجموع درس‌ها)", "type": "money", "suffix": "تومان"},
            {"field": "is_active", "label": "فعال", "type": "bool"},
        ],
    },
    "offerings": {
        "title": "برگزاری دوره",
        "icon": "calendar-clock",
        "api": "/api/education/offerings/",
        "canCreate": True,
        "canEdit": True,
        "formationAction": True,   # «تشکیل کلاس» در مودال جزئیات
        "columns": [
            {"field": "code", "label": "کد برگزاری"},
            {"field": "title", "label": "برگزاری"},
            {"field": "course_title", "label": "دوره"},
            {"field": "capacity", "label": "ظرفیت"},
            {"field": "enrolled_count", "label": "ثبت‌نام"},
            {"field": "start_date", "label": "شروع"},
            {"field": "status", "label": "وضعیت", "type": "badge"},
        ],
        "form": [
            {"name": "course", "label": "دوره", "type": "lookup", "required": True,
             "endpoint": "/api/education/courses/", "labelField": "title"},
            {"name": "code", "label": "کد/عنوان برگزاری", "type": "text", "dir": "ltr",
             "placeholder": "OFFERING-1403-PY01",
             "hint": "یکتا؛ خالی بگذارید تا به‌صورت of-0001 خودکار ساخته شود."},
            {"name": "title", "label": "عنوان برگزاری", "type": "text"},
            {"name": "capacity", "label": "ظرفیت (۰ = نامحدود)", "type": "number"},
            {"name": "total_sessions", "label": "تعداد جلسات دوره (راهنمای تشکیل کلاس؛ ۰ = محاسبه از مدت درس)", "type": "number"},
            {"name": "lessons_roster", "label": "درس‌های دوره (به‌صورت خودکار از دوره واکشی می‌شود)", "type": "readonly-list",
             "source": "course", "endpoint": "/api/education/courses/"},
            {"name": "start_date", "label": "تاریخ شروع (پیشنهادی)", "type": "jalali-date"},
            {"name": "location", "label": "محل برگزاری (پیشنهادی)", "type": "lookup",
             "endpoint": "/api/education/locations/", "labelField": "name"},
            {"name": "instructor", "label": "استاد (پیشنهادی)", "type": "lookup",
             "endpoint": "/api/persons/?person_type=teacher",
             "labelTemplate": "{first_name} {last_name}"},
            {"name": "schedule", "label": "زمان برگزاری (پیشنهادی — روزها و ساعت)", "type": "schedule"},
            {"name": "auto_skip_holidays", "label": "پرش خودکار تعطیلات در تولید جلسات", "type": "checkbox"},
            {"name": "course_tuition", "label": "شهریه دوره (از دوره خوانده می‌شود)", "type": "readonly-money",
             "source": "course", "endpoint": "/api/education/courses/", "valueField": "total_tuition"},
            {"name": "status", "label": "وضعیت", "type": "select", "options": [
                {"value": "draft", "label": "پیش‌نویس"},
                {"value": "open", "label": "باز (ثبت‌نام)"},
                {"value": "running", "label": "در حال برگزاری"},
                {"value": "finished", "label": "پایان‌یافته"},
                {"value": "closed", "label": "بسته"},
                {"value": "cancelled", "label": "لغوشده"},
            ]},
        ],
        "detail": [
            {"field": "code", "label": "کد برگزاری"},
            {"field": "title", "label": "برگزاری"},
            {"field": "course_title", "label": "دوره"},
            {"field": "capacity", "label": "ظرفیت"},
            {"field": "enrolled_count", "label": "ثبت‌نام‌شدگان"},
            {"field": "seats_left_display", "label": "جای خالی"},
            {"field": "start_date", "label": "شروع"},
            {"field": "lesson_titles", "label": "درس‌های دوره", "type": "list"},
            {"field": "classes", "label": "کلاس‌های تشکیل‌شده", "type": "classes"},
            {"field": "course_tuition", "label": "شهریه دوره", "type": "money", "suffix": "تومان"},
            {"field": "status", "label": "وضعیت"},
        ],
    },
    "sessions": {
        "title": "جلسات کلاس",
        "icon": "calendar-days",
        "api": "/api/education/sessions/",
        "canCreate": False,       # sessions come from «تشکیل کلاس» (or the
        "canEdit": True,          # manual per-session adjustment, task §3.ب
        "formationLink": True,    # «تشکیل کلاس» button on the page header
        "columns": [
            {"field": "class_code", "label": "کد کلاس"},
            {"field": "offering_title", "label": "برگزاری"},
            {"field": "lesson_title", "label": "درس"},
            {"field": "session_number", "label": "جلسه"},
            {"field": "session_date", "label": "تاریخ"},
            {"field": "start_time", "label": "شروع"},
            {"field": "end_time", "label": "پایان"},
            {"field": "teacher_name", "label": "استاد"},
            {"field": "location_name", "label": "محل"},
            {"field": "status", "label": "وضعیت", "type": "badge"},
        ],
        "form": [
            {"name": "offering", "label": "برگزاری دوره", "type": "lookup", "required": True,
             "endpoint": "/api/education/offerings/", "labelField": "code"},
            # class_code is display-only in detail (the generator owns it).
            {"name": "lesson", "label": "درس", "type": "lookup",
             "endpoint": "/api/education/lessons/", "labelField": "title"},
            {"name": "teacher", "label": "استاد", "type": "lookup",
             "endpoint": "/api/persons/?person_type=teacher",
             "labelTemplate": "{first_name} {last_name}"},
            {"name": "location", "label": "محل برگزاری کلاس", "type": "lookup",
             "endpoint": "/api/education/locations/", "labelField": "name"},
            {"name": "title", "label": "عنوان جلسه", "type": "text"},
            {"name": "session_date", "label": "تاریخ جلسه", "type": "jalali-date", "required": True},
            {"name": "start_time", "label": "ساعت شروع", "type": "jalali-time", "required": True},
            {"name": "end_time", "label": "ساعت پایان", "type": "jalali-time", "required": True},
            {"name": "status", "label": "وضعیت", "type": "select", "options": [
                {"value": "scheduled", "label": "زمان‌بندی‌شده"},
                {"value": "held", "label": "برگزارشده"},
                {"value": "cancelled", "label": "لغوشده"},
            ]},
        ],
        "detail": [
            {"field": "class_code", "label": "کد کلاس"},
            {"field": "offering_title", "label": "برگزاری"},
            {"field": "lesson_title", "label": "درس"},
            {"field": "session_number", "label": "جلسه"},
            {"field": "title", "label": "عنوان"},
            {"field": "session_date", "label": "تاریخ"},
            {"field": "start_time", "label": "شروع"},
            {"field": "end_time", "label": "پایان"},
            {"field": "teacher_name", "label": "استاد"},
            {"field": "location_name", "label": "محل"},
            {"field": "status", "label": "وضعیت"},
        ],
    },
    "locations": {
        "title": "محل‌های آموزش",
        "icon": "map-pin",
        "api": "/api/education/locations/",
        "canCreate": True,
        "canEdit": True,
        "columns": [
            {"field": "code", "label": "کد"},
            {"field": "name", "label": "نام محل"},
            {"field": "building", "label": "ساختمان"},
            {"field": "capacity", "label": "ظرفیت"},
            {"field": "is_active", "label": "فعال", "type": "bool"},
        ],
        "form": [
            {"name": "code", "label": "کد محل", "type": "text", "dir": "ltr", "required": True},
            {"name": "name", "label": "نام محل", "type": "text", "required": True, "hint": "مثلاً کلاس ۱۰۱، سالن اجتماعات"},
            {"name": "building", "label": "ساختمان", "type": "text"},
            {"name": "capacity", "label": "ظرفیت (۰ = نامحدود)", "type": "number"},
            {"name": "equipment", "label": "تجهیزات", "type": "textarea", "hint": "پروژکتور، سیستم، و…"},
        ],
        "detail": [
            {"field": "code", "label": "کد"},
            {"field": "name", "label": "نام"},
            {"field": "building", "label": "ساختمان"},
            {"field": "capacity", "label": "ظرفیت"},
            {"field": "equipment", "label": "تجهیزات"},
            {"field": "is_active", "label": "فعال", "type": "bool"},
        ],
    },
}


class StaffRequiredMixin(LoginRequiredMixin):
    """Dashboard workspace pages: any staff role may read; writes gated by API.

    A teacher who holds no management role (``is_teacher_only``) is blocked
    from every management page here (403) — they get only the dedicated
    teacher portal (pages that set ``teacher_allowed = True``).
    """

    teacher_allowed = False

    def _is_teacher_only(self, request) -> bool:
        roles = set(request.user.role_codes()) if hasattr(request.user, "role_codes") else set()
        return "teacher" in roles and not (roles & _TEACHER_BLOCKED_ROLES)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        roles = set(request.user.role_codes()) if hasattr(request.user, "role_codes") else set()
        if not roles & _STAFF_ROLES:
            raise Http404
        if self._is_teacher_only(request) and not self.teacher_allowed:
            raise PermissionDenied("این بخش برای پنل مدرس در دسترس نیست.")
        return super().dispatch(request, *args, **kwargs)


class ResourcePage(StaffRequiredMixin, TemplateView):
    """Generic list + create/detail modal page for one configured resource.

    Resources flagged ``adminOnly`` (e.g. persons — full PII) are gated to the
    elevated roles even for reading; the base staff gate still applies to the
    rest. The underlying APIs enforce their own permissions regardless.
    """

    template_name = "resource.html"

    def dispatch(self, request, *args, **kwargs):
        # adminOnly resources (persons — full PII) are elevated-role only, even
        # to read. Check before rendering; base staff gate still applies after.
        if request.user.is_authenticated:
            key = kwargs.get("resource") or self.kwargs.get("resource")
            config = RESOURCE_CONFIG.get(key) or {}
            if config.get("adminOnly"):
                roles = set(request.user.role_codes()) if hasattr(request.user, "role_codes") else set()
                if not roles & _SYS_ADMIN_ROLES:
                    raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        key = self.kwargs.get("resource") or kwargs.get("resource")
        config = RESOURCE_CONFIG.get(key)
        if config is None:
            raise Http404
        roles = set(self.request.user.role_codes()) if hasattr(self.request.user, "role_codes") else set()
        context["resource_key"] = key
        context["resource_title"] = config["title"]
        context["can_write"] = bool(roles & _WRITE_ROLES)
        context["config"] = config  # flags for the static header buttons
        context["config_json"] = config  # serialized via json_script in template
        return context


class TimetablePage(StaffRequiredMixin, TemplateView):
    """Daily timetable grid — rows=locations, cols=hours (timetable.js)."""

    template_name = "timetable.html"
    teacher_allowed = True  # teachers see their own schedule


class TeacherDashboardPage(StaffRequiredMixin, TemplateView):
    """Teacher portal home — assigned offerings + upcoming sessions."""

    template_name = "teacher_dashboard.html"
    teacher_allowed = True


class TeacherAttendancePage(StaffRequiredMixin, TemplateView):
    """Attendance management — pick class → auto roster → record per session."""

    template_name = "teacher_attendance.html"
    teacher_allowed = True


class TeacherReportCardPage(StaffRequiredMixin, TemplateView):
    """Descriptive report cards — pick class → per-student passed/failed + note."""

    template_name = "teacher_report_cards.html"
    teacher_allowed = True


class LearnerPortalPage(LoginRequiredMixin, TemplateView):
    """Student/parent portal — own attendance stats + report cards."""

    template_name = "learner_portal.html"


class MessagesPage(StaffRequiredMixin, TemplateView):
    """Internal staff messaging (inbox + compose + thread view)."""

    template_name = "messages.html"


class EnrollmentPage(StaffRequiredMixin, TemplateView):
    """Financial enrollment form (student + offering + discount + payment)."""

    template_name = "enrollment.html"


class WorkQueuePage(StaffRequiredMixin, TemplateView):
    """My work queue (کارتابل) — task-oriented view over /api/tasks/*."""

    template_name = "work_queue.html"


class RequestsPage(LoginRequiredMixin, TemplateView):
    """Requests (درخواست‌ها) — workflow instances scoped by the API.

    Open to every role (a student sees their own requests, staff see the
    ones they may act on) — visibility is enforced by the instances API,
    not here.
    """

    template_name = "requests.html"


class OrgManagerMixin(LoginRequiredMixin):
    """Org screens are an admin tool — mirror the elevated-role trio.

    Presentation gate only; the /api/org/* endpoints enforce the same roles
    server-side, so a hidden page is not the security boundary.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        roles = set(request.user.role_codes()) if hasattr(request.user, "role_codes") else set()
        if not roles & _ORG_ROLES:
            raise Http404
        return super().dispatch(request, *args, **kwargs)


class OrgChartPage(OrgManagerMixin, TemplateView):
    template_name = "org_chart.html"


class OrgPermissionsPage(OrgManagerMixin, TemplateView):
    template_name = "org_permissions.html"


class OrgResponsibilitiesPage(OrgManagerMixin, TemplateView):
    template_name = "org_responsibilities.html"


class OrgDelegationsPage(OrgManagerMixin, TemplateView):
    template_name = "org_delegations.html"


class PermissionManagePage(OrgManagerMixin, TemplateView):
    """Per-user permission editor: search a person → view/edit roles + groups."""

    template_name = "perm_manage.html"
