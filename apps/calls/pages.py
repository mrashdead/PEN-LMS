from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView

from apps.calls.services import CALL_OPERATOR_ROLES


class CallsDashboardPage(LoginRequiredMixin, TemplateView):
    template_name = "calls/dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if not (request.user.is_superuser or set(request.user.role_codes()) & CALL_OPERATOR_ROLES):
            raise PermissionDenied("شما مجاز به دسترسی به ثبت تماس‌ها نیستید.")
        return super().dispatch(request, *args, **kwargs)
