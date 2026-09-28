"""Context processors for the dashboard shell.

``user_flags`` exposes render-time role flags and stored sidebar visibility
overrides. These control presentation only; the views/APIs still enforce
access independently. A hidden link is not a security control.
"""
from __future__ import annotations

from apps.forms.permissions import ELEVATED_ROLES
from apps.forms.templatetags.forms_extras import FORMS_URL_NAMES
from apps.playhouse.permissions import FINANCE_ROLES, OPERATOR_ROLES
from apps.leads.permissions import LEAD_OPERATOR_ROLES
from apps.reports.permissions import REPORT_ACCESS_ROLES, can_access_capacity_report
from apps.core.sidebar import SIDEBAR_ITEMS, visibility_flags_for, visible_sidebar_sections

STAFF_ROLES = {"manager", "workflow_admin", "hr", "employee", "teacher", "supervisor"}

# Sidebar section membership (url_name → which collapsible is active).
EDU_URLS = {
    "workspace-lessons", "workspace-courses", "workspace-offerings", "workspace-terms",
    "workspace-sessions", "workspace-timetable", "workspace-locations",
    "workspace-enrollments", "workspace-enrollment-directory", "workspace-departments",
}
REQ_URLS = FORMS_URL_NAMES | {"workspace-requests", "schema-picker", "submission-create"}


def user_flags(request):
    user = getattr(request, "user", None)
    if user is None or not getattr(user, "is_authenticated", False):
        sidebar_visibility = {item["flag"]: False for item in SIDEBAR_ITEMS}
        return {
            "is_schema_admin": False, "is_staff_user": False,
            "is_manager": False, "is_unit_manager": False,
            "is_teacher": False, "is_teacher_only": False,
            "is_learner": False,
            "is_sys_admin": False,
            "is_reports_user": False,
            "is_playhouse_user": False,
            "is_playhouse_finance": False,
            "is_leads_user": False,
            "is_lead_operator": False,
            "is_lead_teacher": False,
            "can_change_own_password": False,
            "sidebar_urlname": "", "sidebar_is_forms": False,
            "sidebar_is_edu": False, "sidebar_is_req": False,
            "is_site_admin": False,
            "sidebar_visibility": sidebar_visibility,
            "sidebar_sections": {"teacher": False, "education": False, "organization": False, "learner": False, "requests": False, "learner_requests": False, "education_timetable": False},
        }
    try:
        roles = set(user.role_codes())
    except Exception:
        roles = set()
    urlname = getattr(getattr(request, "resolver_match", None), "url_name", "") or ""
    is_teacher = bool(roles & {"teacher"})
    # A teacher who holds NO management/staff-admin role gets the restricted
    # teacher portal only (dashboard/timetable, attendance, report cards).
    is_teacher_only = is_teacher and not (roles & (ELEVATED_ROLES | {"employee", "supervisor"}))
    sidebar_visibility = visibility_flags_for(user, roles=roles)
    return {
        "is_schema_admin": bool(roles & ELEVATED_ROLES),
        "is_staff_user": bool(roles & STAFF_ROLES),
        "is_manager": bool(roles & {"manager", "workflow_admin"}),
        "is_unit_manager": bool(roles & {"manager", "workflow_admin", "hr"}),
        "is_sys_admin": bool(user.is_superuser or roles & {"manager", "workflow_admin"}),
        "is_reports_user": bool(roles & REPORT_ACCESS_ROLES),
        "can_capacity_report": can_access_capacity_report(user),
        "is_playhouse_user": bool(roles & OPERATOR_ROLES),
        "is_playhouse_finance": bool(roles & FINANCE_ROLES),
        "is_leads_user": bool(roles & (LEAD_OPERATOR_ROLES | {"teacher"})),
        "is_lead_operator": bool(roles & LEAD_OPERATOR_ROLES),
        "is_lead_teacher": "teacher" in roles,
        "can_change_own_password": bool(roles & {"manager", "workflow_admin", "supervisor", "employee"}),
        "is_teacher": is_teacher,
        "is_teacher_only": is_teacher_only,
        # A learner-portal account: a student (own data) or a guardian
        # (their wards' data). Both open /workspace/portal/.
        "is_learner": bool(roles & {"student", "guardian"}),
        "sidebar_urlname": urlname,
        "sidebar_is_forms": urlname in FORMS_URL_NAMES,
        "sidebar_is_edu": urlname in EDU_URLS,
        "sidebar_is_req": urlname in REQ_URLS,
        "is_site_admin": bool(getattr(user, "is_superuser", False)),
        "sidebar_visibility": sidebar_visibility,
        "sidebar_sections": visible_sidebar_sections(sidebar_visibility, roles),
    }
