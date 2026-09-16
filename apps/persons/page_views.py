"""Server-rendered persons workspace and its Django-form write endpoint."""
from __future__ import annotations

from django.http import JsonResponse
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = PersonDefinitionForm(actor=self.request.user)
        context["person_form"] = form
        context["person_page_context"] = {
            "api_url": "/api/persons/",
            "create_url": "/workspace/persons/create/",
            "targets": [
                {"value": value, "label": TARGET_LABELS[value]}
                for value, _label in form.fields["target"].choices
            ],
            "can_create": bool(form.allowed_targets),
        }
        return context


class PersonCreatePageView(StaffRequiredMixin, View):
    """POST endpoint that keeps Django Form validation in the write path."""

    def post(self, request, *args, **kwargs):
        form = PersonDefinitionForm(request.POST, actor=request.user)
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
