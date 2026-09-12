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

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.group_permissions import StrictDjangoModelPermissions
from apps.core.permissions import IsAcademicManager, IsActiveUser, IsManagerOrAdmin
from apps.academics.scoping import education_sessions_visible_to
from apps.education.models import (
    AttendanceRecord,
    ClassSession,
    Course,
    CourseOffering,
    Department,
    Lesson,
    Location,
)
from apps.education.serializers import (
    AttendanceRecordSerializer,
    ClassSessionSerializer,
    CourseOfferingSerializer,
    CourseSerializer,
    DepartmentSerializer,
    LessonSerializer,
    LocationSerializer,
)
from apps.education.services import (
    EducationServiceError,
    bulk_attendance,
    create_session,
    enroll_student,
)


def _student_of(request):
    return getattr(request.user, "person", None)


# IsAcademicManager already encodes "reads for academic staff, writes for
# managers" at the class level; each view keeps that pair plus the model-perm
# layer. No per-method branching is needed.

class DepartmentListCreateView(generics.ListCreateAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, IsAcademicManager)


class LocationListCreateView(generics.ListCreateAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, IsAcademicManager)


class LessonListCreateView(generics.ListCreateAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, IsAcademicManager)


class LessonDetailView(generics.RetrieveUpdateAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, IsAcademicManager)


class CourseListCreateView(generics.ListCreateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, IsAcademicManager)


class CourseDetailView(generics.RetrieveUpdateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, IsAcademicManager)


class OfferingListCreateView(generics.ListCreateAPIView):
    queryset = CourseOffering.objects.select_related("course", "location", "instructor")
    serializer_class = CourseOfferingSerializer
    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, IsAcademicManager)


class OfferingDetailView(generics.RetrieveUpdateAPIView):
    queryset = CourseOffering.objects.select_related("course", "location", "instructor")
    serializer_class = CourseOfferingSerializer
    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, IsAcademicManager)


class OfferingEnrollView(APIView):
    """POST /offerings/{id}/enroll/ — capacity enforced under a row lock (B4)."""

    permission_classes = (IsActiveUser, IsManagerOrAdmin, StrictDjangoModelPermissions)

    def post(self, request, pk):
        offering = CourseOffering.objects.filter(pk=pk).first()
        if offering is None:
            return Response({"error": "برگزاری یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        student_id = request.data.get("student")
        if not student_id:
            return Response({"student": "الزامی است."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            enroll_student(offering=offering, student=student_id, actor=request.user)
        except EducationServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            CourseOfferingSerializer(offering, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )


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
            qs = qs.filter(session_date=date)
        return qs

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
                title=vd.get("title", ""),
                actor=request.user,
            )
        except EducationServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            ClassSessionSerializer(session, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class SessionDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = ClassSessionSerializer
    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, IsAcademicManager)

    def get_queryset(self):
        return education_sessions_visible_to(self.request.user)


class SessionBulkAttendanceView(APIView):
    """POST /sessions/{id}/attendance/ — bulk, idempotent roster post (B4)."""

    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, IsAcademicManager)

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
        from apps.education.reports import capacity_report

        return Response({"offerings": capacity_report(user=request.user)})
