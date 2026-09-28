"""
Access catalog — تنها منبع حقیقت برای کاتالوگ منابع و فعل‌های قابل اهدا.

این فایل هم توسط Enforcer (برای تصمیم‌گیری) و هم توسط API/UI (برای رندر گرید)
استفاده می‌شود. هر تغییر در منابع = ویرایش اینجا.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator

from django.apps import apps


# ── Verb constants ────────────────────────────────────────────────────────────
ALL_VERBS = {"view", "add", "change", "delete", "submit", "approve", "reject"}

PAGE_VERBS = {"view"}
FORM_VERBS = {"view", "add", "change", "delete", "submit", "approve", "reject"}
MODEL_VERBS = {"view", "add", "change", "delete"}


@dataclass(frozen=True, slots=True)
class Resource:
    key: str
    title: str
    category: str  # "page" | "form" | "model"
    verbs: tuple[str, ...]
    description: str = ""


# ── Page resources ────────────────────────────────────────────────────────────
# Key = route name (name= در urls.py)، هم‌نام با page_urls.py
_PAGE_RESOURCES: list[Resource] = [
    Resource(key="workspace-profile",        title="پروفایل کاربری",       category="page", verbs=PAGE_VERBS,              description="مشاهده و ویرایش پروفایل شخصی"),
    Resource(key="workspace-password-management", title="مدیریت رمز عبور", category="page", verbs=PAGE_VERBS),
    Resource(key="workspace-work",          title="کارتابل کاری",          category="page", verbs=PAGE_VERBS,              description="وظایف و درخواست‌های منتظر اقدام"),
    Resource(key="workspace-requests",      title="درخواست‌ها",             category="page", verbs=PAGE_VERBS),
    Resource(key="workspace-enrollments",  title="ثبت‌نام‌ها",             category="page", verbs=PAGE_VERBS),
    Resource(key="workspace-org-chart",   title="چارت سازمانی",          category="page", verbs=PAGE_VERBS),
    Resource(key="workspace-org-permissions", title="مجوزهای سازمانی",     category="page", verbs=PAGE_VERBS),
    Resource(key="workspace-org-responsibilities", title="مسئولیت‌ها",     category="page", verbs=PAGE_VERBS),
    #Resource(key="workspace-org-delegations",   title="شهرداری‌ها",         category="page", verbs=PAGE_VERBS),
    Resource(key="workspace-perm-manage",  title="مدیریت دسترسی کاربران", category="page", verbs=PAGE_VERBS, description="ACL دستی — فقط برای مدیران"),
    Resource(key="workspace-persons",       title="اشخاص",                 category="page", verbs={"view", "add"},          description="لیست و جستجوی اشخاص"),
    Resource(key="workspace-person-create",title="ایجاد شخص",             category="page", verbs={"add"}),
    Resource(key="workspace-departments",  title="دپارتمان‌ها",           category="page", verbs={"view", "add"}),
    Resource(key="workspace-terms",        title="ترم‌های تحصیلی",         category="page", verbs={"view", "add"}),
    Resource(key="workspace-lessons",      title="درس‌ها",                category="page", verbs={"view", "add"}),
    Resource(key="workspace-courses",      title="دوره‌ها",                category="page", verbs={"view", "add"}),
    Resource(key="workspace-offerings",    title="برگزاری‌ها",            category="page", verbs={"view", "add"}),
    Resource(key="workspace-sessions",     title="جلسات کلاسی",           category="page", verbs={"view", "add"}),
    Resource(key="workspace-locations",    title="محل‌ها / ساختمان‌ها",    category="page", verbs={"view", "add"}),
    Resource(key="workspace-timetable",    title="زمان‌بندی",              category="page", verbs=PAGE_VERBS),
    Resource(key="workspace-enrollment-capacity", title="گزارش ثبت‌نام و ظرفیت کلاس‌ها", category="page", verbs=PAGE_VERBS, description="آمار تجمیعی ثبت‌نام و ظرفیت؛ پیش‌فرض مدیریت و سرپرست. دسترسی مدرس محدود به کلاس‌های خودش است؛ بدون اطلاعات هویتی یا مالی."),
    Resource(key="workspace-reports",      title="گزارش‌ها",              category="page", verbs=PAGE_VERBS),
    Resource(key="workspace-teacher",      title="پنل معلم",               category="page", verbs=PAGE_VERBS),
    Resource(key="workspace-teacher-attendance", title="حضور معلم",        category="page", verbs=PAGE_VERBS),
    Resource(key="workspace-teacher-report-cards", title="کارنامه معلم",    category="page", verbs=PAGE_VERBS),
    Resource(key="workspace-learner-portal",  title="پنل دانش‌آموز/والدین",category="page", verbs=PAGE_VERBS),
    Resource(key="workspace-messages",     title="پیام‌ها",                category="page", verbs=PAGE_VERBS),
    Resource(key="leads-dashboard",        title="مدیریت لیدها",           category="page", verbs=PAGE_VERBS, description="ثبت و پیگیری لیدهای ورودی برای کارکنان"),
    Resource(key="leads-teacher-assessments", title="تعیین‌سطح‌های من",    category="page", verbs=PAGE_VERBS, description="صف اختصاصی استاد برای ارزیابی لیدهای تخصیص‌یافته"),
]

# ── Model resources ────────────────────────────────────────────────────────────
# Key = app_label.model_name
_MODEL_RESOURCES: list[Resource] = [
    # persons
    Resource(key="persons.person",          title="اشخاص",                  category="model", verbs=MODEL_VERBS),
    Resource(key="persons.persontypeassignment", title="انواع شخص",          category="model", verbs=MODEL_VERBS),
    # academics
    Resource(key="academics.academicterm", title="ترم‌ها",                  category="model", verbs=MODEL_VERBS),
    Resource(key="academics.classgroup",   title="کلاس‌ها",                 category="model", verbs=MODEL_VERBS),
    Resource(key="education.offeringenrollment", title="ثبت‌نام در دوره", category="model", verbs=MODEL_VERBS, description="مشاهده و مدیریت ثبت‌نام دوره؛ اطلاعات مالی تابع مجوز مستقل API مالی است."),
    Resource(key="academics.classenrollment", title="ثبت‌نام کلاسی",         category="model", verbs=MODEL_VERBS),
    # education
    Resource(key="education.department",   title="دپارتمان‌ها",             category="model", verbs=MODEL_VERBS),
    Resource(key="education.lesson",      title="درس‌ها",                  category="model", verbs=MODEL_VERBS),
    Resource(key="education.course",       title="دوره‌ها",                 category="model", verbs=MODEL_VERBS),
    Resource(key="education.courseoffering", title="برگزاری دوره",           category="model", verbs=MODEL_VERBS),
    Resource(key="education.classsession",  title="جلسات کلاسی",             category="model", verbs=MODEL_VERBS),
    Resource(key="education.location",     title="محل‌ها",                  category="model", verbs=MODEL_VERBS),
    Resource(key="education.academicholiday", title="تعطیلات",              category="model", verbs=MODEL_VERBS),
    Resource(key="education.attendance",   title="حضور و غیاب",             category="model", verbs=MODEL_VERBS),
    Resource(key="education.graderecord",  title="کارنامه / نمرات",         category="model", verbs=MODEL_VERBS),
    # forms
    Resource(key="forms.formschema",       title="تعریف فرم",               category="model", verbs=MODEL_VERBS),
    Resource(key="forms.formsubmission",   title="فرم‌ها",                  category="model", verbs=MODEL_VERBS),
    Resource(key="forms.formattachment",   title="پیوست فرم",               category="model", verbs=MODEL_VERBS),
    Resource(key="forms.formcomment",      title="نظرات فرم",               category="model", verbs=MODEL_VERBS),
    # workflow
    Resource(key="workflow.workflowdefinition", title="تعریف فرآیند",       category="model", verbs=MODEL_VERBS),
    Resource(key="workflow.instance",     title="درخواست‌ها / نمونه‌فرآیند", category="model", verbs=MODEL_VERBS),
    Resource(key="workflow.actionlog",    title="تاریخچه فرآیند",           category="model", verbs={"view"}),
    # org
    #Resource(key="org.delegation",        title="شهرداری",                 category="model", verbs=MODEL_VERBS),
    Resource(key="org.personaclentry",    title="ACL دستی",                category="model", verbs=MODEL_VERBS),
    # accounts
    Resource(key="accounts.role",         title="نقش‌ها",                  category="model", verbs=MODEL_VERBS),
    Resource(key="accounts.user",         title="کاربران",                category="model", verbs=MODEL_VERBS),
    # tasks
    Resource(key="tasks.workflowtask",    title="وظایف",                   category="model", verbs=MODEL_VERBS),
    Resource(key="tasks.reminder",        title="یادآوری‌ها",              category="model", verbs=MODEL_VERBS),
    # reports
    Resource(key="reports.dailyattendance", title="گزارش حضور روزانه",     category="model", verbs={"view"}),
    Resource(key="reports.weeklyreport",  title="گزارش هفتگی",            category="model", verbs={"view"}),
    Resource(key="reports.monthlyreport",  title="گزارش ماهانه",           category="model", verbs={"view"}),
    Resource(key="leads.lead",             title="لید و تعیین سطح",         category="model", verbs=MODEL_VERBS),
]

# ── In-memory catalog ──────────────────────────────────────────────────────────
_all_resources: dict[str, Resource] = {}


def _build_catalog() -> None:
    global _all_resources
    _all_resources = {}
    for r in _PAGE_RESOURCES:
        _all_resources[f"page:{r.key}"] = r
    for r in _MODEL_RESOURCES:
        _all_resources[f"model:{r.key}"] = r
    # form resources are registered dynamically from FormSchema (see form_resources()).


_build_catalog()


# ── Public API ─────────────────────────────────────────────────────────────────

def all_resources() -> list[Resource]:
    """Static catalog: page + model (excluding dynamic forms)."""
    return list(_all_resources.values())


def get_resource(resource_type: str, key: str) -> Resource | None:
    """Look up by type:key. Returns None if not found."""
    return _all_resources.get(f"{resource_type}:{key}")


def form_resources() -> list[dict]:
    """
    Dynamic form resources from DB — slugs of active FormSchema.
    Returns list[dict] with keys: key, title, category="form", verbs.
    """
    try:
        FormSchema = apps.get_model("forms", "FormSchema")
    except LookupError:
        return []
    return [
        {
            "key": s.slug,
            "title": s.title,
            "category": "form",
            "verbs": list(FORM_VERBS),
            "description": s.description or "",
        }
        for s in FormSchema.objects.filter(is_active=True, is_deleted=False)
        .order_by("title")
        .only("slug", "title", "description")
    ]


def catalog_for_type(resource_type: str) -> list[Resource] | list[dict]:
    """Return catalog entries filtered by type."""
    if resource_type == "form":
        return form_resources()
    return [r for r in _all_resources.values() if r.category == resource_type]


def valid_verbs(resource_type: str, resource_key: str) -> set[str]:
    """
    Return the set of valid verbs for a given (type, key).
    Falls back to FORM_VERBS/MODEL_VERBS/PAGE_VERBS when key unknown.
    """
    if resource_type == "form":
        return FORM_VERBS
    r = get_resource(resource_type, resource_key)
    if r:
        return set(r.verbs)
    if resource_type == "page":
        return PAGE_VERBS
    return MODEL_VERBS


def normalize_resource_type(type_str: str) -> str | None:
    """Parse 'workspace-reports' → ('page', 'workspace-reports'), 'persons.person' → ('model', 'persons.person')."""
    # page route patterns
    if type_str.startswith("workspace-"):
        return "page"
    # explicit type:key format
    if ":" in type_str:
        parts = type_str.split(":", 1)
        if parts[0] in ("page", "form", "model"):
            return parts[0]
    # model pattern: app_label.model_name
    if "." in type_str and not type_str.startswith("workspace-"):
        return "model"
    return None


def catalog_entry(resource_type: str, resource_key: str) -> dict:
    """
    Build a catalog dict with the shape UI expects:
    { key, title, category, verbs, description, is_dynamic }
    """
    r = get_resource(resource_type, resource_key)
    if r:
        return {
            "key": r.key,
            "title": r.title,
            "category": r.category,
            "verbs": list(r.verbs),
            "description": r.description,
            "is_dynamic": False,
        }
    # form — check DB
    if resource_type == "form":
        try:
            FormSchema = apps.get_model("forms", "FormSchema")
            s = FormSchema.objects.filter(slug=resource_key, is_active=True).first()
            if s:
                return {
                    "key": s.slug,
                    "title": s.title,
                    "category": "form",
                    "verbs": list(FORM_VERBS),
                    "description": s.description or "",
                    "is_dynamic": True,
                }
        except LookupError:
            pass
    return None
