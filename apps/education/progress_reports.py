"""Teacher composition and learner delivery of student progress reports."""
import uuid

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Count, Max, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.fields import JalaliDateField
from apps.core.report_dates import ReportDateError, ReportRange, parse_report_date, parse_report_time
from apps.core.permissions import IsActiveUser, IsTeacherPortalUser
from apps.education.models import CourseOffering, StudentProgressReport
from apps.education.services import _resolve_learner_person, roster_students


class ReportCalendarDateField(JalaliDateField):
    def to_internal_value(self, data):
        try:
            return parse_report_date(data)
        except ReportDateError as exc:
            raise serializers.ValidationError(str(exc))


class ReportClockField(serializers.TimeField):
    def to_internal_value(self, data):
        try:
            return parse_report_time(data)
        except ReportDateError as exc:
            raise serializers.ValidationError(str(exc))


class ProgressReportSerializer(serializers.ModelSerializer):
    period_start = ReportCalendarDateField()
    period_end = ReportCalendarDateField()
    start_time = ReportClockField(required=False, allow_null=True)
    end_time = ReportClockField(required=False, allow_null=True)
    period_display = serializers.CharField(source="get_period_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    student_name = serializers.CharField(source="student.display_name", read_only=True)
    offering_name = serializers.SerializerMethodField()
    author_name = serializers.SerializerMethodField()
    is_class_report = serializers.SerializerMethodField()

    class Meta:
        model = StudentProgressReport
        fields = (
            "id", "offering", "offering_name", "student", "student_name", "author_name", "is_class_report",
            "period", "period_display", "period_start", "period_end", "start_time", "end_time", "title", "summary",
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

    def get_is_class_report(self, obj):
        return bool(obj.class_report_id)

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
            try:
                ReportRange(start, end,
                            attrs.get("start_time", getattr(instance, "start_time", None)),
                            attrs.get("end_time", getattr(instance, "end_time", None))).validate()
            except ReportDateError as exc:
                raise ValidationError({"period_end": str(exc)})
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


class TeacherClassProgressReportView(APIView):
    """Read class-report history and publish reports to every active learner."""

    permission_classes = (IsActiveUser, IsTeacherPortalUser)

    def _offering_for_teacher(self, request, offering_value):
        try:
            offering_id = serializers.UUIDField().run_validation(offering_value)
        except serializers.ValidationError:
            raise ValidationError({"offering": "شناسهٔ کلاس معتبر نیست."})
        offering = get_object_or_404(CourseOffering.objects.select_related("instructor"), pk=offering_id)
        teacher = getattr(request.user, "person", None)
        if teacher is None or offering.instructor_id != teacher.pk:
            raise PermissionDenied("فقط مدرس این کلاس می‌تواند گزارش‌های کلاسی را ببیند یا ارسال کند.")
        return offering

    def get(self, request):
        offering = self._offering_for_teacher(request, request.query_params.get("offering"))
        reports = report_rows().filter(
            author=request.user, offering=offering, class_report_id__isnull=False,
        )
        period = request.query_params.get("period")
        if period:
            if period not in StudentProgressReport.Period.values:
                raise ValidationError({"period": "نوع گزارش معتبر نیست."})
            reports = reports.filter(period=period)

        groups = list(reports.order_by().values("class_report_id").annotate(
            recipient_count=Count("pk"),
            read_count=Count("pk", filter=Q(read_at__isnull=False)),
            last_sent_at=Max("sent_at"),
        ).order_by("-last_sent_at", "class_report_id"))
        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(groups, request, view=self)
        batch_ids = [group["class_report_id"] for group in page]
        representatives = {}
        for report in reports.filter(class_report_id__in=batch_ids).order_by("created_at", "pk"):
            representatives.setdefault(report.class_report_id, report)
        results = []
        for group in page:
            data = ProgressReportSerializer(representatives[group["class_report_id"]]).data
            data["recipient_count"] = group["recipient_count"]
            data["read_count"] = group["read_count"]
            results.append(data)
        return paginator.get_paginated_response(results)

    @transaction.atomic
    def post(self, request):
        offering = self._offering_for_teacher(request, request.data.get("offering"))
        if offering.is_deleted or not offering.is_active:
            raise PermissionDenied("فقط مدرس این کلاس می‌تواند گزارش کلاسی ارسال کند.")

        roster = roster_students(offering=offering)
        if not roster:
            raise ValidationError({"offering": "این کلاس هنرجوی فعالی برای دریافت گزارش ندارد."})

        from apps.persons.models import Person

        students = list(Person.objects.filter(
            pk__in=[row["id"] for row in roster], is_deleted=False,
        ).select_related("user"))
        eligible, unavailable = [], []
        for student in students:
            try:
                learner = student.user
            except ObjectDoesNotExist:
                learner = None
            if (learner is None or not learner.is_active or learner.is_deleted
                    or "student" not in learner.role_codes()):
                unavailable.append(student.display_name)
            else:
                eligible.append(student)
        if unavailable:
            raise ValidationError({
                "students": "برای همهٔ هنرجویان حساب فعال پرتال دانش‌آموزی لازم است: "
                + "، ".join(unavailable)
            })

        payload = request.data.copy()
        payload.pop("student", None)
        batch_id = uuid.uuid4()
        sent_at = timezone.now()
        reports = []
        for student in eligible:
            serializer = ProgressReportSerializer(
                data={**payload, "student": str(student.pk)}, context={"request": request},
            )
            serializer.is_valid(raise_exception=True)
            reports.append(serializer.save(
                author=request.user, status=StudentProgressReport.Status.SENT,
                sent_at=sent_at, class_report_id=batch_id,
            ))
        return Response({"count": len(reports), "class_report_id": str(batch_id)}, status=201)


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
        start = self.request.query_params.get("start")
        end = self.request.query_params.get("end")
        if bool(start) != bool(end):
            raise ValidationError({"date_range": "تاریخ شروع و پایان را با هم وارد کنید."})
        if start and end:
            try:
                start_date = ReportCalendarDateField().run_validation(start)
                end_date = ReportCalendarDateField().run_validation(end)
            except serializers.ValidationError as exc:
                raise ValidationError({"date_range": exc.detail})
            if start_date > end_date:
                raise ValidationError({"end": "تاریخ پایان باید برابر یا بعد از شروع باشد."})
            qs = qs.filter(period_start__lte=end_date, period_end__gte=start_date)
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
