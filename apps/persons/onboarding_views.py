"""
Dynamic onboarding API — the write endpoints of the multi-step create-user
wizard. Kept in their own module (like notification_views in workflow) so
apps/persons/views.py stays the plain-Person CRUD surface.

Endpoints (mounted under /api/persons/onboarding/ by apps/persons/urls.py):

    GET   targets/            step 1 — role picker, filtered by the hierarchy
    GET   schema/?target=X    step 2 — field contract for the chosen target
    POST  create/             atomic submit of the whole wizard

The same ``hierarchy`` + ``onboarding`` contract answers both the JSON API and
HTMX partials; there is no second source of truth for "what may I create".
"""
from __future__ import annotations

from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsActiveUser
from apps.core.utils import english_numbers
from apps.persons import hierarchy
from apps.persons.models import Person
from apps.persons.services import (
    DuplicateNationalCodeError,
    PersonServiceError,
)
from apps.persons.onboarding import (
    FIELD_SPECS,
    OnboardingPermissionError,
    OnboardingValidationError,
    PersonOnboardingService,
    schema_for,
)
from apps.persons.onboarding_serializers import OnboardingCreateSerializer
from apps.persons.serializers import PersonDetailSerializer

onboarding_service = PersonOnboardingService()

TARGET_LABELS = {
    "manager": "مدیر",
    "supervisor": "کارمند سرپرست",
    "employee": "کارمند",
    "teacher": "مدرس",
    "student": "دانش‌آموز",
    "guardian": "ولی/والدین (مستقل)",
}


class OnboardingTargetsView(APIView):
    """GET /api/persons/onboarding/targets/ — step 1 of the wizard."""

    permission_classes = (IsActiveUser, IsAuthenticated)

    def get(self, request):
        roles = set(request.user.role_codes())
        targets = hierarchy.allowed_targets_ordered(
            roles, is_superuser=bool(request.user.is_superuser)
        )
        return Response({
            "targets": [{"value": t, "label": TARGET_LABELS.get(t, t)} for t in targets],
        })


class OnboardingSchemaView(APIView):
    """
    GET /api/persons/onboarding/schema/?target=student — step 2 contract.

    403 (not 404) for a disallowed target mirrors the service guard: the shape
    of another tier's onboarding form is itself an authorization signal.
    """

    permission_classes = (IsActiveUser, IsAuthenticated)

    def get(self, request):
        target = (request.query_params.get("target") or "").strip().lower()
        if target not in FIELD_SPECS:
            return Response(
                {"error": "نوع نامعتبر است."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        schema = schema_for(
            target,
            actor_roles=set(request.user.role_codes()),
            is_superuser=bool(request.user.is_superuser),
        )
        if schema is None:
            return Response(
                {"error": "شما مجاز به ایجاد کاربر با این نوع/نقش نیستید."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response(schema)


class OnboardingCreateView(APIView):
    """
    POST /api/persons/onboarding/create/ — the atomic wizard submit.

    One transaction (service-level @transaction.atomic): Person + profile rows
    + guardian links + user account. Any failure — including a guardian
    collision deep in the repeater — rolls every write back, so the system can
    never hold a student without the parent record the operator just typed.
    """

    permission_classes = (IsActiveUser, IsAuthenticated)

    @staticmethod
    def _existing_by_national_code(payload: dict):
        nc = english_numbers(str(payload.get("national_code") or "")).strip()
        if not nc:
            return None
        return Person.objects.filter(
            national_code=nc, is_deleted=False
        ).first()

    def _replay(self, existing, request):
        return Response({
            "replayed": True,
            "person": PersonDetailSerializer(existing, context={"request": request}).data,
        }, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = OnboardingCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        payload = dict(serializer.validated_data["data"])
        # A multipart upload can carry the photo separately; JSON clients put
        # it in `data` already.
        if request.FILES.get("photo"):
            payload["photo"] = request.FILES["photo"]

        target = serializer.validated_data["target"]

        # Idempotent replay (cheap path): the wizard's double-click would
        # otherwise run the whole atomic block just to roll back. Same
        # national_code live row → 200 with the existing person.
        existing = self._existing_by_national_code(payload)
        if existing is not None:
            return self._replay(existing, request)

        try:
            result = onboarding_service.create(actor=request.user, target=target, payload=payload)
        except OnboardingPermissionError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except DuplicateNationalCodeError:
            # Race path: two same-code requests interleaved past the pre-check;
            # the live-unique constraint (B5) made the loser raise. Not a user
            # error — answer 200 with the winner's row.
            existing = self._existing_by_national_code(payload)
            if existing is not None:
                return self._replay(existing, request)
            return Response(
                {"national_code": ["کد ملی تکراری است."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except OnboardingValidationError as exc:
            detail = exc.args[0] if exc.args else str(exc)
            return Response(
                detail if isinstance(detail, dict) else {"error": str(detail)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except PersonServiceError as exc:
            # Remaining business errors (e.g. grant_role not present in the
            # Role table) — 400 with a message, never a 500.
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:  # noqa: BLE001 — audit then re-raise (500)
            # The atomic block in the service has already rolled every write
            # back; we only record the attempt so a probing client leaves a
            # trail. Re-raising keeps DRF's exception handler in charge of the
            # response shape.
            from apps.core.models import AuditEvent

            AuditEvent.record(
                kind=AuditEvent.Kind.FIELD_CHANGE,
                summary=f"onboarding create failed (target={target}): {exc}",
                actor=request.user,
                metadata={"target": target},
                request=request,
            )
            raise

        person = result["person"]
        return Response({
            "person": PersonDetailSerializer(person, context={"request": request}).data,
            "guardians": [
                PersonDetailSerializer(g, context={"request": request}).data
                for g in result["guardians"]
            ],
            "username": person.user.username if result["user"] else None,
            "created_at": timezone.localtime().isoformat(),
        }, status=status.HTTP_201_CREATED)
