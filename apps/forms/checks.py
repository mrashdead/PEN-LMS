"""
Django system checks for the forms app.

Fails closed in production when the security libraries (bleach, python-magic)
are missing and the explicit fallback flag is not set. This surfaces the
misconfiguration at ``manage.py check`` / deploy time rather than at the first
user upload.
"""
from __future__ import annotations

from django.conf import settings
from django.core.checks import Error, Warning, register

from apps.forms.mime import HAS_MAGIC
from apps.forms.sanitizers import HAS_BLEACH


@register()
def check_forms_security_dependencies(app_configs, **kwargs):
    errors: list[Error] = []
    warnings: list[Warning] = []

    fallback = bool(getattr(settings, "FORMS_ALLOW_SECURITY_FALLBACKS", False))

    if not HAS_BLEACH:
        if fallback:
            warnings.append(
                Warning(
                    "bleach is not installed; rich-text sanitization is using the "
                    "development/test fallback (not equivalent to bleach).",
                    id="forms.W001",
                )
            )
        else:
            errors.append(
                Error(
                    "bleach is required for rich_text fields. Install bleach, or set "
                    "FORMS_ALLOW_SECURITY_FALLBACKS=True only in development.",
                    id="forms.E001",
                )
            )

    if not HAS_MAGIC:
        if fallback:
            warnings.append(
                Warning(
                    "python-magic is not installed; MIME detection is using the "
                    "development/test fallback (not equivalent to libmagic).",
                    id="forms.W002",
                )
            )
        else:
            errors.append(
                Error(
                    "python-magic (libmagic) is required for upload MIME validation. "
                    "Install python-magic + libmagic, or set "
                    "FORMS_ALLOW_SECURITY_FALLBACKS=True only in development.",
                    id="forms.E002",
                )
            )

    return errors + warnings
