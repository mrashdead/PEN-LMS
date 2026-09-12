"""
Server-rendered pages for the dashboard shell (persons / education / reports).

Design: a single config-driven resource engine. Each "resource" (persons,
lessons, courses, offerings, sessions) is described by a declarative dict that
both the Django template and the client JS read — one template
(`resource.html`) and one script (`resource.js`) render list + filters +
create/detail modals for every resource. The server stays the source of
truth: the JS only calls the existing DRF endpoints; it never encodes
permissions or validation beyond what the API enforces.

Reports page renders charts from /api/education/reports/* (real aggregates).
"""
from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.views.generic import TemplateView

# Roles that may see the education/admin surfaces (mirrors the read side of
# apps.core.permissions.IsAcademicManager; writes are gated by the API itself).
_STAFF_ROLES = {"teacher", "manager", "workflow_admin", "hr", "employee"}
_WRITE_ROLES = {"manager", "workflow_admin"}
# Org-intelligence screens (chart/permissions/responsibilities/delegation).
_ORG_ROLES = {"manager", "workflow_admin", "hr"}
# System-admin-only resources (full PII, e.g. persons). Narrower than _ORG_ROLES.
_SYS_ADMIN_ROLES = {"manager", "workflow_admin"}

#: Declarative resource configs. `columns`/`form`/`detail` drive the generic UI.
RESOURCE_CONFIG: dict[str, dict] = {
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
                {"value": "parent", "label": "والدین"},
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
                {"value": "parent", "label": "والدین"},
            ]},
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
            {"name": "auto_create_user", "label": "ساخت خودکار کاربر (نام‌کاربری/رمز = کد ملی)", "type": "checkbox"},
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
        "columns": [
            {"field": "code", "label": "کد"},
            {"field": "title", "label": "عنوان درس"},
            {"field": "duration_hours", "label": "مدت (ساعت)"},
            {"field": "assessment_method", "label": "نحوه آزمون"},
            {"field": "tuition", "label": "شهریه"},
            {"field": "is_active", "label": "فعال", "type": "bool"},
        ],
        "form": [
            {"name": "code", "label": "کد درس", "type": "text", "dir": "ltr", "required": True},
            {"name": "title", "label": "عنوان درس", "type": "text", "required": True},
            {"name": "syllabus", "label": "سرفصل / مباحث", "type": "textarea"},
            {"name": "description", "label": "توضیحات", "type": "textarea"},
            {"name": "duration_hours", "label": "مدت زمان (ساعت)", "type": "number"},
            {"name": "assessment_method", "label": "نحوه آزمون", "type": "select", "options": [
                {"value": "written", "label": "کتبی"},
                {"value": "oral", "label": "شفاهی"},
                {"value": "project", "label": "پروژه"},
                {"value": "continuous", "label": "مستمر"},
                {"value": "none", "label": "بدون آزمون"},
            ]},
            {"name": "required_equipment", "label": "تجهیزات مورد نیاز", "type": "textarea"},
            {"name": "learning_resources", "label": "منابع آموزش", "type": "textarea"},
            {"name": "tuition", "label": "شهریه (ریال)", "type": "number"},
        ],
        "detail": [
            {"field": "code", "label": "کد"},
            {"field": "title", "label": "عنوان"},
            {"field": "syllabus", "label": "سرفصل"},
            {"field": "description", "label": "توضیحات"},
            {"field": "duration_hours", "label": "مدت (ساعت)"},
            {"field": "assessment_method", "label": "نحوه آزمون"},
            {"field": "required_equipment", "label": "تجهیزات"},
            {"field": "learning_resources", "label": "منابع"},
            {"field": "tuition", "label": "شهریه"},
            {"field": "is_active", "label": "فعال", "type": "bool"},
        ],
    },
    "courses": {
        "title": "دوره‌ها",
        "icon": "library",
        "api": "/api/education/courses/",
        "canCreate": True,
        "columns": [
            {"field": "code", "label": "کد"},
            {"field": "title", "label": "عنوان دوره"},
            {"field": "is_active", "label": "فعال", "type": "bool"},
        ],
        "form": [
            {"name": "code", "label": "کد دوره", "type": "text", "dir": "ltr", "required": True},
            {"name": "title", "label": "عنوان دوره", "type": "text", "required": True},
            {"name": "description", "label": "توضیحات دوره", "type": "textarea"},
            {"name": "objectives", "label": "اهداف یادگیری", "type": "textarea"},
        ],
        "detail": [
            {"field": "code", "label": "کد"},
            {"field": "title", "label": "عنوان"},
            {"field": "description", "label": "توضیحات"},
            {"field": "objectives", "label": "اهداف"},
            {"field": "is_active", "label": "فعال", "type": "bool"},
        ],
    },
    "offerings": {
        "title": "برگزاری دوره",
        "icon": "calendar-clock",
        "api": "/api/education/offerings/",
        "canCreate": True,
        "columns": [
            {"field": "title", "label": "برگزاری"},
            {"field": "capacity", "label": "ظرفیت"},
            {"field": "enrolled_count", "label": "ثبت‌نام"},
            {"field": "start_date", "label": "شروع"},
            {"field": "status", "label": "وضعیت", "type": "badge"},
        ],
        "form": [
            {"name": "course", "label": "دوره", "type": "lookup", "required": True,
             "endpoint": "/api/education/courses/", "labelField": "title"},
            {"name": "title", "label": "عنوان برگزاری", "type": "text"},
            {"name": "capacity", "label": "ظرفیت", "type": "number"},
            {"name": "start_date", "label": "تاریخ شروع", "type": "jalali-date"},
            {"name": "end_date", "label": "تاریخ پایان", "type": "jalali-date"},
            {"name": "location", "label": "محل برگزاری", "type": "lookup",
             "endpoint": "/api/education/locations/", "labelField": "name"},
            {"name": "instructor", "label": "استاد", "type": "lookup",
             "endpoint": "/api/persons/?person_type=teacher",
             "labelTemplate": "{first_name} {last_name}"},
            {"name": "tuition", "label": "شهریه", "type": "number"},
            {"name": "status", "label": "وضعیت", "type": "select", "options": [
                {"value": "planned", "label": "برنامه‌ریزی‌شده"},
                {"value": "open", "label": "باز (ثبت‌نام)"},
                {"value": "running", "label": "در حال برگزاری"},
                {"value": "completed", "label": "تکمیل‌شده"},
                {"value": "cancelled", "label": "لغوشده"},
            ]},
        ],
        "detail": [
            {"field": "title", "label": "برگزاری"},
            {"field": "capacity", "label": "ظرفیت"},
            {"field": "enrolled_count", "label": "ثبت‌نام‌شدگان"},
            {"field": "seats_left_display", "label": "جای خالی"},
            {"field": "start_date", "label": "شروع"},
            {"field": "end_date", "label": "پایان"},
            {"field": "status", "label": "وضعیت"},
            {"field": "tuition", "label": "شهریه"},
        ],
    },
    "sessions": {
        "title": "جلسات کلاس",
        "icon": "calendar-days",
        "api": "/api/education/sessions/",
        "canCreate": True,
        "columns": [
            {"field": "session_number", "label": "جلسه"},
            {"field": "title", "label": "عنوان"},
            {"field": "session_date", "label": "تاریخ"},
            {"field": "start_time", "label": "شروع"},
            {"field": "end_time", "label": "پایان"},
            {"field": "status", "label": "وضعیت", "type": "badge"},
        ],
        "form": [
            {"name": "offering", "label": "برگزاری دوره", "type": "lookup", "required": True,
             "endpoint": "/api/education/offerings/", "labelField": "title"},
            {"name": "lesson", "label": "درس", "type": "lookup",
             "endpoint": "/api/education/lessons/", "labelField": "title"},
            {"name": "teacher", "label": "استاد", "type": "lookup",
             "endpoint": "/api/persons/?person_type=teacher",
             "labelTemplate": "{first_name} {last_name}"},
            {"name": "location", "label": "محل برگزاری کلاس", "type": "lookup",
             "endpoint": "/api/education/locations/", "labelField": "name"},
            {"name": "session_number", "label": "شماره جلسه", "type": "number", "required": True},
            {"name": "title", "label": "عنوان جلسه", "type": "text"},
            {"name": "session_date", "label": "تاریخ جلسه", "type": "jalali-date", "required": True},
            {"name": "start_time", "label": "ساعت شروع (HH:MM)", "type": "text", "dir": "ltr", "required": True},
            {"name": "end_time", "label": "ساعت پایان (HH:MM)", "type": "text", "dir": "ltr", "required": True},
            {"name": "status", "label": "وضعیت", "type": "select", "options": [
                {"value": "scheduled", "label": "زمان‌بندی‌شده"},
                {"value": "held", "label": "برگزارشده"},
                {"value": "cancelled", "label": "لغوشده"},
            ]},
        ],
        "detail": [
            {"field": "session_number", "label": "جلسه"},
            {"field": "title", "label": "عنوان"},
            {"field": "session_date", "label": "تاریخ"},
            {"field": "start_time", "label": "شروع"},
            {"field": "end_time", "label": "پایان"},
            {"field": "status", "label": "وضعیت"},
        ],
    },
    "locations": {
        "title": "محل‌های آموزش",
        "icon": "map-pin",
        "api": "/api/education/locations/",
        "canCreate": True,
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
    """Dashboard workspace pages: any staff role may read; writes gated by API."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        roles = set(request.user.role_codes()) if hasattr(request.user, "role_codes") else set()
        if not roles & _STAFF_ROLES:
            raise Http404
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
        context["config_json"] = config  # serialized via json_script in template
        return context


class ReportsPage(StaffRequiredMixin, TemplateView):
    """Daily/weekly/monthly reports with real charts (ApexCharts)."""

    template_name = "reports.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["report_endpoints"] = {
            "attendance": "/api/education/reports/attendance/",
            "capacity": "/api/education/reports/capacity/",
        }
        return context


class TimetablePage(StaffRequiredMixin, TemplateView):
    """Daily timetable grid — rows=locations, cols=hours (timetable.js)."""

    template_name = "timetable.html"


class MessagesPage(StaffRequiredMixin, TemplateView):
    """Internal staff messaging (inbox + compose + thread view)."""

    template_name = "messages.html"


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
