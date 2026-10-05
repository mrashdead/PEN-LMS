"""Role and user overrides for the workspace sidebar presentation."""
from __future__ import annotations

from typing import Any

from django.db import DatabaseError, transaction

from apps.accounts.models import Role
from apps.forms.permissions import ELEVATED_ROLES
from apps.leads.permissions import LEAD_OPERATOR_ROLES
from apps.org.models import SidebarVisibilityRule
from apps.playhouse.permissions import FINANCE_ROLES, OPERATOR_ROLES
from apps.reports.permissions import REPORT_ACCESS_ROLES


STAFF_MENU_ROLES = {"manager", "workflow_admin", "hr", "employee"}
ORG_MENU_ROLES = {"manager", "workflow_admin", "hr"}

# `key` is stable storage/API identity. `flag` is the safe dictionary key used
# from Django templates. Defaults mirror the current sidebar's role groups.
SIDEBAR_ITEMS: tuple[dict[str, Any], ...] = (
    {"key": "dashboard-home", "flag": "dashboard_home", "title": "داشبورد", "section": "عمومی", "default_roles": None},
    {"key": "workspace-teacher", "flag": "workspace_teacher", "title": "داشبورد و دوره‌های من", "section": "پنل مدرس", "default_roles": {"teacher"}},
    {"key": "workspace-timetable", "flag": "workspace_timetable", "title": "تقویم و برنامه", "section": "آموزش", "default_roles": STAFF_MENU_ROLES | {"teacher"}},
    {"key": "workspace-teacher-attendance", "flag": "workspace_teacher_attendance", "title": "حضور و غیاب", "section": "پنل مدرس", "default_roles": {"teacher"}},
    {"key": "workspace-teacher-report-cards", "flag": "workspace_teacher_report_cards", "title": "کارنامه توصیفی", "section": "پنل مدرس", "default_roles": {"teacher"}},
    {"key": "workspace-teacher-progress-reports", "flag": "workspace_teacher_progress_reports", "title": "گزارش پیشرفت دانش‌آموزان", "section": "پنل مدرس", "default_roles": {"teacher"}},
    {"key": "leads-teacher-assessments", "flag": "leads_teacher_assessments", "title": "تعیین‌سطح‌های من", "section": "پنل مدرس", "default_roles": {"teacher"}},
    {"key": "workspace-learner-portal", "flag": "workspace_learner_portal", "title": "حضور، کارنامه و گزارش‌های من", "section": "پورتال دانش‌آموز", "default_roles": {"student", "guardian"}},
    {"key": "workspace-requests", "flag": "workspace_requests", "title": "درخواست‌ها", "section": "درخواست‌ها", "default_roles": STAFF_MENU_ROLES | {"student", "guardian"}},
    {"key": "workspace-work", "flag": "workspace_work", "title": "کارهای من", "section": "کارتابل", "default_roles": STAFF_MENU_ROLES},
    {"key": "staff-dashboard", "flag": "staff_dashboard", "title": "کارکرد و مرخصی", "section": "کارکنان", "default_roles": STAFF_MENU_ROLES | {"supervisor", "teacher"}},
    {"key": "calls-dashboard", "flag": "calls_dashboard", "title": "ثبت تماس‌ها", "section": "ارتباطات", "default_roles": STAFF_MENU_ROLES | {"supervisor", "teacher"}},
    {"key": "submission-picker", "flag": "submission_picker", "title": "مرکز درخواست‌ها", "section": "درخواست‌ها", "default_roles": STAFF_MENU_ROLES},
    {"key": "workspace-persons", "flag": "workspace_persons", "title": "جامعه آموزشی", "section": "آموزشگاه", "default_roles": ELEVATED_ROLES},
    {"key": "workspace-staff", "flag": "workspace_staff", "title": "اعضای مجموعه", "section": "کارکنان", "default_roles": ELEVATED_ROLES},
    {"key": "workspace-departments", "flag": "workspace_departments", "title": "دپارتمان‌ها", "section": "آموزشگاه", "default_roles": STAFF_MENU_ROLES},
    {"key": "workspace-terms", "flag": "workspace_terms", "title": "ترم‌های تحصیلی", "section": "آموزشگاه", "default_roles": STAFF_MENU_ROLES},
    {"key": "workspace-lessons", "flag": "workspace_lessons", "title": "درس‌ها", "section": "آموزشگاه", "default_roles": STAFF_MENU_ROLES},
    {"key": "workspace-courses", "flag": "workspace_courses", "title": "دوره‌ها", "section": "آموزشگاه", "default_roles": STAFF_MENU_ROLES},
    {"key": "workspace-offerings", "flag": "workspace_offerings", "title": "برگزاری‌ها", "section": "آموزشگاه", "default_roles": STAFF_MENU_ROLES},
    {"key": "workspace-sessions", "flag": "workspace_sessions", "title": "کلاس‌ها و جلسات", "section": "آموزشگاه", "default_roles": STAFF_MENU_ROLES},
    {"key": "workspace-locations", "flag": "workspace_locations", "title": "محل‌های آموزش", "section": "آموزشگاه", "default_roles": STAFF_MENU_ROLES},
    {"key": "workspace-enrollments", "flag": "workspace_enrollments", "title": "ثبت‌نام", "section": "آموزشگاه", "default_roles": STAFF_MENU_ROLES},
    {"key": "workspace-messages", "flag": "workspace_messages", "title": "پیام‌ها", "section": "ارتباطات", "default_roles": STAFF_MENU_ROLES},
    {"key": "workspace-enrollment-capacity", "flag": "workspace_enrollment_capacity", "title": "ثبت‌نام و ظرفیت کلاس‌ها", "section": "گزارش‌ها", "default_roles": REPORT_ACCESS_ROLES},
    {"key": "workspace-reports", "flag": "workspace_reports", "title": "گزارش‌ها و تحلیل‌ها", "section": "گزارش‌ها", "default_roles": REPORT_ACCESS_ROLES},
    {"key": "playhouse-dashboard", "flag": "playhouse_dashboard", "title": "خانه بازی", "section": "خانه بازی", "default_roles": OPERATOR_ROLES},
    {"key": "playhouse-finance", "flag": "playhouse_finance", "title": "گزارش مالی خانه بازی", "section": "خانه بازی", "default_roles": FINANCE_ROLES},
    {"key": "playhouse-settings", "flag": "playhouse_settings", "title": "تنظیمات خانه بازی", "section": "خانه بازی", "default_roles": FINANCE_ROLES},
    {"key": "leads-dashboard", "flag": "leads_dashboard", "title": "مدیریت لیدها", "section": "مدیریت لیدها", "default_roles": LEAD_OPERATOR_ROLES},
    {"key": "workspace-org-chart", "flag": "workspace_org_chart", "title": "نمودار سازمانی", "section": "مدیریت سازمان", "default_roles": ORG_MENU_ROLES},
    {"key": "workspace-perm-manage", "flag": "workspace_perm_manage", "title": "مدیریت مجوز کاربران", "section": "مدیریت سازمان", "default_roles": ORG_MENU_ROLES},
)

_ITEM_BY_KEY = {item["key"]: item for item in SIDEBAR_ITEMS}
_ITEMS_BY_FLAG = {item["flag"]: item for item in SIDEBAR_ITEMS}


def default_visible(item_key: str, role_code: str) -> bool:
    item = _ITEM_BY_KEY.get(item_key)
    if item is None:
        return False
    role_set = item["default_roles"]
    return role_set is None or role_code in role_set


def _active_rules(*, roles: set[str] | None = None, user=None) -> list[SidebarVisibilityRule]:
    query = SidebarVisibilityRule.objects.filter(is_deleted=False)
    if roles and user is not None:
        from django.db.models import Q
        query = query.filter(Q(user__isnull=True, role_code__in=roles) | Q(user=user))
    elif roles:
        query = query.filter(user__isnull=True, role_code__in=roles)
    elif user is not None:
        query = query.filter(user=user)
    else:
        return []
    return list(query.only("role_code", "user_id", "item_key", "is_visible"))


def visibility_flags_for(user, roles: set[str] | None = None) -> dict[str, bool]:
    """Resolve role defaults, role overrides, then the user's own overrides."""
    if roles is None:
        roles = set(user.role_codes()) if hasattr(user, "role_codes") else set()
    try:
        rules = _active_rules(roles=roles, user=user)
    except DatabaseError:
        # Keep the existing built-in role defaults usable if the new migration
        # has not been applied yet or the database is temporarily unavailable.
        rules = []

    role_overrides: dict[tuple[str, str], bool] = {}
    user_overrides: dict[str, bool] = {}
    for rule in rules:
        if rule.user_id:
            user_overrides[rule.item_key] = rule.is_visible
        else:
            role_overrides[(rule.role_code, rule.item_key)] = rule.is_visible

    flags: dict[str, bool] = {}
    is_superuser = bool(getattr(user, "is_superuser", False))
    for item in SIDEBAR_ITEMS:
        if is_superuser:
            visible = True
        elif roles:
            visible = any(
                role_overrides.get((role, item["key"]), default_visible(item["key"], role))
                for role in roles
            )
        else:
            visible = item["default_roles"] is None
        flags[item["flag"]] = (
            True if is_superuser and item["key"] == "workspace-perm-manage"
            else user_overrides.get(item["key"], visible)
        )
    return flags


def visible_sidebar_sections(flags: dict[str, bool], roles: set[str]) -> dict[str, bool]:
    """Template booleans for section headings and collapsible groups."""
    teacher = any(flags.get(k, False) for k in (
        "workspace_teacher", "workspace_teacher_attendance",
        "workspace_teacher_report_cards", "workspace_teacher_progress_reports", "leads_teacher_assessments",
    )) or ("teacher" in roles and flags.get("workspace_timetable", False))
    education_timetable = bool(
        flags.get("workspace_timetable", False) and "teacher" not in roles
    )
    education = any(flags.get(k, False) for k in (
        "workspace_persons", "workspace_departments", "workspace_lessons",
        "workspace_courses", "workspace_offerings", "workspace_sessions",
        "workspace_locations", "workspace_enrollments",
    )) or education_timetable
    staff = flags.get("workspace_staff", False)
    organization = any(flags.get(k, False) for k in (
        "workspace_org_chart", "workspace_perm_manage",
    ))
    learner = flags.get("workspace_learner_portal", False)
    is_learner = bool(roles & {"student", "guardian"})
    is_staff = bool(roles & STAFF_MENU_ROLES)
    requests = bool(
        flags.get("submission_picker", False)
        or (flags.get("workspace_requests", False) and (is_staff or not is_learner))
    )
    return {
        "teacher": teacher,
        "education": education,
        "staff": staff,
        "organization": organization,
        "learner": learner,
        "requests": requests,
        "learner_requests": bool(
            flags.get("workspace_requests", False)
            and roles & {"student", "guardian"}
            and not roles & STAFF_MENU_ROLES
            and not flags.get("submission_picker", False)
        ),
        "education_timetable": education_timetable,
    }


def admin_role_payload(role_code: str) -> dict[str, Any]:
    role = Role.all_objects.filter(
        code=role_code, is_active=True, is_deleted=False,
    ).first()
    if role is None:
        raise ValueError("نقش فعال یافت نشد.")
    stored = {
        row.item_key: row.is_visible
        for row in SidebarVisibilityRule.objects.filter(
            role_code=role.code, user__isnull=True, is_deleted=False,
        )
    }
    return {
        "role": {"code": role.code, "name": role.name},
        "items": [
            {
                "key": item["key"],
                "title": item["title"],
                "section": item["section"],
                "default_visible": default_visible(item["key"], role.code),
                "visible": stored.get(item["key"], default_visible(item["key"], role.code)),
                "customized": item["key"] in stored,
            }
            for item in SIDEBAR_ITEMS
        ],
    }


def admin_user_payload(user) -> dict[str, Any]:
    stored = {
        row.item_key: row.is_visible
        for row in SidebarVisibilityRule.objects.filter(
            user=user, is_deleted=False,
        )
    }
    flags = visibility_flags_for(user)
    return {
        "user": {
            "id": str(user.pk),
            "name": " ".join(x for x in (user.first_name, user.last_name) if x) or user.username,
            "roles": sorted(user.role_codes()),
        },
        "items": [
            {
                "key": item["key"],
                "title": item["title"],
                "section": item["section"],
                "override": stored.get(item["key"]),
                "effective_visible": flags[item["flag"]],
            }
            for item in SIDEBAR_ITEMS
        ],
    }


def _validate_rules(rules: Any) -> dict[str, bool | None]:
    if not isinstance(rules, dict):
        raise ValueError("قوانین نمایش باید به‌صورت شیء ارسال شوند.")
    cleaned: dict[str, bool | None] = {}
    for key, value in rules.items():
        if key not in _ITEM_BY_KEY:
            raise ValueError(f"بخش سایدبار نامعتبر است: {key}")
        if value is not None and not isinstance(value, bool):
            raise ValueError(f"مقدار نمایش برای {key} باید true، false یا null باشد.")
        cleaned[key] = value
    return cleaned


@transaction.atomic
def save_role_rules(role_code: str, rules: Any) -> dict[str, Any]:
    role = Role.all_objects.filter(
        code=role_code, is_active=True, is_deleted=False,
    ).first()
    if role is None:
        raise ValueError("نقش فعال یافت نشد.")
    cleaned = _validate_rules(rules)
    existing = {
        row.item_key: row
        for row in SidebarVisibilityRule.objects.filter(
            role_code=role.code, user__isnull=True, is_deleted=False,
        )
    }
    for key, visible in cleaned.items():
        row = existing.get(key)
        if visible is None:
            if row:
                row.soft_delete()
        elif row:
            if row.is_visible != visible:
                row.is_visible = visible
                row.save(update_fields=["is_visible", "updated_at"])
        else:
            SidebarVisibilityRule.objects.create(
                role_code=role.code, item_key=key, is_visible=visible,
            )
    return admin_role_payload(role.code)


@transaction.atomic
def save_user_rules(user, rules: Any) -> dict[str, Any]:
    cleaned = _validate_rules(rules)
    existing = {
        row.item_key: row
        for row in SidebarVisibilityRule.objects.filter(user=user, is_deleted=False)
    }
    for key, visible in cleaned.items():
        row = existing.get(key)
        if visible is None:
            if row:
                row.soft_delete()
        elif row:
            if row.is_visible != visible:
                row.is_visible = visible
                row.save(update_fields=["is_visible", "updated_at"])
        else:
            SidebarVisibilityRule.objects.create(
                user=user, item_key=key, is_visible=visible,
            )
    return admin_user_payload(user)


def admin_catalog_payload() -> dict[str, Any]:
    roles = Role.all_objects.filter(is_active=True, is_deleted=False).order_by("priority", "code")
    return {
        "roles": [{"code": role.code, "name": role.name} for role in roles],
        "items": [
            {"key": item["key"], "title": item["title"], "section": item["section"]}
            for item in SIDEBAR_ITEMS
        ],
    }
