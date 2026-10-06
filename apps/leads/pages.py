from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.utils import timezone
from django.views.generic import TemplateView

from apps.core.utils import jalali_date_str
from apps.leads.permissions import LEAD_OPERATOR_ROLES
from apps.education.models import Course
from apps.leads.selectors import assigned_leads_for_teacher, assessors

class LeadsPage(LoginRequiredMixin, TemplateView):
    template_name = "leads/dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        roles = set(request.user.role_codes()) if hasattr(request.user, "role_codes") else set()
        if not roles & LEAD_OPERATOR_ROLES:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        roles = set(self.request.user.role_codes()) if hasattr(self.request.user, "role_codes") else set()
        now = timezone.localtime()
        next_quarter = ((now.hour * 60 + now.minute) // 15 + 1) * 15
        if next_quarter >= 24 * 60:
            today_min_time = "23:59"
        else:
            today_min_time = f"{next_quarter // 60:02d}:{next_quarter % 60:02d}"
        context.update({
            "lead_assessors": assessors(),
            "lead_courses": Course.objects.filter(is_active=True, is_deleted=False).order_by("title"),
            "lead_can_create": True,
            "today_iso": timezone.localdate().isoformat(),
            "today_jalali": jalali_date_str(timezone.localdate()),
            "today_min_time": today_min_time,
        })
        return context


class LeadTeacherAssessmentsPage(LoginRequiredMixin, TemplateView):
    template_name = "leads/teacher_assessments.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        roles = set(request.user.role_codes()) if hasattr(request.user, "role_codes") else set()
        if "teacher" not in roles:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        leads = assigned_leads_for_teacher(self.request.user)
        context.update({
            "leads": leads[:50],
            "lead_count": leads.count(),
            "lead_pending_count": leads.filter(status__in=[Lead.Status.SENT, "scheduled"]).count(),
            "lead_completed_count": leads.filter(status__in=[Lead.Status.ASSESSED, Lead.Status.RECOMMENDED, Lead.Status.ENROLLED]).count(),
        })
        return context
