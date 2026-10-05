"""Server-rendered persons workspace and its Django-form write endpoint."""
from __future__ import annotations

from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from apps.core.pages import StaffRequiredMixin
from apps.persons.forms import PersonDefinitionForm, TARGET_LABELS
from apps.persons.person_definition import (
    PersonDefinitionPermissionError,
    PersonDefinitionService,
    PersonDefinitionValidationError,
)
from apps.persons.services import DuplicateNationalCodeError, PersonServiceError


def _form_error_payload(form) -> dict[str, list[str]]:
    errors: dict[str, list[str]] = {}
    for field, messages in form.errors.items():
        key = "non_field_errors" if field == "__all__" else field
        errors[key] = [str(message) for message in messages]
    return errors


class PersonsPage(StaffRequiredMixin, TemplateView):
    template_name = "persons.html"

    def setup(self, request, *args, directory="education", **kwargs):
        self.directory = directory
        super().setup(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        form = PersonDefinitionForm(actor=request.user, directory=self.directory)
        if not form.allowed_targets:
            raise PermissionDenied("شما مجوز ایجاد شخص را ندارید.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = PersonDefinitionForm(actor=self.request.user, directory=self.directory)
        actor_roles = set(self.request.user.role_codes())
        context["person_form"] = form
        context["person_page_context"] = {
            "api_url": "/api/persons/?directory=" + self.directory,
            "directory": self.directory,
            "title": "جامعه آموزشی" if self.directory == "education" else "اعضای مجموعه",
            "create_url": "/workspace/persons/staff/create/" if self.directory == "staff" else "/workspace/persons/create/",
            "targets": [
                {"value": value, "label": TARGET_LABELS[value]}
                for value, _label in form.fields["target"].choices
            ],
            "can_create": bool(form.allowed_targets),
            "can_create_user": bool(
                self.directory == "education"
                and actor_roles & {"manager", "hr", "workflow_admin"}
                and self.request.user.has_perm("persons.change_person")
            ),
            "can_manage_passwords": bool(
                self.request.user.is_superuser
                or set(self.request.user.role_codes()) & {"manager", "workflow_admin"}
            ),
            "password_management_url": reverse("workspace-password-management"),
        }
        return context


class PersonCreatePageView(StaffRequiredMixin, View):
    """POST endpoint that keeps Django Form validation in the write path."""

    def post(self, request, *args, **kwargs):
        directory = "staff" if request.path.startswith("/workspace/persons/staff/") else "education"
        form = PersonDefinitionForm(request.POST, actor=request.user, directory=directory)
        if not form.is_valid():
            return JsonResponse({"errors": _form_error_payload(form)}, status=400)

        try:
            person = PersonDefinitionService().create(
                actor=request.user,
                cleaned_data=form.cleaned_data,
            )
        except PersonDefinitionPermissionError as exc:
            return JsonResponse({"errors": {"target": [str(exc)]}}, status=403)
        except DuplicateNationalCodeError as exc:
            return JsonResponse({"errors": {"national_code": [str(exc)]}}, status=400)
        except PersonDefinitionValidationError as exc:
            return JsonResponse({"errors": {"non_field_errors": [str(exc)]}}, status=400)
        except PersonServiceError as exc:
            return JsonResponse({"errors": {"non_field_errors": [str(exc)]}}, status=400)

        return JsonResponse(
            {
                "person": {
                    "id": str(person.pk),
                    "name": person.display_name,
                    "username": person.user.username if person.user_id else person.national_code,
                },
                "message": "شخص با موفقیت ثبت شد و حساب کاربری او ایجاد شد.",
            },
            status=201,
        )
