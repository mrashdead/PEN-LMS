"""Enrollment from a qualified lead under the lead management permission."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from rest_framework import generics, serializers

from apps.education.models import CourseOffering
from apps.education.registration_permissions import can_create_free_enrollment
from apps.education.serializers import CourseOfferingSerializer, OfferingEnrollmentSerializer
from apps.education.views import OfferingEnrollmentListCreateView
from apps.leads.models import Lead
from apps.leads.permissions import IsLeadOperator, is_lead_operator


class LeadEnrollmentPage(LoginRequiredMixin, TemplateView):
    template_name = "enrollment.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if not is_lead_operator(request.user):
            raise Http404
        self.lead = get_object_or_404(Lead, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(lead_enrollment=self.lead, can_create_free_enrollment=can_create_free_enrollment(self.request.user))
        return context


class LeadEnrollmentScopeMixin:
    permission_classes = (IsLeadOperator,)

    def get_lead(self):
        if not hasattr(self, "_lead"):
            self._lead = get_object_or_404(Lead, pk=self.kwargs["lead_pk"])
        return self._lead

    def offerings(self):
        lead = self.get_lead()
        qs = CourseOffering.objects.filter(is_active=True, course__is_active=True, course__is_deleted=False,
                                          status__in=[CourseOffering.Status.DRAFT, CourseOffering.Status.OPEN, CourseOffering.Status.RUNNING])
        return qs.filter(course_id=lead.course_id) if lead.course_id else qs


class LeadOfferingListView(LeadEnrollmentScopeMixin, generics.ListAPIView):
    serializer_class = CourseOfferingSerializer
    pagination_class = None

    def get_queryset(self):
        return self.offerings().select_related("course", "instructor", "location")

    def list(self, request, *args, **kwargs):
        from rest_framework.response import Response
        return Response({"results": self.get_serializer(self.get_queryset(), many=True).data})


class LeadOfferingDetailView(LeadEnrollmentScopeMixin, generics.RetrieveAPIView):
    serializer_class = CourseOfferingSerializer

    def get_queryset(self):
        return self.offerings().select_related("course", "instructor", "location")


class LeadFinancialEnrollmentSerializer(OfferingEnrollmentSerializer):
    def validate(self, attrs):
        lead = self.context["lead"]
        if attrs.get("lead") is not None and attrs["lead"].pk != lead.pk:
            raise serializers.ValidationError({"lead": "لید ارسالی با مسیر ثبت‌نام مطابقت ندارد."})
        if not lead.enrolled_person_id or attrs["student"].pk != lead.enrolled_person_id:
            raise serializers.ValidationError({"student": "ابتدا پرونده دانش‌آموز همین لید را ایجاد یا متصل کنید."})
        if not self.context["view"].offerings().filter(pk=attrs["offering"].pk).exists():
            raise serializers.ValidationError({"offering": "برگزاری باید فعال و متعلق به دوره معرفی‌شده باشد."})
        attrs["lead"] = lead
        return super().validate(attrs)


class LeadFinancialEnrollmentView(LeadEnrollmentScopeMixin, OfferingEnrollmentListCreateView):
    serializer_class = LeadFinancialEnrollmentSerializer

    def get_serializer_context(self):
        return {**super().get_serializer_context(), "lead": self.get_lead()}

    def get_queryset(self):
        lead = self.get_lead()
        qs = super().get_queryset().filter(student_id=lead.enrolled_person_id)
        return qs.filter(offering__course_id=lead.course_id) if lead.course_id else qs.none()
