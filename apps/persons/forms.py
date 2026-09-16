"""Django form contract for the server-rendered person wizard."""
from __future__ import annotations

from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from apps.core.utils import english_numbers
from apps.persons import hierarchy
from apps.persons.models import Person


PUBLIC_TARGETS = ("manager", "employee", "teacher", "student")
TARGET_LABELS = {
    "manager": "مدیریت جدید",
    "employee": "کارمند جدید",
    "teacher": "استاد / مدرس",
    "student": "دانش‌آموز",
}


def _text_widget(*, direction: str = "rtl", **attrs):
    return forms.TextInput(attrs={"class": "form-control", "dir": direction, **attrs})


class PersonDefinitionForm(forms.Form):
    """Strict, role-aware form used by the persons workspace page.

    The form deliberately contains the superset of fields used by the four
    visible targets. The template/Vanilla JS hides and disables irrelevant
    fields; ``clean()`` is the second line of defence on the server.
    """

    target = forms.ChoiceField(
        label="نوع کاربر چیست؟",
        choices=(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    first_name = forms.CharField(
        label="نام", max_length=128,
        widget=_text_widget(autocomplete="given-name"),
    )
    last_name = forms.CharField(
        label="نام خانوادگی", max_length=128,
        widget=_text_widget(autocomplete="family-name"),
    )
    national_code = forms.CharField(
        # Keep the browser limit at 10, but let the server-side clean method
        # receive overlong input so it can return the domain-specific error.
        label="کد ملی", max_length=20,
        widget=_text_widget(
            direction="ltr", inputmode="numeric", maxlength="10",
            pattern="[0-9۰-۹]{10}", autocomplete="off",
        ),
        help_text="دقیقاً ۱۰ رقم عددی.",
    )
    phone_number = forms.CharField(
        # The widget prevents normal over-typing; the larger server limit
        # ensures clean_phone_number owns the validation message for crafted
        # requests too.
        label="شماره موبایل", max_length=20,
        widget=_text_widget(
            direction="ltr", inputmode="numeric", maxlength="11",
            pattern="09[0-9۰-۹]{9}", autocomplete="tel",
        ),
        help_text="دقیقاً ۱۱ رقم و با ۰۹ شروع شود.",
    )
    email = forms.CharField(
        # clean_email is intentionally the single server-side validator so
        # invalid addresses receive the same readable Persian error as the
        # other strict fields.
        label="ایمیل (اختیاری)", required=False, max_length=254,
        widget=_text_widget(direction="ltr", autocomplete="email", type="email"),
    )
    gender = forms.ChoiceField(
        label="جنسیت", choices=Person.Gender.choices,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    birth_date = forms.CharField(
        label="تاریخ تولد", required=False,
        widget=_text_widget(
            direction="ltr", inputmode="numeric", placeholder="۱۴۰۵/۰۱/۰۱",
            autocomplete="bday",
        ),
    )

    employee_kind = forms.ChoiceField(
        label="نوع کاربری کارمند", required=False,
        choices=(("supervisor", "سرپرست"), ("ordinary", "عادی")),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    job_title = forms.CharField(
        label="عنوان سمت / پست سازمانی", max_length=128, required=False,
        widget=_text_widget(),
    )
    password = forms.CharField(
        label="کلمه عبور اختصاصی", required=False, strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "dir": "ltr",
                "autocomplete": "new-password",
                "minlength": "8",
            }
        ),
        help_text="برای مدیریت و کارمند الزامی است؛ حداقل ۸ نویسه.",
    )
    specialization = forms.CharField(
        label="تخصص‌ها / دروس قابل تدریس", max_length=256, required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "مثال: ریاضی، فیزیک، پایتون",
            }
        ),
    )

    father_first_name = forms.CharField(
        label="نام پدر", max_length=128, required=False,
        widget=_text_widget(autocomplete="off"),
    )
    father_last_name = forms.CharField(
        label="نام خانوادگی پدر", max_length=128, required=False,
        widget=_text_widget(autocomplete="off"),
    )
    father_phone_number = forms.CharField(
        label="شماره موبایل پدر", max_length=20, required=False,
        widget=_text_widget(direction="ltr", inputmode="numeric", maxlength="11", pattern="09[0-9۰-۹]{9}"),
    )
    mother_first_name = forms.CharField(
        label="نام مادر", max_length=128, required=False,
        widget=_text_widget(autocomplete="off"),
    )
    mother_last_name = forms.CharField(
        label="نام خانوادگی مادر", max_length=128, required=False,
        widget=_text_widget(autocomplete="off"),
    )
    mother_phone_number = forms.CharField(
        label="شماره موبایل مادر", max_length=20, required=False,
        widget=_text_widget(direction="ltr", inputmode="numeric", maxlength="11", pattern="09[0-9۰-۹]{9}"),
    )

    def __init__(self, *args, actor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.actor = actor
        roles = set(actor.role_codes()) if actor and hasattr(actor, "role_codes") else set()
        allowed = hierarchy.allowed_targets(roles, is_superuser=bool(getattr(actor, "is_superuser", False)))
        self.allowed_targets = [target for target in PUBLIC_TARGETS if target in allowed]
        self.fields["target"].choices = [
            (target, TARGET_LABELS[target]) for target in self.allowed_targets
        ]
        for name, field in self.fields.items():
            if field.help_text:
                field.widget.attrs["aria-describedby"] = f"help-{name}"

    @staticmethod
    def _normalize_phone(value: str) -> str:
        return english_numbers(value or "").strip()

    def clean_national_code(self) -> str:
        value = english_numbers(self.cleaned_data.get("national_code") or "").strip()
        if len(value) != 10 or not value.isdigit():
            raise forms.ValidationError("کد ملی باید دقیقاً ۱۰ رقم عددی باشد.")
        if Person.objects.filter(national_code=value, is_deleted=False).exists():
            raise forms.ValidationError("شخصی با این کد ملی از قبل ثبت شده است.")
        return value

    def clean_phone_number(self) -> str:
        value = self._normalize_phone(self.cleaned_data.get("phone_number"))
        if len(value) != 11 or not value.isdigit() or not value.startswith("09"):
            raise forms.ValidationError("شماره موبایل باید دقیقاً ۱۱ رقم و با ۰۹ شروع شود.")
        return value

    def clean_email(self) -> str:
        value = (self.cleaned_data.get("email") or "").strip().lower()
        if value:
            try:
                validate_email(value)
            except ValidationError:
                raise forms.ValidationError("قالب ایمیل معتبر نیست.")
        return value

    def _clean_parent_phone(self, name: str) -> str:
        value = self._normalize_phone(self.cleaned_data.get(name))
        if value and (len(value) != 11 or not value.isdigit() or not value.startswith("09")):
            self.add_error(name, "شماره موبایل باید دقیقاً ۱۱ رقم و با ۰۹ شروع شود.")
            return ""
        return value

    def clean_father_phone_number(self) -> str:
        return self._clean_parent_phone("father_phone_number")

    def clean_mother_phone_number(self) -> str:
        return self._clean_parent_phone("mother_phone_number")

    def clean_password(self) -> str:
        value = self.cleaned_data.get("password") or ""
        if value:
            try:
                validate_password(value)
            except ValidationError as exc:
                raise forms.ValidationError(list(exc.messages))
        return value

    def clean(self):
        cleaned = super().clean()
        target = cleaned.get("target")
        if target not in self.allowed_targets:
            self.add_error("target", "شما مجاز به ایجاد این نوع کاربر نیستید.")
            return cleaned

        if target == "student":
            father_phone = cleaned.get("father_phone_number") or ""
            mother_phone = cleaned.get("mother_phone_number") or ""
            if not father_phone and not mother_phone:
                self.add_error(None, "ثبت حداقل یکی از شماره موبایل پدر یا مادر الزامی است.")
            for prefix, label, phone in (
                ("father", "پدر", father_phone),
                ("mother", "مادر", mother_phone),
            ):
                if phone and not (cleaned.get(f"{prefix}_first_name") and cleaned.get(f"{prefix}_last_name")):
                    self.add_error(None, f"نام و نام خانوادگی {label} را کامل کنید.")

        if target == "employee":
            if not cleaned.get("employee_kind"):
                self.add_error("employee_kind", "نوع کاربری کارمند را انتخاب کنید.")

        if target in {"employee", "manager"} and not cleaned.get("job_title"):
            self.add_error("job_title", "عنوان سمت / پست سازمانی الزامی است.")

        if target in {"employee", "manager"} and not cleaned.get("password"):
            self.add_error("password", "برای کارمند و مدیریت، کلمه عبور اختصاصی الزامی است.")

        return cleaned

    def to_onboarding_payload(self) -> tuple[str, dict]:
        if not self.is_valid():
            raise ValueError("فرم ابتدا باید معتبر شود.")
        data = {
            "first_name": self.cleaned_data["first_name"].strip(),
            "last_name": self.cleaned_data["last_name"].strip(),
            "national_code": self.cleaned_data["national_code"],
            "mobile": self.cleaned_data["phone_number"],
            "email": self.cleaned_data.get("email") or "",
            "gender": self.cleaned_data.get("gender") or Person.Gender.NOT_SPECIFIED,
            "birth_date": self.cleaned_data.get("birth_date") or "",
            "job_title": self.cleaned_data.get("job_title") or "",
            "specialization": self.cleaned_data.get("specialization") or "",
            # New person definitions always provision a dashboard account.
            "auto_create_user": True,
            "password": self.cleaned_data.get("password") or "",
        }
        target = self.cleaned_data["target"]
        if target == "student":
            data["student_code"] = f"STU-{data['national_code']}"
            data["parents"] = {
                "father_first_name": self.cleaned_data.get("father_first_name") or "",
                "father_last_name": self.cleaned_data.get("father_last_name") or "",
                "father_phone": self.cleaned_data.get("father_phone_number") or "",
                "mother_first_name": self.cleaned_data.get("mother_first_name") or "",
                "mother_last_name": self.cleaned_data.get("mother_last_name") or "",
                "mother_phone": self.cleaned_data.get("mother_phone_number") or "",
            }
        elif target in {"employee", "manager", "teacher"}:
            data["employee_code"] = f"EMP-{data['national_code']}"
        if target == "employee" and self.cleaned_data.get("employee_kind") == "supervisor":
            data["grant_role"] = "supervisor"
        return target, data
