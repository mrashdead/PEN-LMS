from __future__ import annotations

from django.db import models
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response

from apps.core.permissions import (
    IsActiveUser,
    CanAccessPersons,
    IsPersonOwnerOrManager,
    CanCreateUserForPerson,
    CanManageStudentParent,
)
from apps.persons.models import Person, StudentParent
from apps.persons.serializers import (
    CreateUserForPersonSerializer,
    PersonCreateSerializer,
    PersonDetailSerializer,
    PersonListSerializer,
    StudentParentSerializer,
)
from apps.persons.services import PersonService, PersonServiceError

person_service = PersonService()


class PersonListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/persons/       — لیست اشخاص (مدیران: همه؛ کارمندان: محدود)
    POST /api/persons/       — ثبت شخص جدید (فقط manager/hr/workflow_admin)
    """

    permission_classes = (IsActiveUser, CanAccessPersons)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PersonCreateSerializer
        return PersonListSerializer

    def get_queryset(self):
        user = self.request.user
        roles = user.role_codes()

        # مدیران و منابع انسانی همه اشخاص را می‌بینند
        if roles & {"manager", "hr", "workflow_admin"}:
            qs = Person.objects.select_related("user").all()
        else:
            # کارمندان و معلمان فقط اشخاص فعال و عمومی (student, parent) را ببینند
            qs = Person.objects.select_related("user").filter(is_active=True)

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
        person = self.perform_create(serializer)
        output = PersonDetailSerializer(person, context={"request": request})
        return Response(output.data, status=status.HTTP_201_CREATED)


class PersonDetailView(generics.RetrieveUpdateAPIView):
    """
    GET    /api/persons/{id}/    — جزئیات شخص
    PATCH  /api/persons/{id}/    — ویرایش (فرد یا manager)
    """

    permission_classes = (IsActiveUser, IsPersonOwnerOrManager)
    serializer_class = PersonDetailSerializer

    def get_queryset(self):
        user = self.request.user
        roles = user.role_codes()
        if roles & {"manager", "hr", "workflow_admin"}:
            return Person.objects.select_related("user").all()
        return Person.objects.select_related("user").filter(
            models.Q(user=user) | models.Q(is_active=True)
        )


class CreateUserForPersonView(views.APIView):
    """
    POST /api/persons/{id}/create-user/
    ساخت User برای شخص — فقط manager/hr/workflow_admin
    """

    permission_classes = (IsActiveUser, CanCreateUserForPerson)

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


class StudentParentListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/student-parents/       — لیست روابط والد-فرزند (فقط مدیران)
    POST /api/student-parents/       — ثبت رابطه جدید (فقط مدیران)
    """

    permission_classes = (IsActiveUser, CanManageStudentParent)
    serializer_class = StudentParentSerializer
    queryset = StudentParent.objects.select_related("parent", "student").all()