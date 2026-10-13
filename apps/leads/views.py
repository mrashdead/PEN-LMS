from __future__ import annotations

from django.db.models import Q
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import AuditEvent
from apps.education.models import Course, CourseLesson
from apps.leads.models import Lead, LeadAssessment, LeadRecommendation
from apps.leads.permissions import IsAssignedLeadAssessor, IsLeadAssessor, IsLeadOperator, can_assess_lead, is_lead_operator
from apps.leads.selectors import assigned_leads_for_assessor, assessors, leads_for_user
from apps.leads.serializers import (
    LeadAssessmentSerializer,
    LeadCreateSerializer,
    LeadEnrollmentSerializer,
    LeadRecommendationSerializer,
    LeadPersonCreateSerializer,
    LeadSerializer,
    LeadAssessorSerializer,
)
from apps.persons.models import Person
from apps.persons.services import DuplicateNationalCodeError, PersonService

person_service = PersonService()


class LeadPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class LeadListCreateView(generics.ListCreateAPIView):
    serializer_class = LeadSerializer
    permission_classes = (IsLeadAssessor,)
    pagination_class = LeadPagination

    def get_queryset(self):
        qs = leads_for_user(self.request.user)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            if status_filter == Lead.Status.SENT:
                qs = qs.filter(status__in=[Lead.Status.SENT, "scheduled"])
            else:
                qs = qs.filter(status=status_filter)
        query = self.request.query_params.get("q", "").strip()
        if query:
            qs = qs.filter(
                Q(student_name__icontains=query)
                | Q(phone__icontains=query)
                | Q(code__icontains=query)
            )
        return qs

    def create(self, request, *args, **kwargs):
        if not is_lead_operator(request.user):
            return Response({"detail": "فقط کارکنان می‌توانند لید جدید ثبت کنند."}, status=403)
        return super().create(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return LeadCreateSerializer
        return LeadSerializer if is_lead_operator(self.request.user) else LeadAssessorSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, status=Lead.Status.SENT)


class LeadDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = LeadSerializer
    permission_classes = (IsLeadAssessor,)

    def get_queryset(self):
        return leads_for_user(self.request.user)

    def get_serializer_class(self):
        return LeadSerializer if is_lead_operator(self.request.user) else LeadAssessorSerializer

    def update(self, request, *args, **kwargs):
        if not is_lead_operator(request.user):
            return Response({"detail": "ویرایش لید فقط برای کارکنان مجاز است."}, status=403)
        return super().update(request, *args, **kwargs)


class LeadActionView(APIView):
    permission_classes = (IsLeadAssessor,)

    def post(self, request, pk, action):
        lead = leads_for_user(request.user).filter(pk=pk).first()
        if not lead:
            return Response({"detail": "لید پیدا نشد."}, status=status.HTTP_404_NOT_FOUND)

        if action == "send":
            if not is_lead_operator(request.user):
                return Response({"detail": "ارسال لید فقط برای کارکنان مجاز است."}, status=403)
            if lead.status not in (Lead.Status.NEW, Lead.Status.SENT):
                return Response({"detail": "ارجاع فقط پیش از ثبت نتیجه تعیین سطح امکان‌پذیر است."}, status=400)
            assessor_id = request.data.get("assessor")
            person = assessors().filter(pk=assessor_id).first()
            if not person:
                return Response({"detail": "استاد یا مسئول معتبر انتخاب کنید."}, status=400)
            lead.assessor = person
            lead.status = Lead.Status.SENT
            lead.save(update_fields=["assessor", "status", "updated_at"])
        elif action == "delete":
            if not is_lead_operator(request.user):
                return Response({"detail": "حذف مورد تعیین سطح فقط برای کارکنان مجاز است."}, status=403)
            if lead.status not in (Lead.Status.NEW, Lead.Status.SENT, Lead.Status.LOST, "scheduled"):
                return Response(
                    {"detail": "حذف فقط در مراحل اولیه و پیش از ثبت نتیجه تعیین سطح امکان‌پذیر است."},
                    status=400,
                )
            lead.soft_delete()
            AuditEvent.record(
                kind=AuditEvent.Kind.FIELD_CHANGE,
                summary="حذف نرم مورد تعیین سطح",
                actor=request.user,
                obj=lead,
                request=request,
                metadata={"action": "soft_delete", "resource": "leads.lead", "status": lead.status},
            )
            return Response({"detail": "مورد تعیین سطح حذف شد.", "id": str(lead.pk)})
        elif action == "assess":
            if not can_assess_lead(request.user, lead):
                return Response({"detail": "فقط ارزیاب تخصیص‌یافته می‌تواند نتیجه را ثبت کند."}, status=403)
            if lead.status not in (Lead.Status.SENT, "scheduled"):
                return Response({"detail": "این مورد در انتظار تعیین سطح نیست."}, status=400)
            ser = LeadAssessmentSerializer(data=request.data)
            ser.is_valid(raise_exception=True)
            assessment = LeadAssessment.objects.create(lead=lead, assessor=lead.assessor, recorded_by=request.user, result=ser.validated_data["result"])
            lead.assessment_result = assessment.result
            lead.status = Lead.Status.ASSESSED
            lead.save(update_fields=["assessment_result", "status", "updated_at"])
        elif action == "recommend":
            if not can_assess_lead(request.user, lead):
                return Response({"detail": "معرفی دوره فقط برای ارزیاب تخصیص‌یافته مجاز است."}, status=403)
            if lead.status not in (Lead.Status.ASSESSED, Lead.Status.RECOMMENDED):
                return Response({"detail": "ابتدا باید تعیین سطح ثبت شود."}, status=400)
            latest_assessment = lead.assessments.order_by("-created_at", "-pk").first()
            if not latest_assessment:
                return Response({"detail": "ابتدا نتیجه تعیین سطح را ثبت کنید."}, status=400)
            ser = LeadRecommendationSerializer(data=request.data)
            ser.is_valid(raise_exception=True)
            course = ser.validated_data["course"]
            lesson = ser.validated_data.get("lesson")
            if lesson and not CourseLesson.objects.filter(course=course, lesson=lesson).exists():
                return Response({"detail": "درس انتخاب‌شده متعلق به دوره نیست."}, status=400)
            note = ser.validated_data.get("recommendation", "")
            LeadRecommendation.objects.create(lead=lead, assessment=latest_assessment, assessor=lead.assessor, recorded_by=request.user, course=course, lesson=lesson, note=note)
            lead.course = course
            lead.lesson = lesson
            lead.recommendation = note
            lead.status = Lead.Status.RECOMMENDED
            lead.save(update_fields=["course", "lesson", "recommendation", "status", "updated_at"])
        elif action == "enroll":
            if not is_lead_operator(request.user):
                return Response({"detail": "تکمیل ثبت‌نام فقط برای کارکنان مجاز است."}, status=403)
            ser = LeadEnrollmentSerializer(data=request.data)
            ser.is_valid(raise_exception=True)
            lead.enrolled_person = ser.validated_data["enrolled_person"]
            lead.status = Lead.Status.ENROLLED
            lead.save(update_fields=["enrolled_person", "status", "updated_at"])
        elif action == "archive":
            if not is_lead_operator(request.user):
                return Response({"detail": "بایگانی لید فقط برای کارکنان مجاز است."}, status=403)
            lead.status = Lead.Status.LOST
            lead.save(update_fields=["status", "updated_at"])
        else:
            return Response({"detail": "عملیات نامعتبر است."}, status=400)
        serializer_class = LeadSerializer if is_lead_operator(request.user) else LeadAssessorSerializer
        return Response(serializer_class(lead).data)


class LeadPersonCreateView(APIView):
    """Create or link the student Person that will be used by enrollment."""
    permission_classes = (IsLeadOperator,)

    def post(self, request, pk):
        lead = leads_for_user(request.user).filter(pk=pk).first()
        if not lead:
            return Response({"detail": "لید پیدا نشد."}, status=404)
        if lead.enrolled_person_id:
            return Response({
                "person_id": str(lead.enrolled_person_id),
                "person_name": lead.enrolled_person.display_name,
                "already_linked": True,
            })
        if lead.status not in (Lead.Status.RECOMMENDED, Lead.Status.ASSESSED):
            return Response({"detail": "ابتدا تعیین سطح و معرفی دوره را تکمیل کنید."}, status=400)

        serializer = LeadPersonCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        existing = Person.objects.filter(
            national_code=data["national_code"],
            person_type=Person.Type.STUDENT,
            is_active=True,
            is_deleted=False,
        ).first()
        if existing:
            person = existing
        else:
            words = " ".join((lead.student_name or "").split()).split(" ", 1)
            try:
                person = person_service.create_person(
                    national_code=data["national_code"],
                    first_name=words[0] if words else lead.student_name,
                    last_name=words[1] if len(words) > 1 else "",
                    person_type=Person.Type.STUDENT,
                    mobile=lead.phone,
                    father_name=data.get("father_name", ""),
                    address=lead.neighborhood,
                    registered_by=request.user,
                    auto_create_user=False,
                )
            except DuplicateNationalCodeError as exc:
                return Response({"national_code": [str(exc)]}, status=400)

        lead.enrolled_person = person
        lead.save(update_fields=["enrolled_person", "updated_at"])
        return Response({
            "person_id": str(person.pk),
            "person_name": person.display_name,
            "already_linked": False,
        }, status=201)


class LeadAssessorListView(APIView):
    permission_classes = (IsLeadOperator,)

    def get(self, request):
        return Response({"results": [{"id": str(p.pk), "name": p.display_name, "type": "ارزیاب"} for p in assessors()]})


class LeadCourseListView(APIView):
    """Course choices for placement, without granting access to education administration."""
    permission_classes = (IsLeadAssessor,)

    def get(self, request):
        courses = Course.objects.filter(is_active=True, is_deleted=False).prefetch_related("course_lessons__lesson").order_by("title")
        return Response({"results": [
            {"id": str(course.pk), "title": course.title, "lesson_titles": [
                {"id": str(link.lesson_id), "title": link.lesson.title}
                for link in course.course_lessons.all()
                if link.lesson.is_active and not link.lesson.is_deleted
            ]}
            for course in courses
        ]})


class LeadAssessorQueueView(generics.ListAPIView):
    """The assessor's own assigned lead queue, independent of teaching roles."""
    serializer_class = LeadAssessorSerializer
    permission_classes = (IsAssignedLeadAssessor,)
    pagination_class = None

    def get_queryset(self):
        qs = assigned_leads_for_assessor(self.request.user)
        status_filter = self.request.query_params.get("status")
        return qs.filter(status=status_filter) if status_filter else qs


class LeadAssessorDetailView(generics.RetrieveAPIView):
    serializer_class = LeadAssessorSerializer
    permission_classes = (IsAssignedLeadAssessor,)

    def get_queryset(self):
        return assigned_leads_for_assessor(self.request.user)


class LeadAssessorResultView(APIView):
    permission_classes = (IsAssignedLeadAssessor,)

    def post(self, request, pk):
        lead = assigned_leads_for_assessor(request.user).filter(pk=pk).first()
        if not lead:
            return Response({"detail": "این لید به شما تخصیص داده نشده است."}, status=404)
        if lead.status not in (Lead.Status.SENT, "scheduled"):
            return Response({"detail": "این لید در انتظار ثبت تعیین سطح نیست."}, status=400)
        serializer = LeadAssessmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assessment = LeadAssessment.objects.create(lead=lead, assessor=lead.assessor, recorded_by=request.user, result=serializer.validated_data["result"])
        lead.assessment_result = assessment.result
        lead.status = Lead.Status.ASSESSED
        lead.save(update_fields=("assessment_result", "status", "updated_at"))
        return Response(LeadAssessorSerializer(lead).data)
