from __future__ import annotations

from django.db import models, transaction
from django.db.models import Exists, OuterRef, Prefetch
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response

from apps.core.group_permissions import HasGroupPermission, StrictDjangoModelPermissions
from apps.core.crud_views import SoftDeleteView, SoftRestoreView
from apps.core.permissions import (
    IsActiveUser,
    CanAccessPersons,
    IsManagerOrAdmin,
    IsPersonOwnerOrManager,
    CanCreateUserForPerson,
    ResourceCRUDPermission,
)
from apps.core.utils import english_numbers
from apps.persons.models import GuardianProfile, Person, StudentGuardian
from apps.persons.pagination import PersonCursorPagination
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
    can_view_full_person_detail,
    mask_identifier,
    persons_visible_to,
)

person_service = PersonService()


class PersonListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/persons/       — لیست اشخاص (مدیران: همه؛ کارمندان: محدود)
    POST /api/persons/       — ثبت شخص جدید (فقط manager/hr/workflow_admin)
    """

    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, CanAccessPersons)
    pagination_class = PersonCursorPagination

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PersonCreateSerializer
        return PersonListSerializer

    def get_queryset(self):
        # Central visibility rule (B1): elevated → all; teacher/employee →
        # self + active directory; parent → self + own children;
        # student/other end-user → self only.
        from apps.accounts.models import UserRole

        role_prefetch = Prefetch(
            "user__user_roles",
            queryset=UserRole.objects.filter(
                is_active=True, role__is_active=True, role__is_deleted=False,
            ).select_related("role").only(
                "user_id", "role_id", "role__code", "role__name",
            ),
            to_attr="active_role_links",
        )
        qs = persons_visible_to(self.request.user).select_related("user").prefetch_related(
            role_prefetch
        ).only(
            "id", "national_code", "first_name", "last_name", "person_type",
            "birth_date", "mobile", "email", "is_active", "created_at", "user_id",
        )

        # فیلتر بر اساس نوع شخص
        person_type = self.request.query_params.get("person_type")
        if person_type:
            qs = qs.filter(person_type=person_type)

        # ``role`` is the public filter name. Primary person types use the
        # indexed person_type column; leadership roles live on UserRole and
        # are matched with EXISTS so the directory never materializes a join.
        role = (self.request.query_params.get("role") or "").strip().lower()
        if role:
            if role == Person.Type.EMPLOYEE:
                leadership_exists = UserRole.objects.filter(
                    user_id=OuterRef("user_id"),
                    role__code__in=("manager", "supervisor"),
                    role__is_active=True,
                    role__is_deleted=False,
                    is_active=True,
                )
                qs = qs.filter(person_type=role).annotate(
                    has_leadership=Exists(leadership_exists)
                ).filter(has_leadership=False)
            elif role in {choice for choice, _label in Person.Type.choices}:
                qs = qs.filter(person_type=role)
            else:
                role_exists = UserRole.objects.filter(
                    user_id=OuterRef("user_id"),
                    role__code=role,
                    role__is_active=True,
                    role__is_deleted=False,
                    is_active=True,
                )
                qs = qs.annotate(role_match=Exists(role_exists)).filter(role_match=True)

        # فیلتر بر اساس وضعیت
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active == "true")

        # National-code search is exact by contract; an explicit prefix query
        # is also available and stays B-Tree friendly. Name fields use prefix
        # matching rather than a leading-wildcard table scan.
        national_code = english_numbers(
            self.request.query_params.get("national_code") or ""
        ).strip()
        if national_code:
            qs = qs.filter(national_code=national_code)
        national_code_prefix = english_numbers(
            self.request.query_params.get("national_code_prefix") or ""
        ).strip()
        if national_code_prefix:
            qs = qs.filter(national_code__startswith=national_code_prefix)

        first_name = (self.request.query_params.get("first_name") or "").strip()
        last_name = (self.request.query_params.get("last_name") or "").strip()
        if first_name:
            qs = qs.filter(first_name__istartswith=first_name)
        if last_name:
            qs = qs.filter(last_name__istartswith=last_name)

        search = (self.request.query_params.get("search") or "").strip()
        if search:
            normalized_search = english_numbers(search)
            if normalized_search.isdigit():
                qs = qs.filter(national_code__startswith=normalized_search)
            else:
                qs = qs.filter(
                    models.Q(first_name__istartswith=search)
                    | models.Q(last_name__istartswith=search)
                )

        ordering = (self.request.query_params.get("ordering") or "-created_at").strip()
        ordering_map = {
            "-created_at": ("-created_at", "-pk"),
            "last_name": ("last_name", "first_name", "-created_at", "-pk"),
            "-last_name": ("-last_name", "-first_name", "-created_at", "-pk"),
            "first_name": ("first_name", "last_name", "-created_at", "-pk"),
        }
        return qs.order_by(*ordering_map.get(ordering, ordering_map["-created_at"]))

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

    permission_classes = (IsActiveUser, StrictDjangoModelPermissions, IsPersonOwnerOrManager, ResourceCRUDPermission)
    serializer_class = PersonDetailSerializer

    def get_queryset(self):
        # Same central visibility rule as the list view — a detail route must
        # never widen what the list hides (B1). Writes stay restricted by
        # IsPersonOwnerOrManager; reads of RAW PII are gated per-field by the
        # serializer via can_view_full_person_detail() (view_person_detail).
        return persons_visible_to(self.request.user).select_related(
            "user", "student_profile", "guardian_profile", "staff_profile"
        )


class PersonSoftDeleteView(SoftDeleteView):
    queryset = Person.objects.all()
    resource_key = "persons"


class PersonRestoreView(SoftRestoreView):
    queryset = Person.all_objects.all()
    resource_key = "persons"


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


class GuardianLinkView(views.APIView):
    """
    تکفل یک دانش‌آموز — GET فهرست / POST افزودن یا اصلاح ولی.

    GET  /api/persons/{student_id}/guardians/
        →  [{guardian_id, name, relation, relation_display, custody_status,
             is_primary, phone_override, can_submit_requests, ...}]
    POST /api/persons/{student_id}/guardians/
        body: {"national_code": "...", "relation": "father",
               "custody_status": "under_custody", "is_primary": true}
        ملیِ ولی باید از قبل Person باشد (ساخت ولی تازه کارِ ویزارد
        onboarding است، نه این نقطه‌ی پایانی).

    writes: مدیر/سرپرست. GET: دارندگان view_person_detail (ماسک PII روی
    نام/کدملی ولی برای بقیه‌ی نقش‌ها اعمال می‌شود).
    """

    permission_classes = (IsActiveUser,)
    # NO StrictDjangoModelPermissions: this APIView has no queryset, and the
    # DRF class raises ImproperlyConfigured (→500) rather than 403 there. Row
    # visibility is enforced by persons_visible_to() and writes by the inline
    # role gate below — the same pattern as /api/education/reports/*.

    def get_object(self, person_id):
        person = persons_visible_to(self.request.user).filter(
            pk=person_id, person_type=Person.Type.STUDENT, is_deleted=False,
        ).first()
        if person is None:
            return None
        return person

    def get(self, request, person_id):
        student = self.get_object(person_id)
        if student is None:
            return Response({"error": "دانش‌آموز یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        rows = (
            StudentGuardian.objects
            .filter(student=student, is_deleted=False, is_active=True)
            .select_related("guardian", "guardian__guardian_profile")
        )
        can_full = can_view_full_person_detail(request.user, student)
        out = []
        for link in rows:
            g = link.guardian
            item = {
                "guardian_id": str(g.pk),
                "relation": link.relation,
                "relation_display": link.get_relation_display(),
                "custody_status": link.custody_status,
                "custody_display": link.get_custody_status_display(),
                "is_primary": bool(
                    getattr(g, "guardian_profile", None) and g.guardian_profile.is_primary
                ),
                "can_submit_requests": link.can_submit_requests,
                "can_receive_billing": link.can_receive_billing,
                "is_active": link.is_active,
            }
            if can_full:
                item["first_name"] = g.first_name
                item["last_name"] = g.last_name
                item["national_code"] = g.national_code
                item["mobile"] = link.phone_override or g.mobile
            else:
                item["first_name"] = g.first_name[0] + "‌"
                item["last_name"] = g.last_name
                item["national_code"] = mask_identifier(g.national_code)
                item["mobile"] = mask_identifier(link.phone_override or g.mobile)
            out.append(item)
        return Response(out)

    def post(self, request, person_id):
        if not getattr(request.user, "is_superuser", False) and not (
            set(request.user.role_codes()) & {"manager", "workflow_admin", "hr", "supervisor"}
        ):
            return Response(
                {"error": "فقط مدیر/سرپرست مجاز به تکفل است."},
                status=status.HTTP_403_FORBIDDEN,
            )
        student = self.get_object(person_id)
        if student is None:
            return Response({"error": "دانش‌آموز یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        nc = english_numbers(str(request.data.get("national_code") or "")).strip()
        if not nc:
            return Response(
                {"national_code": ["کد ملی ولی را وارد کنید."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        guardian = Person.objects.filter(
            national_code=nc, is_deleted=False
        ).first()
        if guardian is None:
            return Response(
                {"national_code": ["ولی با این کد ملی ثبت نشده است."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        relation = (request.data.get("relation") or "").strip() or "other"
        if relation not in dict(GuardianProfile.Relation.choices).keys():
            relation = "other"
        custody = (request.data.get("custody_status") or "").strip()
        if custody not in dict(StudentGuardian.Custody.choices).keys():
            custody = StudentGuardian.Custody.UNDER_CUSTODY
        with transaction.atomic():
            link, _ = StudentGuardian.objects.update_or_create(
                student=student, guardian=guardian, is_deleted=False,
                defaults={
                    "relation": relation,
                    "custody_status": custody,
                    "phone_override": str(request.data.get("phone_override") or "").strip(),
                    "can_submit_requests": bool(
                        request.data.get("can_submit_requests", True)
                    ),
                    "can_receive_billing": bool(
                        request.data.get("can_receive_billing", False)
                    ),
                    "is_active": True,
                },
            )
            if guardian.person_type != Person.Type.GUARDIAN and not guardian.has_type(
                Person.Type.GUARDIAN
            ):
                person_service.add_person_type(
                    person=guardian, type_code=Person.Type.GUARDIAN,
                    assigned_by=request.user, provision_user_roles=True,
                )
            GuardianProfile.objects.get_or_create(
                person=guardian,
                defaults={"is_primary": bool(request.data.get("is_primary"))},
            )
            if request.data.get("is_primary"):
                GuardianProfile.objects.filter(person=guardian).update(is_primary=True)
        return Response({"detail": "تکفل ذخیره شد.", "id": str(link.pk)}, status=status.HTTP_201_CREATED)
