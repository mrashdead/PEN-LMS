from __future__ import annotations

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.education.models import CourseLesson
from apps.leads.models import Lead
from apps.leads.permissions import IsLeadAssessor, IsLeadOperator, IsLeadTeacher, is_lead_operator
from apps.leads.selectors import assigned_leads_for_teacher, assessors, leads_for_user
from apps.leads.serializers import (
    LeadAssessmentSerializer,
    LeadCreateSerializer,
    LeadEnrollmentSerializer,
    LeadRecommendationSerializer,
    LeadPersonCreateSerializer,
    LeadSerializer,
    TeacherLeadSerializer,
)
from apps.persons.models import Person
from apps.persons.services import DuplicateNationalCodeError, PersonService

person_service = PersonService()


class LeadListCreateView(generics.ListCreateAPIView):
    serializer_class = LeadSerializer
    permission_classes = (IsLeadAssessor,)

    def get_queryset(self):
        qs = leads_for_user(self.request.user)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def create(self, request, *args, **kwargs):
        if not is_lead_operator(request.user):
            return Response({"detail": "فقط کارکنان می‌توانند لید جدید ثبت کنند."}, status=403)
        return super().create(request, *args, **kwargs)

    def get_serializer_class(self):
        return LeadCreateSerializer if self.request.method == "POST" else LeadSerializer

    def perform_create(self, serializer):
        lead = serializer.save(created_by=self.request.user)
        if lead.assessment_date:
            lead.status = Lead.Status.SCHEDULED
            lead.save(update_fields=["status", "updated_at"])


class LeadDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = LeadSerializer
    permission_classes = (IsLeadAssessor,)

    def get_queryset(self):
        return leads_for_user(self.request.user)

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
            assessor_id = request.data.get("assessor")
            person = assessors().filter(pk=assessor_id).first()
            if not person:
                return Response({"detail": "استاد یا مسئول معتبر انتخاب کنید."}, status=400)
            lead.assessor = person
            lead.status = Lead.Status.SENT
            lead.save(update_fields=["assessor", "status", "updated_at"])
        elif action == "assess":
            if not (request.user.role_codes() & {"teacher", "employee", "supervisor", "manager", "hr", "workflow_admin"}):
                return Response({"detail": "دسترسی ثبت ارزیابی ندارید."}, status=403)
            ser = LeadAssessmentSerializer(data=request.data)
            ser.is_valid(raise_exception=True)
            lead.assessment_score = ser.validated_data.get("score")
            lead.assessment_result = ser.validated_data["result"]
            lead.status = Lead.Status.ASSESSED
            lead.save(update_fields=["assessment_score", "assessment_result", "status", "updated_at"])
        elif action == "recommend":
            if not is_lead_operator(request.user):
                return Response({"detail": "معرفی دوره فقط برای کارکنان مجاز است."}, status=403)
            ser = LeadRecommendationSerializer(data=request.data)
            ser.is_valid(raise_exception=True)
            course = ser.validated_data["course"]
            lesson = ser.validated_data.get("lesson")
            if lesson and not CourseLesson.objects.filter(course=course, lesson=lesson).exists():
                return Response({"detail": "درس انتخاب‌شده متعلق به دوره نیست."}, status=400)
            lead.course = course
            lead.lesson = lesson
            lead.recommendation = ser.validated_data.get("recommendation", "")
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
        return Response(LeadSerializer(lead).data)


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
                    student_code=data["student_code"],
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
        return Response({"results": [{"id": str(p.pk), "name": p.display_name, "type": "استاد"} for p in assessors()]})


class TeacherLeadListView(generics.ListAPIView):
    """A teacher-specific queue that cannot expand to the staff lead list."""
    serializer_class = TeacherLeadSerializer
    permission_classes = (IsLeadTeacher,)
    pagination_class = None

    def get_queryset(self):
        qs = assigned_leads_for_teacher(self.request.user)
        status_filter = self.request.query_params.get("status")
        return qs.filter(status=status_filter) if status_filter else qs


class TeacherLeadDetailView(generics.RetrieveAPIView):
    serializer_class = TeacherLeadSerializer
    permission_classes = (IsLeadTeacher,)

    def get_queryset(self):
        return assigned_leads_for_teacher(self.request.user)


class TeacherLeadAssessmentView(APIView):
    permission_classes = (IsLeadTeacher,)

    def post(self, request, pk):
        lead = assigned_leads_for_teacher(request.user).filter(pk=pk).first()
        if not lead:
            return Response({"detail": "این لید به شما تخصیص داده نشده است."}, status=404)
        if lead.status != Lead.Status.SENT:
            return Response({"detail": "این لید در انتظار ثبت تعیین سطح نیست."}, status=400)
        serializer = LeadAssessmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lead.assessment_score = serializer.validated_data.get("score")
        lead.assessment_result = serializer.validated_data["result"]
        lead.status = Lead.Status.ASSESSED
        lead.save(update_fields=("assessment_score", "assessment_result", "status", "updated_at"))
        return Response(TeacherLeadSerializer(lead).data)
