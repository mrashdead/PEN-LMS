from __future__ import annotations

from django.apps import AppConfig


class FormsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.forms"
    verbose_name = "Forms (فرم‌ساز پویا)"

    def ready(self) -> None:
        from apps.forms import checks  # noqa: F401  (registers system checks)
