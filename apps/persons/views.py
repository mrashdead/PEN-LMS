from __future__ import annotations

from django.db import models
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response

from apps.core.group_permissions import HasGroupPermission, StrictDjangoModelPermissions
from apps.core.permissions import (
    IsActiveUser,
    CanAccessPersons,
    IsManagerOrAdmin,
    IsPersonOwnerOrManager,
    CanCreateUserForPerson,
)
from apps.persons.models import Person
from apps.persons.serializers import (
    CreateUserForPersonSerializer,
    PersonCreateSerializer,
    PersonDetailSerializer,
    PersonListSerializer,
)
from apps.persons.services import (
    DuplicateNationalCodeError,
    PersonService,
    PersonServiceError,
    persons_visible_to,
)

person_service = PersonService()


class PersonListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/persons/       — لیست اشخاص (مدیران: همه؛ کارمندان: محدود)
    POST /api/persons/       — ثبت شخص جدید (فقط manager/hr/workflow_admin)
    """

    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, CanAccessPersons)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PersonCreateSerializer
        return PersonListSerializer

    def get_queryset(self):
        # Central visibility rule (B1): elevated → all; teacher/employee →
        # self + active directory; parent → self + own children;
        # student/other end-user → self only.
        qs = persons_visible_to(self.request.user).select_related("user")

        # فیلتر بر اساس نوع شخص
        person_type = self.request.query_params.get("person_type")
        if person_type:
            qs = qs.filter(person_type=person_type)

        # فیلتر بر اساس وضعیت
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active == "true")

        # جستجو
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                models.Q(national_code__icontains=search)
                | models.Q(first_name__icontains=search)
                | models.Q(last_name__icontains=search)
                | models.Q(mobile__icontains=search)
                | models.Q(student_code__icontains=search)
                | models.Q(employee_code__icontains=search)
            )

        return qs.order_by("-created_at")

    def perform_create(self, serializer):
        person = person_service.create_person(
            **serializer.validated_data,
            registered_by=self.request.user,
        )
        return person

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            person = self.perform_create(serializer)
        except DuplicateNationalCodeError as exc:
            return Response({"national_code": [str(exc)]}, status=status.HTTP_400_BAD_REQUEST)
        output = PersonDetailSerializer(person, context={"request": request})
        return Response(output.data, status=status.HTTP_201_CREATED)


class PersonDetailView(generics.RetrieveUpdateAPIView):
    """
    GET    /api/persons/{id}/    — جزئیات شخص (PII ماسک‌شده برای غیرمتولیان)
    PATCH  /api/persons/{id}/    — ویرایش (فرد یا manager)
    """

    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, IsPersonOwnerOrManager)
    serializer_class = PersonDetailSerializer

    def get_queryset(self):
        # Same central visibility rule as the list view — a detail route must
        # never widen what the list hides (B1). Writes stay restricted by
        # IsPersonOwnerOrManager; reads of RAW PII are gated per-field by the
        # serializer via can_view_full_person_detail() (view_person_detail).
        return persons_visible_to(self.request.user).select_related("user")


class CreateUserForPersonView(views.APIView):
    """
    POST /api/persons/{id}/create-user/
    ساخت User برای شخص — فقط manager/hr/workflow_admin
    """

    permission_classes = (IsActiveUser, HasGroupPermission, CanCreateUserForPerson)
    required_permissions = {
        "POST": ["persons.change_person"],
    }

    def post(self, request, person_id):
        serializer = CreateUserForPersonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            person = person_service.create_user_for_person(
                person_id=person_id,
                username=serializer.validated_data.get("username") or None,
                password=serializer.validated_data.get("password") or None,
                created_by=request.user,
            )
        except PersonServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        output = PersonDetailSerializer(person, context={"request": request})
        return Response(output.data)


class PersonTypeAssignView(views.APIView):
    """
    POST /api/persons/{id}/types/ — افزودن نوع دوم به شخص (§13-1).
    body: {"type": "employee", "valid_from": ..., "valid_to": ...}
    """

    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, IsManagerOrAdmin)

    def post(self, request, person_id):
        person = Person.objects.filter(pk=person_id, is_deleted=False).first()
        if person is None:
            return Response({"error": "شخص یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        type_code = (request.data.get("type") or "").strip().lower()
        try:
            person_service.add_person_type(
                person=person,
                type_code=type_code,
                valid_from=request.data.get("valid_from"),
                valid_to=request.data.get("valid_to"),
                assigned_by=request.user,
            )
        except PersonServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            PersonDetailSerializer(person, context={"request": request}).data
        )