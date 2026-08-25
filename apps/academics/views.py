from __future__ import annotations

from django.db import models
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from apps.academics.models import AcademicTerm, ClassEnrollment, ClassGroup
from apps.academics.serializers import (
    AcademicTermCreateSerializer,
    AcademicTermDetailSerializer,
    AcademicTermListSerializer,
    ClassEnrollmentCreateSerializer,
    ClassEnrollmentListSerializer,
    ClassGroupCreateSerializer,
    ClassGroupDetailSerializer,
    ClassGroupListSerializer,
)


# ──────────────────────────────────────────────
#  Academic Term
# ──────────────────────────────────────────────


class AcademicTermListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/academics/terms/        — لیست ترم‌ها
    POST /api/academics/terms/        — ایجاد ترم جدید
    """

    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AcademicTermCreateSerializer
        return AcademicTermListSerializer

    def get_queryset(self):
        qs = AcademicTerm.objects.all()

        # فیلتر ترم جاری
        current = self.request.query_params.get("current")
        if current is not None:
            qs = qs.filter(is_current=current == "true")

        # فیلتر وضعیت
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active == "true")

        return qs.order_by("-start_date")


class AcademicTermDetailView(generics.RetrieveUpdateAPIView):
    """
    GET    /api/academics/terms/{id}/   — جزئیات ترم
    PATCH  /api/academics/terms/{id}/   — ویرایش ترم
    """

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = AcademicTermDetailSerializer
    queryset = AcademicTerm.objects.all()


class AcademicTermActivateView(generics.GenericAPIView):
    """
    POST /api/academics/terms/{id}/activate/   — فعال‌سازی ترم به عنوان جاری
    """

    permission_classes = (permissions.IsAuthenticated,)
    queryset = AcademicTerm.objects.all()

    def post(self, request, pk):
        try:
            term = self.get_object()
            term.is_current = True
            term.save()
            serializer = AcademicTermDetailSerializer(term, context={"request": request})
            return Response(serializer.data)
        except AcademicTerm.DoesNotExist:
            return Response({"error": "ترم مورد نظر یافت نشد."}, status=status.HTTP_404_NOT_FOUND)


# ──────────────────────────────────────────────
#  Class Group
# ──────────────────────────────────────────────


class ClassGroupListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/academics/class-groups/        — لیست کلاس‌ها
    POST /api/academics/class-groups/        — ایجاد کلاس جدید
    """

    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ClassGroupCreateSerializer
        return ClassGroupListSerializer

    def get_queryset(self):
        qs = ClassGroup.objects.select_related("term", "teacher").all()

        # فیلتر بر اساس ترم
        term_id = self.request.query_params.get("term")
        if term_id:
            qs = qs.filter(term_id=term_id)

        # فیلتر بر اساس معلم
        teacher_id = self.request.query_params.get("teacher")
        if teacher_id:
            qs = qs.filter(teacher_id=teacher_id)

        # جستجو
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                models.Q(name__icontains=search)
                | models.Q(code__icontains=search)
                | models.Q(room__icontains=search)
            )

        return qs.order_by("term", "code")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        class_group = serializer.save()
        output = ClassGroupDetailSerializer(class_group, context={"request": request})
        return Response(output.data, status=status.HTTP_201_CREATED)


class ClassGroupDetailView(generics.RetrieveUpdateAPIView):
    """
    GET    /api/academics/class-groups/{id}/   — جزئیات کلاس
    PATCH  /api/academics/class-groups/{id}/   — ویرایش کلاس
    """

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ClassGroupDetailSerializer
    queryset = ClassGroup.objects.select_related("term", "teacher").all()


# ──────────────────────────────────────────────
#  Class Enrollment
# ──────────────────────────────────────────────


class ClassEnrollmentListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/academics/enrollments/        — لیست ثبت‌نام‌ها
    POST /api/academics/enrollments/        — ثبت‌نام دانش‌آموز در کلاس
    """

    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ClassEnrollmentCreateSerializer
        return ClassEnrollmentListSerializer

    def get_queryset(self):
        qs = ClassEnrollment.objects.select_related(
            "class_group", "student"
        ).all()

        # فیلتر بر اساس کلاس
        class_group_id = self.request.query_params.get("class_group")
        if class_group_id:
            qs = qs.filter(class_group_id=class_group_id)

        # فیلتر بر اساس دانش‌آموز
        student_id = self.request.query_params.get("student")
        if student_id:
            qs = qs.filter(student_id=student_id)

        # فیلتر وضعیت
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active == "true")

        return qs.order_by("class_group", "student")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        enrollment = serializer.save()
        output = ClassEnrollmentListSerializer(enrollment, context={"request": request})
        return Response(output.data, status=status.HTTP_201_CREATED)


class ClassEnrollmentDetailView(generics.RetrieveDestroyAPIView):
    """
    GET    /api/academics/enrollments/{id}/   — جزئیات ثبت‌نام
    DELETE /api/academics/enrollments/{id}/   — حذف ثبت‌نام
    """

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ClassEnrollmentListSerializer
    queryset = ClassEnrollment.objects.select_related("class_group", "student").all()
