"""
Education API — CRUD for the typed domain tables + transactional endpoints.

  /api/education/departments/           GET/POST
  /api/education/locations/             GET/POST
  /api/education/lessons/               GET/POST
  /api/education/lessons/{id}/          GET/PATCH
  /api/education/courses/               GET/POST
  /api/education/courses/{id}/          GET/PATCH
  /api/education/offerings/             GET/POST
  /api/education/offerings/{id}/        GET/PATCH
  /api/education/offerings/{id}/enroll/ POST   (capacity under row lock)
  /api/education/sessions/              GET/POST (conflict-checked via service)
  /api/education/sessions/{id}/         GET/PATCH
  /api/education/sessions/{id}/attendance/  POST (bulk, idempotent)

Reads: academic staff (teacher/employee included). Writes: managers.
Attendance/grade writes: teacher-of-class OR manager (object check on session).
"""
from __future__ import annotations

import datetime as dt
import json
import urllib.request

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.group_permissions import StrictDjangoModelPermissions
from apps.core.crud_views import SoftDeleteView, SoftRestoreView
from apps.core.permissions import (
    IsAcademicManager,
    IsActiveUser,
    IsManagerOrAdmin,
    IsTeacherPortalUser,
    ResourceCRUDPermission,
)
from apps.core.utils import persian_date
from apps.academics.scoping import (
    education_courses_visible_to,
    education_offerings_visible_to,
    education_sessions_visible_to,
)
from apps.education.models import (
    AcademicHoliday,
    AttendanceRecord,
    ClassSession,
    Course,
    CourseOffering,
    Department,
    EnrollmentWaitlist,
    EnrollmentRefund,
    Lesson,
    Location,
    OfferingEnrollment,
    ParentReportDelivery,
    SessionMaterial,
)
from apps.leads.models import Lead
from apps.education.calendar import student_schedule
from apps.education.serializers import (
    AcademicHolidaySerializer,
    AttendanceRecordSerializer,
    ClassSessionSerializer,
    CourseOfferingSerializer,
    CourseSerializer,
    DepartmentSerializer,
    LessonSerializer,
    LocationSerializer,
    OfferingEnrollmentSerializer,
    EnrollmentWaitlistSerializer,
    SessionMaterialSerializer,
)
from apps.education.services import (
    CapacityExceededError,
    EducationServiceError,
    bulk_attendance,
    create_offering_enrollment,
    convert_offering_enrollment_to_class,
    process_enrollment_refund,
    request_enrollment_refund,
    create_session,
    enroll_student,
    generate_sessions,
    update_session,
    learner_attendance_summary,
    learner_report_cards,
    learner_students,
    place_on_waitlist,
    promote_next_waitlist,
    withdraw_student,
    record_session_attendance,
    roster_students,
    save_report_cards,
    teacher_classes,
    teacher_report_cards,
    _resolve_learner_person,
)
from apps.persons.models import Person, StudentGuardian


def _student_of(request):
    return getattr(request.user, "person", None)


# IsAcademicManager already encodes "reads for academic staff, writes for
# managers" at the class level; each view keeps that pair plus the model-perm
# layer. No per-method branching is needed.

class DepartmentListCreateView(generics.ListCreateAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, IsAcademicManager)


class DepartmentDetailView(generics.RetrieveUpdateAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, IsAcademicManager, ResourceCRUDPermission)


class DepartmentSoftDeleteView(SoftDeleteView):
    queryset = Department.objects.all()
    resource_key = "departments"


class DepartmentRestoreView(SoftRestoreView):
    queryset = Department.all_objects.all()
    resource_key = "departments"


class LocationListCreateView(generics.ListCreateAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, IsAcademicManager)


class LocationDetailView(generics.RetrieveUpdateAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, IsAcademicManager, ResourceCRUDPermission)


class LocationSoftDeleteView(SoftDeleteView):
    queryset = Location.objects.all()
    resource_key = "locations"


class LocationRestoreView(SoftRestoreView):
    queryset = Location.all_objects.all()
    resource_key = "locations"


class HolidayListCreateView(generics.ListCreateAPIView):
    """
    GET/POST /api/education/holidays/ — تقویم تعطیلات (منبع پرشِ موتور جلسات).

    GET فیلترهای اختیاری: ?from=YYYY-MM-DD&to=YYYY-MM-DD&scope=official|weekly|
    institute&location=<id>&active=true. خواندن برای کارکنان آموزشی آزاد است
    (تقویم باید تعطیلی را نشانشان دهد)، نوشتن فقط مدیر.
    """

    queryset = AcademicHoliday.objects.select_related("location").all()
    serializer_class = AcademicHolidaySerializer
    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, IsAcademicManager)

    def get_queryset(self):
        qs = super().get_queryset().order_by("date_from", "scope")
        p = self.request.query_params
        date_from = (p.get("from") or "").strip()
        date_to = (p.get("to") or "").strip()
        if date_from:
            # Overlap: anything whose range reaches into the window, plus all
            # weekly rules (they repeat regardless of the stored single date).
            qs = qs.filter(
                models.Q(scope=AcademicHoliday.Scope.WEEKLY)
                | models.Q(date_to__gte=date_from)
            )
        if date_to:
            qs = qs.filter(
                models.Q(scope=AcademicHoliday.Scope.WEEKLY)
                | models.Q(date_from__lte=date_to)
            )
        scope = (p.get("scope") or "").strip()
        if scope:
            qs = qs.filter(scope=scope)
        location = (p.get("location") or "").strip()
        if location:
            qs = qs.filter(location_id=location)
        active = p.get("active")
        if active is not None:
            qs = qs.filter(is_active=active.lower() in {"1", "true", "yes"})
        return qs


class HolidayDetailView(generics.RetrieveUpdateAPIView):
    queryset = AcademicHoliday.objects.select_related("location").all()
    serializer_class = AcademicHolidaySerializer
    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, IsAcademicManager, ResourceCRUDPermission)


class HolidaySoftDeleteView(SoftDeleteView):
    queryset = AcademicHoliday.objects.all()
    resource_key = "holidays"


class HolidayRestoreView(SoftRestoreView):
    queryset = AcademicHoliday.all_objects.all()
    resource_key = "holidays"


class LessonListCreateView(generics.ListCreateAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, IsAcademicManager)


class LessonDetailView(generics.RetrieveUpdateAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, IsAcademicManager, ResourceCRUDPermission)


class LessonSoftDeleteView(SoftDeleteView):
    queryset = Lesson.objects.all()
    resource_key = "lessons"


class LessonRestoreView(SoftRestoreView):
    queryset = Lesson.all_objects.all()
    resource_key = "lessons"


class CourseListCreateView(generics.ListCreateAPIView):
    serializer_class = CourseSerializer
    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, IsAcademicManager)

    def get_queryset(self):
        # «درس‌ها» از ردیف‌های زندهٔ CourseLesson خوانده می‌شود (lesson_links)،
        # نه از مدیر M2M که لینک‌های soft-deleted را هم برمی‌گرداند.
        return education_courses_visible_to(self.request.user).prefetch_related(
            "course_lessons__lesson"
        )


class CourseDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = CourseSerializer
    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, IsAcademicManager, ResourceCRUDPermission)

    def get_queryset(self):
        return education_courses_visible_to(self.request.user).prefetch_related(
            "course_lessons__lesson"
        )


class CourseSoftDeleteView(SoftDeleteView):
    queryset = Course.objects.all()
    resource_key = "courses"


class CourseRestoreView(SoftRestoreView):
    queryset = Course.all_objects.all()
    resource_key = "courses"


class OfferingListCreateView(generics.ListCreateAPIView):
    serializer_class = CourseOfferingSerializer
    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, IsAcademicManager)

    def get_queryset(self):
        return education_offerings_visible_to(self.request.user)


class OfferingDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = CourseOfferingSerializer
    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, IsAcademicManager, ResourceCRUDPermission)

    def get_queryset(self):
        return education_offerings_visible_to(self.request.user)


class OfferingSoftDeleteView(SoftDeleteView):
    queryset = CourseOffering.objects.all()
    resource_key = "offerings"


class OfferingRestoreView(SoftRestoreView):
    queryset = CourseOffering.all_objects.all()
    resource_key = "offerings"


class OfferingGenerateSessionsView(APIView):
    """POST /offerings/{id}/generate-sessions/ — materialize the recurrence
    rule into real sessions (conflict-checked, holiday-aware).

    NOTE: kept for the offering-level (no class code) flow. The class-
    formation form (§2) uses POST /class-formation/ instead, which threads
    class_code/lesson/teacher/location overrides through the same engine.

    Body (all optional):
      {"count": 20,        # EXACT number of sessions (else total_sessions,
                           #   else legacy hours-distribution mode)
       "weeks": 12,        # hours-mode horizon
       "regenerate": true, # soft-delete this offering's future SCHEDULED
                           #   sessions first (idempotent wizard re-run)
       "strict": false}    # true → any room/teacher collision aborts with 400
                           #   instead of pushing the slot a week forward
    """

    # NOTE: NO StrictDjangoModelPermissions — queryset-less APIView makes that
    # class raise ImproperlyConfigured (→ HTTP 500) inside DRF's
    # get_required_permissions (the §13-7 reports pitfall, found here too).
    # The role gate + the offering lookup below are the authority.
    permission_classes = (IsActiveUser, IsManagerOrAdmin)

    def post(self, request, pk):
        offering = CourseOffering.objects.filter(pk=pk).first()
        if offering is None:
            return Response({"error": "برگزاری یافت نشد."}, status=status.HTTP_404_NOT_FOUND)

        def _int(name):
            raw = request.data.get(name)
            try:
                return int(raw) if raw not in (None, "") else None
            except (TypeError, ValueError):
                raise ValueError(name)

        try:
            weeks = _int("weeks")
            count = _int("count")
        except ValueError as exc:
            return Response(
                {str(exc): "باید عدد صحیح باشد."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if count is not None and count <= 0:
            return Response(
                {"count": "تعداد جلسات باید بزرگ‌تر از صفر باشد."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        regenerate = str(request.data.get("regenerate") or "").lower() in {"1", "true", "yes"}
        strict = str(request.data.get("strict") or "").lower() in {"1", "true", "yes"}
        try:
            result = generate_sessions(
                offering=offering, actor=request.user,
                weeks=weeks, count=count, regenerate=regenerate, strict=strict,
            )
        except EducationServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_200_OK)


class OfferingEnrollView(APIView):
    """POST /offerings/{id}/enroll/ — capacity enforced under a row lock (B4)."""

    # Queryset-less APIView again: StrictDjangoModelPermissions would 500
    # inside DRF here too. IsManagerOrAdmin is the authority (same trio the
    # class was already carrying).
    permission_classes = (IsActiveUser, IsManagerOrAdmin)

    def post(self, request, pk):
        offering = CourseOffering.objects.filter(pk=pk).first()
        if offering is None:
            return Response({"error": "برگزاری یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        student_id = request.data.get("student")
        if not student_id:
            return Response({"student": "الزامی است."}, status=status.HTTP_400_BAD_REQUEST)
        student = Person.objects.filter(
            pk=student_id, person_type=Person.Type.STUDENT,
            is_active=True, is_deleted=False,
        ).first()
        if student is None:
            return Response({"student": "دانش‌آموز فعال یافت نشد."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            enroll_student(offering=offering, student=student, actor=request.user)
        except CapacityExceededError:
            entry = place_on_waitlist(offering=offering, student=student, actor=request.user)
            return Response({
                "waitlisted": True,
                "waitlist_id": str(entry.pk),
                "message": "ظرفیت تکمیل است؛ دانش‌آموز در صف انتظار قرار گرفت.",
            }, status=status.HTTP_202_ACCEPTED)
        except EducationServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            CourseOfferingSerializer(offering, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )


class OfferingEnrollmentListCreateView(generics.ListCreateAPIView):
    """GET/POST /enrollments/ — financial enrollment (amount/discount/payment/cheque).

    Creating an enrollment also bumps the offering's capacity counter through
    the same row-locked service, so seats and the money record stay consistent.
    """

    serializer_class = OfferingEnrollmentSerializer
    permission_classes = (IsActiveUser, IsManagerOrAdmin, StrictDjangoModelPermissions)

    def get_queryset(self):
        qs = OfferingEnrollment.objects.filter(is_deleted=False).select_related(
            "offering", "offering__course", "student"
        )
        offering = self.request.query_params.get("offering")
        if offering:
            qs = qs.filter(offering_id=offering)
        student = self.request.query_params.get("student")
        if student:
            qs = qs.filter(student_id=student)
        return qs.order_by("-created_at")

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        offering = serializer.validated_data["offering"]
        student = serializer.validated_data["student"]
        lead = serializer.validated_data.get("lead")
        try:
            enrollment = create_offering_enrollment(
                offering=offering,
                student=student,
                actor=request.user,
                course_amount=serializer.validated_data.get("course_amount"),
                discount_type=serializer.validated_data.get("discount_type", OfferingEnrollment.DiscountType.NONE),
                discount_value=serializer.validated_data.get("discount_value", 0),
                payment_method=serializer.validated_data.get("payment_method", OfferingEnrollment.PaymentMethod.CASH),
                cheque_count=serializer.validated_data.get("cheque_count", 0),
                cheques=serializer.validated_data.get("cheques") or [],
                reference=serializer.validated_data.get("reference", ""),
                enrolled_at=serializer.validated_data.get("enrolled_at"),
            )
        except CapacityExceededError:
            entry = place_on_waitlist(offering=offering, student=student, actor=request.user)
            return Response({
                "waitlisted": True,
                "waitlist_id": str(entry.pk),
                "message": "ظرفیت تکمیل است؛ دانش‌آموز در صف انتظار قرار گرفت.",
            }, status=status.HTTP_202_ACCEPTED)
        except EducationServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        if lead is not None:
            lead.enrolled_person = student
            lead.status = Lead.Status.ENROLLED
            lead.save(update_fields=["enrolled_person", "status", "updated_at"])
        return Response(self.get_serializer(enrollment).data, status=status.HTTP_201_CREATED)


class OfferingEnrollmentDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = OfferingEnrollmentSerializer
    permission_classes = (IsActiveUser, IsManagerOrAdmin, StrictDjangoModelPermissions, ResourceCRUDPermission)
    queryset = OfferingEnrollment.objects.filter(is_deleted=False).select_related(
        "offering", "offering__course", "student"
    )


class OfferingEnrollmentConvertToClassView(APIView):
    """Create the final ClassEnrollment after a class group is formed."""

    permission_classes = (IsActiveUser, IsManagerOrAdmin)

    def post(self, request, pk):
        enrollment = OfferingEnrollment.objects.filter(pk=pk, is_deleted=False).first()
        if enrollment is None:
            return Response({"error": "ثبت‌نام یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        from apps.academics.models import ClassGroup

        class_group = ClassGroup.objects.filter(
            pk=request.data.get("class_group"), is_deleted=False,
        ).first()
        if class_group is None:
            return Response({"class_group": "کلاس معتبر یافت نشد."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            membership = convert_offering_enrollment_to_class(
                enrollment=enrollment,
                class_group=class_group,
                actor=request.user,
            )
        except EducationServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "offering_enrollment": str(enrollment.pk),
            "class_enrollment": str(membership.pk),
        }, status=status.HTTP_200_OK)


class OfferingEnrollmentRefundView(APIView):
    permission_classes = (IsActiveUser, IsManagerOrAdmin)

    def post(self, request, pk):
        enrollment = OfferingEnrollment.objects.filter(pk=pk, is_deleted=False).first()
        if enrollment is None:
            return Response({"error": "ثبت‌نام یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        try:
            refund = request_enrollment_refund(
                enrollment=enrollment,
                amount=request.data.get("amount"),
                requested_by=request.user,
                reason=request.data.get("reason", ""),
            )
        except (EducationServiceError, TypeError, ValueError) as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(EnrollmentRefundSerializer(refund).data, status=status.HTTP_201_CREATED)


class EnrollmentRefundProcessView(APIView):
    permission_classes = (IsActiveUser, IsManagerOrAdmin)

    def post(self, request, pk):
        refund = EnrollmentRefund.objects.filter(pk=pk, is_deleted=False).first()
        if refund is None:
            return Response({"error": "درخواست عودت یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        try:
            refund = process_enrollment_refund(
                refund=refund,
                processor=request.user,
                reference=request.data.get("reference", ""),
            )
        except EducationServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(EnrollmentRefundSerializer(refund).data)


class EnrollmentSoftDeleteView(SoftDeleteView):
    queryset = OfferingEnrollment.objects.all()
    resource_key = "enrollments"

    def post(self, request, *args, **kwargs):
        enrollment = self.get_object()
        was_live = not enrollment.is_deleted
        response = super().post(request, *args, **kwargs)
        if was_live and response.status_code < 300:
            withdraw_student(offering=enrollment.offering, actor=request.user)
        return response


class EnrollmentRestoreView(SoftRestoreView):
    queryset = OfferingEnrollment.all_objects.all()
    resource_key = "enrollments"


class WaitlistListCreateView(generics.ListCreateAPIView):
    """GET/POST /waitlist/ — FIFO queue for full offerings."""

    serializer_class = EnrollmentWaitlistSerializer
    permission_classes = (IsActiveUser, IsManagerOrAdmin)

    def get_queryset(self):
        qs = EnrollmentWaitlist.objects.filter(is_deleted=False).select_related(
            "offering", "offering__course", "student"
        )
        offering = self.request.query_params.get("offering")
        if offering:
            qs = qs.filter(offering_id=offering)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs.order_by("requested_at", "created_at")

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        entry = place_on_waitlist(
            offering=serializer.validated_data["offering"],
            student=serializer.validated_data["student"],
            actor=request.user,
        )
        return Response(self.get_serializer(entry).data, status=status.HTTP_201_CREATED)


class WaitlistOfferView(APIView):
    """POST /waitlist/<offering>/offer-next/ — manually trigger FIFO offer."""

    permission_classes = (IsActiveUser, IsManagerOrAdmin)

    def post(self, request, pk):
        offering = CourseOffering.objects.filter(pk=pk, is_deleted=False).first()
        if offering is None:
            return Response({"detail": "برگزاری یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        entry = promote_next_waitlist(offering=offering, actor=request.user)
        if entry is None:
            return Response({"offered": False, "message": "صف انتظاری برای این برگزاری وجود ندارد یا ظرفیت آزاد نیست."})
        return Response({"offered": True, "entry": EnrollmentWaitlistSerializer(entry).data})


class SessionMaterialListCreateView(APIView):
    """GET/POST /sessions/<id>/materials/ — topics and teaching attachments."""

    permission_classes = (IsActiveUser,)

    def _session(self, request, pk):
        session = ClassSession.objects.filter(pk=pk, is_deleted=False).select_related(
            "offering", "teacher", "location"
        ).first()
        if session is None:
            return None
        roles = set(request.user.role_codes())
        if roles & {"manager", "workflow_admin", "hr"}:
            return session
        if education_sessions_visible_to(request.user).filter(pk=pk).exists():
            return session
        return None

    def get(self, request, pk):
        session = self._session(request, pk)
        if session is None:
            return Response({"detail": "جلسه یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        rows = SessionMaterial.objects.filter(session=session, is_deleted=False).order_by("sort_order", "created_at")
        return Response({
            "topic": session.topic,
            "schedule_version": session.schedule_revisions.filter(is_deleted=False).count() + 1,
            "materials": SessionMaterialSerializer(rows, many=True, context={"request": request}).data,
        })

    def post(self, request, pk):
        session = self._session(request, pk)
        if session is None:
            return Response({"detail": "جلسه یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        roles = set(request.user.role_codes())
        person = _student_of(request)
        if not (roles & {"manager", "workflow_admin", "hr"}) and (
            person is None or session.teacher_id != person.pk
        ):
            return Response({"detail": "فقط مدرس این جلسه یا مدیر می‌تواند ضمیمه اضافه کند."}, status=status.HTTP_403_FORBIDDEN)
        serializer = SessionMaterialSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        material = serializer.save(session=session)
        return Response(SessionMaterialSerializer(material, context={"request": request}).data, status=status.HTTP_201_CREATED)

    def patch(self, request, pk):
        session = self._session(request, pk)
        if session is None:
            return Response({"detail": "جلسه یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        roles = set(request.user.role_codes())
        person = _student_of(request)
        if not (roles & {"manager", "workflow_admin", "hr"}) and (
            person is None or session.teacher_id != person.pk
        ):
            return Response({"detail": "فقط مدرس این جلسه یا مدیر می‌تواند برنامه را ویرایش کند."}, status=status.HTTP_403_FORBIDDEN)
        topic = str((request.data or {}).get("topic") or "").strip()
        try:
            update_session(session=session, actor=request.user, topic=topic)
        except EducationServiceError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return self.get(request, pk)


class SessionMaterialDetailView(APIView):
    permission_classes = (IsActiveUser,)

    def post(self, request, pk):
        material = SessionMaterial.objects.filter(pk=pk, is_deleted=False).select_related("session").first()
        if material is None:
            return Response({"detail": "ضمیمه یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        roles = set(request.user.role_codes())
        person = _student_of(request)
        if not (roles & {"manager", "workflow_admin", "hr"}) and (
            person is None or material.session.teacher_id != person.pk
        ):
            return Response({"detail": "دسترسی حذف این ضمیمه را ندارید."}, status=status.HTTP_403_FORBIDDEN)
        material.soft_delete()
        return Response({"detail": "ضمیمه حذف شد.", "id": str(material.pk)})


def _report_student_and_guardian(request):
    student_id = (
        request.query_params.get("student")
        or (request.data.get("student") if hasattr(request, "data") else "")
        or ""
    ).strip() or None
    person = _resolve_learner_person(request.user, student_id)
    if person is None:
        return None, None
    link = (
        StudentGuardian.objects.filter(
            student=person, is_active=True, is_deleted=False,
        ).select_related("guardian").order_by("-guardian__is_active", "guardian__last_name").first()
    )
    guardian = link.guardian if link else None
    return person, guardian


def _send_report_sms(*, phone: str, student, attendance: dict, report_cards: list[dict]) -> None:
    from django.conf import settings

    gateway = getattr(settings, "SMS_GATEWAY_URL", "")
    if not gateway:
        raise RuntimeError("درگاه پیامک در تنظیمات سامانه فعال نشده است.")
    message = (
        f"گزارش {student.first_name} {student.last_name}: "
        f"حضور {attendance.get('rate', 0)}٪، "
        f"جلسات {attendance.get('all', 0)}، "
        f"کارنامه صادرشده {len(report_cards)} مورد."
    )
    payload = json.dumps({
        "to": phone, "message": message,
        "from": getattr(settings, "SMS_SENDER", ""),
    }).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    token = getattr(settings, "SMS_GATEWAY_TOKEN", "")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(gateway, data=payload, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=10) as response:
        if response.status >= 300:
            raise RuntimeError(f"درگاه پیامک پاسخ {response.status} داد.")


class LearnerReportCardDeliveryView(APIView):
    """PDF download and parent SMS action for the learner report."""

    permission_classes = (IsActiveUser,)

    def get(self, request):
        person, _guardian = _report_student_and_guardian(request)
        if person is None:
            return Response({"detail": "گزارش این دانش‌آموز برای شما قابل مشاهده نیست."}, status=status.HTTP_403_FORBIDDEN)
        attendance = learner_attendance_summary(request.user, student=person)
        cards = learner_report_cards(request.user, student=person)
        if request.query_params.get("format") != "pdf":
            return Response({"student": person.display_name, "attendance": attendance, "report_cards": cards})
        from apps.education.report_pdf import build_learner_report_pdf

        try:
            content = build_learner_report_pdf(student=person, attendance=attendance, report_cards=cards)
        except ImportError:
            return Response({"detail": "کتابخانهٔ تولید PDF روی سرور نصب نشده است."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        ParentReportDelivery.objects.create(
            student=person, requested_by=request.user,
            channel=ParentReportDelivery.Channel.PDF,
            status=ParentReportDelivery.Status.SENT,
            recipient="download",
            sent_at=timezone.now(),
        )
        response = HttpResponse(content, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="learner-report-{person.student_code or person.pk}.pdf"'
        return response

    def post(self, request):
        person, guardian = _report_student_and_guardian(request)
        if person is None:
            return Response({"detail": "گزارش این دانش‌آموز برای شما قابل مشاهده نیست."}, status=status.HTTP_403_FORBIDDEN)
        phone = (guardian.mobile if guardian else "") or ""
        if not phone:
            return Response({"detail": "برای این دانش‌آموز شمارهٔ همراه ولی ثبت نشده است."}, status=status.HTTP_400_BAD_REQUEST)
        attendance = learner_attendance_summary(request.user, student=person)
        cards = learner_report_cards(request.user, student=person)
        delivery = ParentReportDelivery.objects.create(
            student=person, requested_by=request.user,
            channel=ParentReportDelivery.Channel.SMS,
            recipient=phone,
        )
        try:
            _send_report_sms(phone=phone, student=person, attendance=attendance, report_cards=cards)
        except Exception as exc:
            delivery.status = ParentReportDelivery.Status.FAILED
            delivery.error = str(exc)[:2000]
            delivery.save(update_fields=["status", "error", "updated_at"])
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        delivery.status = ParentReportDelivery.Status.SENT
        delivery.sent_at = timezone.now()
        delivery.save(update_fields=["status", "sent_at", "updated_at"])
        return Response({"sent": True, "message": "گزارش برای ولی پیامک شد."})


class SessionListCreateView(generics.ListCreateAPIView):
    serializer_class = ClassSessionSerializer
    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, IsAcademicManager)

    def get_queryset(self):
        # DataScope (criterion §13-2): shared service-level scoping replaces
        # the previous ad-hoc teacher-only filter.
        qs = education_sessions_visible_to(self.request.user)
        offering_id = self.request.query_params.get("offering")
        if offering_id:
            qs = qs.filter(offering_id=offering_id)
        date = self.request.query_params.get("date")
        if date:
            try:
                from apps.core.utils import english_numbers
                date_clean = english_numbers(date.strip())
                if '/' in date_clean:
                    import jdatetime
                    parsed = jdatetime.datetime.strptime(date_clean, "%Y/%m/%d").date().togregorian()
                elif '-' in date_clean:
                    import datetime as _dt
                    parsed = _dt.date.fromisoformat(date_clean)
                else:
                    parsed = None
                if parsed is None:
                    raise ValueError("Invalid date format")
                qs = qs.filter(session_date=parsed)
            except (ValueError, TypeError):
                qs = qs.none()
        class_code = self.request.query_params.get("class_code")
        if class_code:
            qs = qs.filter(class_code__icontains=class_code.strip())
        status_value = self.request.query_params.get("status")
        if status_value:
            qs = qs.filter(status=status_value)
        search = self.request.query_params.get("search")
        if search:
            search = search.strip()
            qs = qs.filter(
                models.Q(class_code__icontains=search)
                | models.Q(offering__code__icontains=search)
                | models.Q(offering__title__icontains=search)
                | models.Q(offering__course__title__icontains=search)
                | models.Q(lesson__title__icontains=search)
                | models.Q(topic__icontains=search)
                | models.Q(title__icontains=search)
                | models.Q(teacher__first_name__icontains=search)
                | models.Q(teacher__last_name__icontains=search)
                | models.Q(location__name__icontains=search)
            )
        return qs.select_related("offering", "offering__course", "lesson", "teacher", "location").order_by(
            "class_code", "session_number", "session_date", "start_time"
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data
        try:
            session = create_session(
                offering=vd["offering"],
                session_date=vd["session_date"],
                start_time=vd["start_time"],
                end_time=vd["end_time"],
                session_number=vd.get("session_number"),
                lesson=vd.get("lesson"),
                teacher=vd.get("teacher"),
                location=vd.get("location"),
                class_code=vd.get("class_code", ""),
                title=vd.get("title", ""),
                topic=vd.get("topic", ""),
                actor=request.user,
            )
        except EducationServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            ClassSessionSerializer(session, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class SessionDetailView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /sessions/{id}/ — a generated session stays individually
    editable (task §3.ب: move one session for a closure, retune its hours,
    shift its room). Every schedule-bearing edit goes through
    ``update_session`` so the same room/teacher/class conflict rules apply
    as on create — except the row itself."""

    serializer_class = ClassSessionSerializer
    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, IsAcademicManager, ResourceCRUDPermission)

    def get_queryset(self):
        return education_sessions_visible_to(self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        vd = dict(serializer.validated_data)
        for key in ("offering", "class_group", "session_number"):
            vd.pop(key, None)
        schedule_fields = {
            key: vd.pop(key)
            for key in (
                "session_date", "start_time", "end_time", "teacher", "location",
                "lesson", "title", "topic", "status", "class_code",
            )
            if key in vd
        }
        try:
            if schedule_fields:
                instance = update_session(session=instance, actor=request.user, **schedule_fields)
            else:
                for attr, value in vd.items():
                    setattr(instance, attr, value)
                if vd:
                    instance.save(update_fields=list(vd) + ["updated_at"])
        except EducationServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(instance).data)


class SessionSoftDeleteView(SoftDeleteView):
    resource_key = "sessions"

    def get_queryset(self):
        return education_sessions_visible_to(self.request.user)


class SessionRestoreView(SoftRestoreView):
    queryset = ClassSession.all_objects.all()
    resource_key = "sessions"

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        vd = dict(serializer.validated_data)
        # re-parenting an existing session is not a manual adjustment —
        # formation owns that; silently drop these keys.
        vd.pop("offering", None)
        vd.pop("session_number", None)
        schedule_fields = {
            k: vd.pop(k)
            for k in ("session_date", "start_time", "end_time",
                      "teacher", "location", "lesson", "title", "status",
                      "class_code")
            if k in vd
        }
        if schedule_fields:
            try:
                session = update_session(
                    session=instance, actor=request.user, **schedule_fields
                )
            except EducationServiceError as exc:
                return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        else:  # legacy_id or other non-schedule metadata
            for attr, value in vd.items():
                setattr(instance, attr, value)
            session = instance
            if vd:
                instance.save()
        return Response(self.get_serializer(session).data)


class SessionBulkAttendanceView(APIView):
    """POST /sessions/{id}/attendance/ — bulk, idempotent roster post (B4)."""

    # Same queryset-less-APIView rule as above: role class is the gate, and
    # per-object ownership (teacher == session teacher) is checked below.
    # NOTE: this is deliberately NOT IsAcademicManager — that class refuses
    # every POST from a plain teacher (its write trio is manager-only), which
    # made the ownership check below dead code. IsTeacherPortalUser admits the
    # teacher role; the check below is the row authority.
    permission_classes = (IsActiveUser, IsTeacherPortalUser)

    def post(self, request, pk):
        session = ClassSession.objects.filter(pk=pk).first()
        if session is None:
            return Response({"error": "جلسه یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        # A teacher may only post rosters for their OWN sessions; managers
        # may post for any session.
        roles = request.user.role_codes()
        teacher_person = _student_of(request)
        if "manager" not in roles and "workflow_admin" not in roles and "hr" not in roles:
            if teacher_person is None or session.teacher_id != teacher_person.pk:
                return Response(
                    {"error": "فقط مدرس این جلسه یا مدیر می‌تواند حضور ثبت کند."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        rows = request.data.get("rows") or []
        if not isinstance(rows, list) or not rows:
            return Response({"rows": "لیست ردیف‌ها الزامی است."}, status=status.HTTP_400_BAD_REQUEST)
        replace = bool(request.data.get("replace", False))
        try:
            result = bulk_attendance(
                session=session, rows=rows, recorded_by=request.user, replace=replace,
            )
        except EducationServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as exc:
            return Response({"rows": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_200_OK)


class SessionAttendanceListView(generics.ListAPIView):
    """GET /sessions/{id}/attendance/ — the roster for one real session."""

    serializer_class = AttendanceRecordSerializer
    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, IsAcademicManager)

    def get_queryset(self):
        # The session itself must be inside the requester's scope (teacher →
        # only their sessions; student/parent → only their classes).
        session_ok = education_sessions_visible_to(self.request.user).filter(
            pk=self.kwargs["pk"]
        ).exists()
        if not session_ok:
            return AttendanceRecord.objects.none()
        return AttendanceRecord.objects.filter(
            session_id=self.kwargs["pk"], is_deleted=False
        ).select_related("student")


# ─────────────────────────────────────────────────────────────────────────────
# Teacher portal — roster + descriptive report cards + learner portal
# ─────────────────────────────────────────────────────────────────────────────

class OfferingRosterView(APIView):
    """GET /offerings/{id}/roster/ — active students of the offering's class.

    Auto-populates the attendance/report form. Teacher may read only their own
    offerings; managers any. Returns [{id, name, student_code}].
    """

    permission_classes = (IsActiveUser, IsTeacherPortalUser)

    def get(self, request, pk):
        offering = CourseOffering.objects.filter(pk=pk, is_deleted=False).first()
        if offering is None:
            return Response({"detail": "برگزاری یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        person = _student_of(request)
        roles = request.user.role_codes()
        is_manager = bool(roles & {"manager", "workflow_admin", "hr"})
        if not is_manager and (person is None or offering.instructor_id != person.pk):
            return Response({"detail": "دسترسی ندارید."}, status=status.HTTP_403_FORBIDDEN)
        return Response({"results": roster_students(offering=offering)})


class OfferingSessionSheetView(APIView):
    """GET /offerings/{id}/sheet/?session=<id> — attendance sheet read model.

    Merges the offering roster (task §2.3 auto-population) with the saved
    AttendanceRecords of one session, so the teacher page renders one row per
    student with status + note prefilled. ``session`` omitted → fresh sheet
    (empty statuses) for the picker's "new session" mode. Ownership: the
    offering's teacher or a manager — the SAME rule as the record write, and
    deliberately no StrictDjangoModelPermissions here (queryset-less APIView;
    the teacher portal must not depend on per-model view_* grants).
    """

    permission_classes = (IsActiveUser, IsTeacherPortalUser)

    def get(self, request, pk):
        offering = CourseOffering.objects.filter(pk=pk, is_deleted=False).first()
        if offering is None:
            return Response({"detail": "برگزاری یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        person = _student_of(request)
        roles = request.user.role_codes()
        is_manager = bool(roles & {"manager", "workflow_admin", "hr"})
        if not is_manager and (person is None or offering.instructor_id != person.pk):
            return Response({"detail": "دسترسی ندارید."}, status=status.HTTP_403_FORBIDDEN)

        session_id = (request.query_params.get("session") or "").strip()
        session = None
        if session_id:
            session = ClassSession.objects.filter(
                pk=session_id, offering=offering, is_deleted=False
            ).first()
            if session is None:
                return Response({"detail": "جلسه در این کلاس یافت نشد."},
                                status=status.HTTP_404_NOT_FOUND)

        saved = {}
        if session is not None:
            saved = {
                str(r.student_id): {"status": r.status, "note": r.note}
                for r in AttendanceRecord.objects.filter(
                    session=session, is_deleted=False
                )
            }
        # The class's own session list — powers the sheet's session dropdown
        # (pick a recorded session to edit, or choose «جلسه جدید»).
        sessions = [
            {
                "id": str(s.pk),
                "number": s.session_number,
                "date": s.session_date.isoformat(),
                "date_jalali": persian_date(s.session_date),
                "start": s.start_time.strftime("%H:%M"),
                "end": s.end_time.strftime("%H:%M"),
                "status": s.status,
                "recorded": s.recorded,
            }
            for s in ClassSession.objects.filter(
                offering=offering, is_deleted=False
            ).annotate(
                recorded=models.Count(
                    "attendances", filter=models.Q(attendances__is_deleted=False)
                )
            ).order_by("session_date", "start_time")[:200]
        ]

        roster = roster_students(offering=offering)
        for row in roster:
            got = saved.pop(row["id"], None)
            row["status"] = got["status"] if got else ""
            row["note"] = got["note"] if got else ""
        # students who had a record but left the roster (withdrawn): keep them
        # visible so the teacher sees the historical line, flagged.
        from apps.persons.models import Person

        for sid, vals in saved.items():
            p = Person.objects.filter(pk=sid).first()
            if p is None:
                continue
            roster.append({
                "id": sid,
                "name": (p.first_name + " " + p.last_name).strip(),
                "student_code": p.student_code or "",
                "status": vals["status"],
                "note": vals["note"],
                "inactive": True,
            })
        return Response({
            "session": None if session is None else {
                "id": str(session.pk),
                "session_number": session.session_number,
                "title": session.title,
                "lesson": str(session.lesson_id) if session.lesson_id else "",
                "status": session.status,
            },
            "rows": roster,
            "sessions": sessions,
            "offering": {
                "id": str(offering.pk),
                "title": offering.title or (offering.course.title if offering.course_id else ""),
                "schedule": offering.schedule or {},
                "location": offering.location.name if offering.location_id else "",
            },
        })


class OfferingRecordSessionView(APIView):
    """POST /offerings/{id}/record-session/ — the teacher-portal attendance write.

    ONE request = the whole session sheet: session metadata (Jalali date,
    number, start/end) + one row per auto-loaded student. The service runs it
    in a single ``transaction.atomic`` (find-or-create ClassSession + bulk
    upsert AttendanceRecord), refuses a second session on the same date or a
    duplicated session number, and returns the stored sheet's counters.

    body: {session_date (jalali), start_time, end_time,
           session_number?, session_id?, lesson?, title?,
           rows: [{student, status: present|absent|late|excused, note?}]}
    """

    permission_classes = (IsActiveUser, IsTeacherPortalUser)

    def post(self, request, pk):
        offering = CourseOffering.objects.filter(pk=pk, is_deleted=False).first()
        if offering is None:
            return Response({"detail": "برگزاری یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        person = _student_of(request)
        roles = request.user.role_codes()
        is_manager = bool(roles & {"manager", "workflow_admin", "hr"})
        if not is_manager and (person is None or offering.instructor_id != person.pk):
            return Response(
                {"detail": "فقط مدرس این کلاس یا مدیر می‌تواند حضور ثبت کند."},
                status=status.HTTP_403_FORBIDDEN,
            )
        # Parse through the session serializer — Jalali date + HH:MM contract
        # identical to the manager path (server stays the source of truth).
        payload = dict(request.data or {})
        payload["offering"] = str(offering.pk)
        serializer = ClassSessionSerializer(data=payload, context={"request": request})
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data
        rows = payload.get("rows") or []
        if not isinstance(rows, list) or not rows:
            return Response({"rows": "فهرست ردیف‌ها الزامی است."}, status=status.HTTP_400_BAD_REQUEST)
        session_id = payload.get("session_id") or None
        # Take the number from the RAW payload: the serializer defaults it to
        # 1 when omitted, but «omitted» here must mean «next available» (the
        # service derives max+1), not «force session #1».
        raw_number = payload.get("session_number")
        try:
            session_number = int(raw_number) if raw_number not in (None, "") else None
        except (TypeError, ValueError):
            return Response({"session_number": "باید عدد صحیح باشد."},
                            status=status.HTTP_400_BAD_REQUEST)
        if session_number is not None and session_number < 1:
            return Response({"session_number": "شماره جلسه باید مثبت باشد."},
                            status=status.HTTP_400_BAD_REQUEST)
        replace = str(payload.get("replace", True)).lower() in {"1", "true", "yes"}
        try:
            result = record_session_attendance(
                offering=offering,
                session_date=vd["session_date"],
                start_time=vd["start_time"],
                end_time=vd["end_time"],
                rows=rows,
                actor=request.user,
                session_id=session_id,
                session_number=session_number,
                lesson=vd.get("lesson"),
                title=vd.get("title", ""),
                replace=replace,
            )
        except EducationServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_200_OK)


class OfferingReportCardsView(APIView):
    """Descriptive report cards for one offering (teacher-of-class / manager).

    GET  → the offering's roster merged with any saved cards (pre-fill).
    POST → {"rows": [{student, result: passed|failed, teacher_note}]}
           Atomic + idempotent (update_or_create); failed ⇒ note required.
    """

    permission_classes = (IsActiveUser, IsTeacherPortalUser)

    def _offering_or_denied(self, request, pk):
        offering = CourseOffering.objects.filter(pk=pk, is_deleted=False).first()
        if offering is None:
            return None, Response(
                {"detail": "برگزاری یافت نشد."}, status=status.HTTP_404_NOT_FOUND
            )
        person = _student_of(request)
        roles = request.user.role_codes()
        is_manager = bool(roles & {"manager", "workflow_admin", "hr"})
        if not is_manager and (person is None or offering.instructor_id != person.pk):
            return None, Response(
                {"detail": "فقط مدرس این برگزاری یا مدیر."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return offering, None

    def get(self, request, pk):
        offering, denied = self._offering_or_denied(request, pk)
        if denied is not None:
            return denied
        return Response({
            "roster": roster_students(offering=offering),
            "cards": teacher_report_cards(offering),
        })

    def post(self, request, pk):
        offering, denied = self._offering_or_denied(request, pk)
        if denied is not None:
            return denied
        rows = (request.data or {}).get("rows") or []
        if not isinstance(rows, list) or not rows:
            return Response({"rows": "فهرست ردیف‌ها الزامی است."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = save_report_cards(offering=offering, rows=rows, actor=request.user)
        except EducationServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_200_OK)


class LearnerPortalView(APIView):
    """GET /portal/?student=<id> — attendance summary + report cards.

    Student → their own rows (``student`` optional, must match them). Guardian
    → exactly one of their ACTIVE wards (``student`` required; the switcher
    list comes back as ``students`` so a parent of two can toggle). Resolution
    runs through ``_resolve_learner_person`` — there is no path to another
    student's data, and the role code alone grants nothing.
    """

    permission_classes = (IsActiveUser,)

    def get(self, request):
        student_id = (request.query_params.get("student") or "").strip() or None
        person = _resolve_learner_person(request.user, student_id)
        students = learner_students(request.user)
        if person is None:
            return Response({
                "detail": "شما دانش‌آموز یا ولیّ ثبت‌شده‌ی این حساب نیستید.",
                "students": students,
            }, status=status.HTTP_403_FORBIDDEN)
        return Response({
            "student": next((s for s in students if s["id"] == str(person.pk)),
                            {"id": str(person.pk), "name": person.display_name,
                             "student_code": person.student_code or "", "relation": "self"}),
            "students": students,
            "attendance": learner_attendance_summary(request.user, student=person),
            "report_cards": learner_report_cards(request.user, student=person),
            "schedule": student_schedule(
                request.user,
                start=timezone.localdate(),
                end=timezone.localdate() + dt.timedelta(days=30),
            ),
        })


class TeacherClassesView(APIView):
    """GET /teacher/classes/ — offerings assigned to this teacher + upcoming
    sessions. Powers the teacher dashboard and the class pickers.

    Teacher-only read; a manager may also call it (returns their own, which is
    empty unless they are an instructor) — the scoping is by instructor==person.
    """

    permission_classes = (IsActiveUser, IsAcademicManager)

    def get(self, request):
        return Response({"results": teacher_classes(request.user)})


class OfferingCreateSessionView(APIView):
    """POST /offerings/{id}/sessions/ — teacher (or manager) creates a real
    session for their own offering; conflict-checked via create_session.

    body: {session_date (jalali), start_time, end_time, session_number?, lesson?}
    """

    permission_classes = (IsActiveUser, IsTeacherPortalUser)

    def post(self, request, pk):
        offering = CourseOffering.objects.filter(pk=pk, is_deleted=False).first()
        if offering is None:
            return Response({"detail": "برگزاری یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        person = _student_of(request)
        roles = request.user.role_codes()
        is_manager = bool(roles & {"manager", "workflow_admin", "hr"})
        if not is_manager and (person is None or offering.instructor_id != person.pk):
            return Response({"detail": "فقط مدرس این برگزاری یا مدیر."}, status=status.HTTP_403_FORBIDDEN)
        # Validate through the session serializer so Jalali date + HH:MM times
        # parse exactly like the manager path (no raw-string coercion).
        payload = dict(request.data or {})
        payload["offering"] = str(offering.pk)
        serializer = ClassSessionSerializer(data=payload, context={"request": request})
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data
        try:
            session = create_session(
                offering=offering,
                session_date=vd["session_date"],
                start_time=vd["start_time"],
                end_time=vd["end_time"],
                session_number=vd.get("session_number") or None,
                lesson=vd.get("lesson"),
                teacher=offering.instructor,
                location=offering.location,
                title=vd.get("title", ""),
                topic=vd.get("topic", ""),
                actor=request.user,
            )
        except EducationServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            ClassSessionSerializer(session, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Reports (criterion §13-7) — daily/weekly/monthly aggregates over REAL data
# ─────────────────────────────────────────────────────────────────────────────

class AttendanceReportView(APIView):
    """
    GET /api/education/reports/attendance/?period=day|week|month&date=YYYY-MM-DD
    date = میلادی ISO (هم‌راستا با قرارداد سرور)؛ گروه‌بندی شمسی در خروجی.
    """

    # APIView without a queryset: model-permission class would deny everyone,
    # so the role class is the gate (row-scope enforced inside the report).
    permission_classes = (IsActiveUser, IsAcademicManager)

    def get(self, request):
        import datetime as dt
        from apps.core.utils import english_numbers
        from apps.education.reports import ReportError, attendance_report

        period = (request.query_params.get("period") or "day").strip().lower()
        raw = (request.query_params.get("date") or "").strip()
        ref = None
        if raw:
            try:
                ref = dt.date.fromisoformat(english_numbers(raw))
            except ValueError:
                return Response(
                    {"date": "قالب تاریخ باید YYYY-MM-DD (میلادی) باشد."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        group_month = request.query_params.get("group_by") == "jalali_month"
        try:
            data = attendance_report(
                user=request.user, period=period, ref=ref,
                group_by_jalali_month=group_month,
            )
        except ReportError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(data)


class CapacityReportView(APIView):
    """GET /api/education/reports/capacity/ — ظرفیت ثبت‌نام (§13-7)."""

    permission_classes = (IsActiveUser, IsAcademicManager)

    def get(self, request):
        from django.db.models import Count
        from django.db.models.functions import TruncMonth
        from rest_framework.exceptions import ValidationError

        from apps.academics.scoping import class_groups_visible_to
        from apps.academics.models import ClassEnrollment
        from apps.core.fields import JalaliDateField
        from apps.education.models import OfferingEnrollment
        from apps.education.reports import capacity_report, class_group_capacity_report

        params = request.query_params
        start = end = None
        try:
            if params.get("from"):
                start = JalaliDateField().run_validation(params["from"])
            if params.get("to"):
                end = JalaliDateField().run_validation(params["to"])
        except ValidationError as exc:
            return Response({"date": exc.detail}, status=status.HTTP_400_BAD_REQUEST)
        if start and end and end < start:
            return Response({"date": "تاریخ پایان باید بعد از شروع باشد."}, status=status.HTTP_400_BAD_REQUEST)

        active = params.get("is_active")
        active_filter = None if active is None else active.strip().lower() in {"1", "true", "yes"}
        offerings = capacity_report(
            user=request.user,
            course_id=params.get("course") or None,
            offering_id=params.get("offering") or None,
            is_active=active_filter,
        )
        groups = class_group_capacity_report(
            user=request.user,
            term_id=params.get("term") or None,
            class_group_id=params.get("class_group") or None,
            is_active=active_filter,
        )

        offered_enrollments = OfferingEnrollment.objects.filter(
            is_deleted=False, is_active=True, offering__is_deleted=False,
        )
        group_enrollments = class_groups_visible_to(request.user).values("pk")
        academic_enrollments = ClassEnrollment.objects.filter(
            class_group_id__in=group_enrollments, is_deleted=False, is_active=True,
        )
        if start:
            offered_enrollments = offered_enrollments.filter(enrolled_at__gte=start)
            academic_enrollments = academic_enrollments.filter(enrollment_date__gte=start)
        if end:
            offered_enrollments = offered_enrollments.filter(enrolled_at__lte=end)
            academic_enrollments = academic_enrollments.filter(enrollment_date__lte=end)
        if params.get("course"):
            offered_enrollments = offered_enrollments.filter(offering__course_id=params["course"])
        if params.get("offering"):
            offered_enrollments = offered_enrollments.filter(offering_id=params["offering"])
        if params.get("class_group"):
            academic_enrollments = academic_enrollments.filter(class_group_id=params["class_group"])
        if params.get("term"):
            academic_enrollments = academic_enrollments.filter(class_group__term_id=params["term"])
        return Response({
            "offerings": offerings,
            "class_groups": groups,
            "registrations_by_month": {
                "offerings": list(
                    offered_enrollments.annotate(month=TruncMonth("enrolled_at"))
                    .values("month").annotate(total=Count("id")).order_by("month")
                ),
                "class_groups": list(
                    academic_enrollments.annotate(month=TruncMonth("enrollment_date"))
                    .values("month").annotate(total=Count("id")).order_by("month")
                ),
            },
        })


# ─────────────────────────────────────────────────────────────────────────────
# «تشکیل کلاس» — class formation (form 2): prefill → preview → atomic generate
# ─────────────────────────────────────────────────────────────────────────────

def _offering_or_404(pk):
    try:
        return CourseOffering.objects.filter(pk=pk, is_deleted=False).first()
    except (ValidationError, TypeError, ValueError):
        # a garbage path/uuid param is a 404, never a 500
        return None


class OfferingFormationView(APIView):
    """GET /offerings/{id}/formation/ — everything the class-formation form
    needs to auto-fill from the offering: proposed place, days+hours, the
    offering's lesson list (ordered, with hours), instructor, start date,
    a suggested class code and the already-formed classes.

    The values are SUGGESTIONS — the form posts them back (edited or not) to
    POST /class-formation/.
    """

    permission_classes = (IsActiveUser, IsAcademicManager)

    def get(self, request, pk):
        from apps.education.class_formation import formation_prefill
        from apps.education.serializers import classes_of_offering

        offering = _offering_or_404(pk)
        if offering is None:
            return Response({"detail": "برگزاری یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        payload = formation_prefill(offering).as_dict()
        payload["classes"] = classes_of_offering(offering)
        return Response(payload)


class ClassFormationPreviewView(APIView):
    """POST /class-formation/preview/ — dry-run of the generator: exact N
    numbered sessions with holiday jumps and per-row conflict flags, WITHOUT
    writing anything. Same validation contract as the real POST, so what the
    user previews is what the submit will produce."""

    permission_classes = (IsActiveUser, IsManagerOrAdmin)

    def post(self, request):
        from apps.education.class_formation import preview_sessions
        from apps.education.models import Location
        from apps.persons.models import Person

        offering = _offering_or_404(request.data.get("offering") or "")
        if offering is None:
            return Response({"offering": "برگزاری دوره یافت نشد."},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            count = request.data.get("count")
            # blank/absent → None (meaning "use the offering's proposal");
            # a bad id → explicit error, not a silent default.
            location = self._model_or_none(Location, request.data.get("location"),
                                           "فضای انتخابی یافت نشد.")
            teacher = self._model_or_none(Person, request.data.get("teacher"),
                                          "استاد انتخابی یافت نشد.")
            raw_skip = request.data.get("skip_holidays")
            skip = (None if raw_skip in (None, "")
                    else str(raw_skip).lower() in {"1", "true", "yes"})
            data = preview_sessions(
                offering=offering,
                lesson=request.data.get("lesson"),
                schedule=request.data.get("schedule") or {},
                start_date=_parse_iso_date(request.data.get("start_date")),
                count=int(count) if count not in (None, "") else 0,
                location=location,
                teacher=teacher,
                skip_holidays=skip,
            )
        except (EducationServiceError, ValueError) as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(data)

    @staticmethod
    def _model_or_none(model, raw, message):
        if raw in (None, ""):
            return None
        try:
            obj = model.objects.filter(pk=raw, is_deleted=False).first()
        except (ValidationError, ValueError, TypeError):
            obj = None
        if obj is None:
            raise EducationServiceError(message)
        return obj


class ClassFormationView(APIView):
    """POST /class-formation/ — the «تشکیل کلاس» submit.

    Validated through ClassFormationSerializer (offering/lesson existence,
    teacher active, schedule grammar), then handed to
    ClassSessionGeneratorService: ONE atomic transaction that produces
    exactly N ClassSession rows (1..N per class code), jumping holidays and
    pushing conflicted slots a week forward (or aborting everything under
    strict=true). Room/teacher double-booking is impossible — the same row-
    lock protocol as create_session.
    """

    permission_classes = (IsActiveUser, IsManagerOrAdmin)

    def post(self, request):
        from apps.education.serializers import ClassFormationSerializer

        serializer = ClassFormationSerializer(
            data=request.data, context={"request": request}
        )
        try:
            serializer.is_valid(raise_exception=True)
            result = serializer.save()
        except EducationServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_201_CREATED)


def _parse_iso_date(value):
    """accept jalali ۱۴۰۴/۰۷/۰۱ (the form format, dashes too — same
    ambiguity rule as core.fields.JalaliDateField) or gregorian YYYY-MM-DD."""
    from apps.core.utils import english_numbers
    import datetime as dt
    import jdatetime
    raw = (str(value).strip() if value not in (None, "") else "")
    if not raw:
        return None
    raw = english_numbers(raw)
    # JalaliDateField parses BOTH separators as jalali; mirror it unless the
    # year is unmistakably gregorian (>= 1500 only via ISO dashes with a
    # 4-digit year that is out of the jalali range in use, e.g. 19xx/20xx
    # written as ISO). Years 1300–1499 are always treated as jalali.
    for fmt in ("%Y/%m/%d", "%Y-%m-%d"):
        try:
            return jdatetime.datetime.strptime(raw, fmt).date().togregorian()
        except ValueError:
            continue
    try:
        return dt.date.fromisoformat(raw)
    except ValueError:
        raise ValueError("قالب تاریخ باید ۱۴۰۴/۰۷/۰۱ یا YYYY-MM-DD باشد.")
