"""One permission decision for the operational registration UI and APIs."""
from apps.core.access_enforcer import acl_strict
from apps.core.crud import roles_for
from rest_framework.permissions import BasePermission

PAGE_KEY = 'workspace-enrollments'
READ_ROLES = {'manager', 'workflow_admin', 'hr', 'supervisor', 'employee', 'teacher', 'student', 'guardian'}
STAFF_ROLES = {'manager', 'workflow_admin', 'hr', 'supervisor', 'employee'}
WRITE_ROLES = {'manager', 'workflow_admin', 'hr'}
MODELS = {'offering': 'education.offeringenrollment', 'class': 'academics.classenrollment'}


def can_access_registrations(user):
    if not user or not user.is_authenticated or not user.is_active or getattr(user, 'is_deleted', False):
        return False
    return acl_strict(user, 'page', PAGE_KEY, 'view', bool(roles_for(user) & READ_ROLES))


def registration_permission(user, source, verb='view'):
    if not can_access_registrations(user) or source not in MODELS:
        return False
    key = MODELS[source]
    app, model = key.split('.')
    baseline = bool(roles_for(user) & (READ_ROLES if verb == 'view' else WRITE_ROLES))
    if verb != 'view':
        baseline = baseline and user.has_perm(f'{app}.{verb}_{model}')
    return acl_strict(user, 'model', key, verb, baseline)


class RegistrationAccess(BasePermission):
    message = 'شما به مدیریت ثبت‌نام‌ها دسترسی ندارید.'

    def has_permission(self, request, view):
        return can_access_registrations(request.user)
