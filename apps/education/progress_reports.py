"""Teacher composition and learner delivery of student progress reports."""
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.fields import JalaliDateField
from apps.core.permissions import IsActiveUser, IsTeacherPortalUser
from apps.education.models import CourseOffering, StudentProgressReport
from apps.education.services import _resolve_learner_person, roster_students


class ProgressReportSerializer(serializers.ModelSerializer):
    period_start = JalaliDateField()
    period_end = JalaliDateField()
    period_display = serializers.CharField(source="get_period_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    student_name = serializers.CharField(source="student.display_name", read_only=True)
    offering_name = serializers.SerializerMethodField()
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = StudentProgressReport
        fields = (
            "id", "offering", "offering_name", "student", "student_name", "author_name",
            "period", "period_display", "period_start", "period_end", "title", "summary",
            "strengths", "improvements", "homework", "next_steps", "status", "status_display",
            "sent_at", "read_at", "created_at", "updated_at",
        )
        read_only_fields = ("id", "status", "sent_at", "read_at", "created_at", "updated_at")
        extra_kwargs = {field: {"max_length": 10000} for field in (
            "summary", "strengths", "improvements", "homework", "next_steps",
        )}

    def get_offering_name(self, obj):
        return obj.offering.title or obj.offering.course.title

    def get_author_name(self, obj):
        person = getattr(obj.author, "person", None)
        return person.display_name if person else obj.author.get_full_name() or obj.author.username

    def validate(self, attrs):
        instance = self.instance
        if instance and instance.status != StudentProgressReport.Status.DRAFT:
            raise ValidationError("گزارش ارسال‌شده قابل ویرایش نیست.")
        offering = attrs.get("offering", getattr(instance, "offering", None))
        student = attrs.get("student", getattr(instance, "student", None))
        if instance and ((offering and offering.pk != instance.offering_id)
                         or (student and student.pk != instance.student_id)):
            raise ValidationError("کلاس و دانش‌آموز گزارش ذخیره‌شده قابل تغییر نیستند.")
        user = self.context["request"].user
        person = getattr(user, "person", None)
        if offering.is_deleted or not offering.is_active or person is None or offering.instructor_id != person.pk:
            raise PermissionDenied("فقط مدرس این کلاس می‌تواند برای دانش‌آموزان آن گزارش بنویسد.")
        if student.is_deleted or str(student.pk) not in {s["id"] for s in roster_students(offering=offering)}:
            raise ValidationError({"student": "دانش‌آموز باید عضو فعال همین کلاس باشد."})
        start = attrs.get("period_start", getattr(instance, "period_start", None))
        end = attrs.get("period_end", getattr(instance, "period_end", None))
        period = attrs.get("period", getattr(instance, "period", None))
        if start and end:
            days = (end - start).days + 1
            if days <= 0:
                raise ValidationError({"period_end": "تاریخ پایان باید برابر یا بعد از شروع باشد."})
            limit = {"daily": 1, "weekly": 7, "monthly": 31}[period]
            if days > limit:
                raise ValidationError({"period_end": f"بازهٔ این گزارش حداکثر {limit} روز است."})
            if end > timezone.localdate():
                raise ValidationError({"period_end": "گزارش عملکرد نمی‌تواند برای آینده باشد."})
        return attrs


def report_rows():
    return StudentProgressReport.objects.select_related("student", "offering__course", "author__person")


def learner_report_student(user, student_id=None):
    person = _resolve_learner_person(user, student_id)
    if person is not None and person.user_id != user.pk:
        from apps.persons.models import StudentGuardian

        today = timezone.localdate()
        link = StudentGuardian.objects.filter(
            student=person, guardian=getattr(user, "person", None),
            is_active=True, is_deleted=False, can_view_grades=True,
        ).filter(Q(valid_from__isnull=True) | Q(valid_from__lte=today)).filter(
            Q(valid_to__isnull=True) | Q(valid_to__gte=today),
        )
        if not link.exists():
            return None
    return person


class TeacherProgressReportListView(generics.ListCreateAPIView):
    permission_classes = (IsActiveUser, IsTeacherPortalUser)
    serializer_class = ProgressReportSerializer

    def get_queryset(self):
        qs = report_rows().filter(author=self.request.user)
        for field in ("offering", "student"):
            value = self.request.query_params.get(field)
            if value:
                try:
                    value = serializers.UUIDField().run_validation(value)
                except serializers.ValidationError:
                    raise ValidationError({field: "شناسه معتبر نیست."})
                qs = qs.filter(**{field: value})
        for field in ("period", "status"):
            if self.request.query_params.get(field):
                qs = qs.filter(**{field: self.request.query_params[field]})
        return qs

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TeacherProgressReportDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsActiveUser, IsTeacherPortalUser)
    serializer_class = ProgressReportSerializer
    http_method_names = ["get", "patch", "head", "options"]

    def get_queryset(self):
        return report_rows().filter(author=self.request.user)

    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        # Share the row lock with send so an edit cannot overwrite publication.
        report = get_object_or_404(self.get_queryset().select_for_update(of=("self",)), pk=kwargs["pk"])
        serializer = self.get_serializer(report, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class SendProgressReportView(APIView):
    permission_classes = (IsActiveUser, IsTeacherPortalUser)

    @transaction.atomic
    def post(self, request, pk):
        report = get_object_or_404(StudentProgressReport.objects.select_for_update(), pk=pk, author=request.user)
        if report.status == StudentProgressReport.Status.DRAFT:
            serializer = ProgressReportSerializer(report, data={}, partial=True, context={"request": request})
            serializer.is_valid(raise_exception=True)
            if not report.student.user_id or not report.student.user.is_active or report.student.user.is_deleted:
                raise ValidationError("دانش‌آموز حساب کاربری فعال ندارد؛ ابتدا حساب پرتال او را فعال کنید.")
            if "student" not in report.student.user.role_codes():
                raise ValidationError("حساب دانش‌آموز به پرتال دانش‌آموزان دسترسی ندارد.")
            report.status = StudentProgressReport.Status.SENT
            report.sent_at = timezone.now()
            report.save(update_fields=["status", "sent_at", "updated_at"])
        return Response(ProgressReportSerializer(report).data)


class LearnerProgressReportListView(generics.ListAPIView):
    permission_classes = (IsActiveUser,)
    serializer_class = ProgressReportSerializer

    def get_queryset(self):
        person = learner_report_student(self.request.user, self.request.query_params.get("student") or None)
        if person is None:
            raise PermissionDenied("شما به گزارش‌های این دانش‌آموز دسترسی ندارید.")
        qs = report_rows().filter(student=person, status=StudentProgressReport.Status.SENT).order_by("-sent_at", "-pk")
        if self.request.query_params.get("period"):
            qs = qs.filter(period=self.request.query_params["period"])
        return qs


class ReadProgressReportView(APIView):
    permission_classes = (IsActiveUser,)

    def post(self, request, pk):
        person = learner_report_student(request.user, request.data.get("student") or None)
        if person is None:
            raise PermissionDenied("شما به گزارش‌های این دانش‌آموز دسترسی ندارید.")
        report = get_object_or_404(report_rows(), pk=pk, student=person, status=StudentProgressReport.Status.SENT)
        # A guardian may read a linked ward's report, but only the learner's
        # own account records that the learner has viewed it.
        if person.user_id == request.user.pk:
            StudentProgressReport.objects.filter(pk=report.pk, read_at__isnull=True).update(read_at=timezone.now())
            report.refresh_from_db()
        return Response(ProgressReportSerializer(report).data)
