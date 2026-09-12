from __future__ import annotations

from django.db import models
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from apps.core.group_permissions import HasGroupPermission, StrictDjangoModelPermissions
from apps.core.permissions import (
    IsActiveUser,
    IsAcademicManager,
    IsManagerOrAdmin,
)
from apps.academics.models import AcademicTerm, ClassEnrollment, ClassGroup
from apps.academics.scoping import class_groups_visible_to, enrollments_visible_to
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
from apps.academics.services import EnrollmentError, enrollment_service

# ──────────────────────────────────────────────
#  Academic Term
# ──────────────────────────────────────────────


class AcademicTermListCreateView(generics.ListCreateAPIView):
    """Terms: readable by academic staff; writable by managers."""

    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, IsAcademicManager)

    def get_serializer_class(self):
        return AcademicTermCreateSerializer if self.request.method == "POST" else AcademicTermListSerializer

    def get_queryset(self):
        qs = AcademicTerm.objects.all()
        current = self.request.query_params.get("current")
        if current is not None:
            qs = qs.filter(is_current=current == "true")
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active == "true")
        return qs.order_by("-start_date")


class AcademicTermDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, IsAcademicManager)
    serializer_class = AcademicTermDetailSerializer
    queryset = AcademicTerm.objects.all()


class AcademicTermActivateView(generics.GenericAPIView):
    """Activate a term as current. Managers only."""

    permission_classes = (IsActiveUser, IsManagerOrAdmin)
    queryset = AcademicTerm.objects.all()

    def post(self, request, pk):
        try:
            term = self.get_object()
            term.is_current = True
            term.save()
            return Response(AcademicTermDetailSerializer(term, context={"request": request}).data)
        except AcademicTerm.DoesNotExist:
            return Response({"error": "ترم مورد نظر یافت نشد."}, status=status.HTTP_404_NOT_FOUND)


# ──────────────────────────────────────────────
#  Class Group
# ──────────────────────────────────────────────


class ClassGroupListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, IsAcademicManager)

    def get_serializer_class(self):
        return ClassGroupCreateSerializer if self.request.method == "POST" else ClassGroupListSerializer

    def get_queryset(self):
        # DataScope (criterion §13-2): scoping lives HERE, in one shared
        # service-level rule, not in ad-hoc view filters.
        qs = class_groups_visible_to(self.request.user)
        term_id = self.request.query_params.get("term")
        if term_id:
            qs = qs.filter(term_id=term_id)
        teacher_id = self.request.query_params.get("teacher")
        if teacher_id:
            qs = qs.filter(teacher_id=teacher_id)
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                models.Q(name__icontains=search) | models.Q(code__icontains=search) | models.Q(room__icontains=search)
            )
        return qs.order_by("term", "code")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        class_group = serializer.save()
        return Response(ClassGroupDetailSerializer(class_group, context={"request": request}).data, status=status.HTTP_201_CREATED)


class ClassGroupDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, IsAcademicManager)
    serializer_class = ClassGroupDetailSerializer

    def get_queryset(self):
        # Scoped so a student/parent cannot fetch a class group by raw UUID.
        return class_groups_visible_to(self.request.user)


# ──────────────────────────────────────────────
#  Class Enrollment
# ──────────────────────────────────────────────


class ClassEnrollmentListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, IsAcademicManager)

    def get_serializer_class(self):
        return ClassEnrollmentCreateSerializer if self.request.method == "POST" else ClassEnrollmentListSerializer

    def get_queryset(self):
        # DataScope (criterion §13-2): shared service-level scoping.
        qs = enrollments_visible_to(self.request.user)
        class_group_id = self.request.query_params.get("class_group")
        if class_group_id:
            qs = qs.filter(class_group_id=class_group_id)
        student_id = self.request.query_params.get("student")
        if student_id:
            qs = qs.filter(student_id=student_id)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active == "true")
        return qs.order_by("class_group", "student")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data
        # Capacity is enforced under a row lock by the service (B4) — a bare
        # serializer.save() allowed concurrent over-enrollment.
        try:
            enrollment = enrollment_service.enroll(
                class_group_id=vd["class_group"].pk,
                student_id=vd["student"].pk,
                enrollment_date=vd.get("enrollment_date"),
                actor=request.user,
            )
        except EnrollmentError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(ClassEnrollmentListSerializer(enrollment, context={"request": request}).data, status=status.HTTP_201_CREATED)


class ClassEnrollmentDetailView(generics.RetrieveDestroyAPIView):
    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, IsAcademicManager)
    serializer_class = ClassEnrollmentListSerializer

    def get_queryset(self):
        return enrollments_visible_to(self.request.user)