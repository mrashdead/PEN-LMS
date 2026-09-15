"""Context processors for the dashboard shell.

``user_flags`` exposes cheap, render-time role flags the sidebar/topbar use to
show/hide surfaces per role (task-oriented UX: a teacher never sees the org
menu; a student never sees the form builder). This is **presentation only** —
it mirrors the role trios in apps.forms.permissions / apps.messaging.services /
apps.core.permissions so no template ever decides access by itself; the
views/APIs still 403/404. A hidden link is not a security control.
"""
from __future__ import annotations

from apps.forms.permissions import ELEVATED_ROLES
from apps.forms.templatetags.forms_extras import FORMS_URL_NAMES

STAFF_ROLES = {"manager", "workflow_admin", "hr", "employee", "teacher"}

# Sidebar section membership (url_name → which collapsible is active).
EDU_URLS = {
    "workspace-lessons", "workspace-courses", "workspace-offerings",
    "workspace-sessions", "workspace-timetable", "workspace-locations",
    "workspace-enrollments", "workspace-departments",
}
REQ_URLS = FORMS_URL_NAMES | {"workspace-requests", "schema-picker", "submission-create"}


def user_flags(request):
    user = getattr(request, "user", None)
    if user is None or not getattr(user, "is_authenticated", False):
        return {
            "is_schema_admin": False, "is_staff_user": False,
            "is_manager": False, "is_unit_manager": False,
            "is_teacher": False, "is_learner": False,
            "is_sys_admin": False,
            "sidebar_urlname": "", "sidebar_is_forms": False,
            "sidebar_is_edu": False, "sidebar_is_req": False,
        }
    try:
        roles = set(user.role_codes())
    except Exception:
        roles = set()
    urlname = getattr(getattr(request, "resolver_match", None), "url_name", "") or ""
    return {
        "is_schema_admin": bool(roles & ELEVATED_ROLES),
        "is_staff_user": bool(roles & STAFF_ROLES),
        "is_manager": bool(roles & {"manager", "workflow_admin"}),
        "is_unit_manager": bool(roles & {"manager", "workflow_admin", "hr"}),
        "is_sys_admin": bool(roles & {"manager", "workflow_admin"}),
        "is_teacher": bool(roles & {"teacher"}),
        "is_learner": bool(roles & {"student"}),
        "sidebar_urlname": urlname,
        "sidebar_is_forms": urlname in FORMS_URL_NAMES,
        "sidebar_is_edu": urlname in EDU_URLS,
        "sidebar_is_req": urlname in REQ_URLS,
    }
