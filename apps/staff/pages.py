from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView


class StaffDashboardPage(LoginRequiredMixin, TemplateView):
    template_name = "staff/dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        roles = set(request.user.role_codes()) if request.user.is_authenticated else set()
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if not (request.user.is_superuser or roles & {
            "employee", "teacher", "supervisor", "manager", "workflow_admin", "hr",
        }):
            raise PermissionDenied("این بخش فقط برای کارکنان قابل دسترسی است.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["staff_is_reviewer"] = bool(
            self.request.user.is_superuser
            or set(self.request.user.role_codes()) & {"manager", "workflow_admin", "hr", "supervisor"}
        )
        return context
