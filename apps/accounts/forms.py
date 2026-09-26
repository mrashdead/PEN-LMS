"""Forms for account self-service and administrator-assisted recovery."""
from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class UserSelect(forms.Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        user = getattr(value, "instance", None)
        if user is not None:
            option["attrs"]["data-username"] = user.username
        return option


class PersonNamedUserChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, user):
        person = getattr(user, "person", None)
        first_name = person.first_name if person else user.first_name
        last_name = person.last_name if person else user.last_name
        full_name = " ".join(part for part in (first_name, last_name) if part).strip()
        return full_name or user.username


class AdminPasswordResetForm(forms.Form):
    """Set a new password for a user who cannot change it themselves."""

    target_user = PersonNamedUserChoiceField(
        label="کاربر",
        queryset=get_user_model().objects.none(),
        empty_label="کاربر را انتخاب کنید",
        widget=UserSelect(attrs={
            "class": "form-select",
            "data-password-user-select": "",
        }),
    )
    new_password1 = forms.CharField(
        label="رمز عبور جدید",
        strip=False,
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "autocomplete": "new-password",
        }),
    )
    new_password2 = forms.CharField(
        label="تکرار رمز عبور جدید",
        strip=False,
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "autocomplete": "new-password",
        }),
    )

    def __init__(self, *args, user_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user_queryset is not None:
            self.fields["target_user"].queryset = user_queryset

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get("new_password1")
        password2 = cleaned.get("new_password2")
        target = cleaned.get("target_user")
        if password1 and password2 and password1 != password2:
            self.add_error("new_password2", "دو رمز عبور یکسان نیستند.")
        if password1 and target:
            try:
                validate_password(password1, target)
            except ValidationError as exc:
                self.add_error("new_password1", exc)
            except Exception:
                # ``validate_password`` normally raises django.core.exceptions
                # ValidationError; keep form behavior predictable for custom
                # validators as well.
                self.add_error("new_password1", "این رمز عبور قابل استفاده نیست.")
        return cleaned

    def save(self, *, actor=None):
        target = self.cleaned_data["target_user"]
        target.set_password(self.cleaned_data["new_password1"])
        target.save(update_fields=["password", "updated_at"])
        return target
