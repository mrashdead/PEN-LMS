# pen/settings.py
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
)

environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

SECRET_KEY: str = env("SECRET_KEY")
DEBUG: bool = env("DEBUG")
ALLOWED_HOSTS: list[str] = env("ALLOWED_HOSTS")

# Application definition

INSTALLED_APPS: list[str] = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "rest_framework",
    "rest_framework.authtoken",
    "django_filters",
    "corsheaders",
    "drf_spectacular",
    "apps.core",
    "apps.accounts",
    "apps.workflow",
    "apps.persons",
    "apps.tasks",
    "apps.academics",
    "apps.education",
    "apps.forms",
    "apps.messaging",
    "apps.org",
    "apps.reports",
    "apps.playhouse",
    "apps.leads",
    "apps.staff",
    "apps.calls",
]

MIDDLEWARE: list[str] = [
    "apps.core.middleware.RequestIDMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "pen.urls"
WSGI_APPLICATION = "pen.wsgi.application"
ASGI_APPLICATION = "pen.asgi.application"

TEMPLATES: list[dict[str, Any]] = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # All UI templates live under frontend/Admin/pen-templates (the
        # purchased Domiex admin theme lives beside it in frontend/Admin/src).
        # This directory is intentionally OUTSIDE STATICFILES_DIRS so template
        # source is never served as a static file.
        "DIRS": [BASE_DIR / "frontend" / "Admin" / "pen-templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            # Explicit tag-library registration (startup import — immune to
            # negative-discovery caching when a templatetags package is added
            # to a running process).
            "libraries": {
                "asset_v": "apps.core.templatetags.asset_v",
                "rbac": "apps.core.templatetags.rbac",
            },
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.user_flags",
            ],
        },
    },
]

DATABASES: dict[str, Any]
# The project's real backend is PostgreSQL; defaulting to sqlite here silently
# created a stray sqlite file when DB_ENGINE was missing from .env. Keep the
# explicit sqlite opt-in for throwaway local runs, but default to postgres.
_db_engine = env("DB_ENGINE", default="django.db.backends.postgresql")
if _db_engine == "django.db.backends.sqlite3":
    DATABASES = {
        "default": {
            "ENGINE": _db_engine,
            "NAME": env("DB_NAME", default=str(BASE_DIR / "db.sqlite3")),
        }
    }
else:
    _db_name = env("DB_NAME")
    _test_db_name = env("TEST_DB_NAME", default=f"test_{_db_name}")
    if _test_db_name == _db_name:
        raise ValueError("TEST_DB_NAME must differ from DB_NAME")
    DATABASES = {
        "default": {
            "ENGINE": _db_engine,
            "NAME": _db_name,
            "USER": env("DB_USER"),
            "PASSWORD": env("DB_PASSWORD"),
            "HOST": env("DB_HOST"),
            "PORT": env("DB_PORT"),
            "CONN_MAX_AGE": env.int("DB_CONN_MAX_AGE", default=60),
            "OPTIONS": {
                "connect_timeout": 10,
                "options": "-c statement_timeout=30000",
            },
            "ATOMIC_REQUESTS": False,
            # Django's test runner creates this database and drops it afterwards.
            "TEST": {"NAME": _test_db_name},
        }
    }

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = env("LANGUAGE_CODE", default="fa-ir")
TIME_ZONE = env("TIME_ZONE", default="Asia/Tehran")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# All UI statics live beside the templates: the purchased Domiex theme ships
# compiled RTL CSS, fonts and UMD libs in frontend/Admin/src/assets, and the
# Pen-specific layer sits in assets/pen/{css,js}. (frontend/Admin/pen-templates
# holds Django template SOURCE and is deliberately not a static dir.)
STATICFILES_DIRS = [
    BASE_DIR / "frontend" / "Admin" / "src",
]
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.core.authentication.ExpiringTokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "apps.core.permissions.IsActiveUser",
    ],
    # Audit every API denial (403/404) into core.AuditEvent (§13-4).
    "EXCEPTION_HANDLER": "apps.core.exceptions.audited_exception_handler",
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "30/minute",
        "user": "300/minute",
        "login": "5/minute",
        "password": "5/minute",
        "form_write": "30/minute",
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Pen LMS API",
    "DESCRIPTION": "قرارداد رسمی API پن",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# ─────────────────────────────────────────────────────────────────────────────
# Email + notification delivery (B6 / outbox worker).
# Default to the console backend in DEBUG so a dev box needs no SMTP; in
# production set EMAIL_BACKEND to django.core.mail.backends.smtp.EmailBackend
# plus the EMAIL_HOST* vars. flush_notifications / the Celery beat task read
# these — a failing mailer only marks the outbox row failed, never rolls back
# a workflow transition (report §6/§13-9).
# ─────────────────────────────────────────────────────────────────────────────
EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend" if DEBUG
    else "django.core.mail.backends.smtp.EmailBackend",
)
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=25)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=False)
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="Pen LMS <noreply@example.com>")
SERVER_EMAIL = env("SERVER_EMAIL", default=DEFAULT_FROM_EMAIL)
EMAIL_TIMEOUT = env.int("EMAIL_TIMEOUT", default=10)

# Parent report SMS adapter. The application sends a provider-neutral JSON
# payload; deployments set the actual provider endpoint and bearer token.
SMS_GATEWAY_URL = env("SMS_GATEWAY_URL", default="")
SMS_GATEWAY_TOKEN = env("SMS_GATEWAY_TOKEN", default="")
SMS_SENDER = env("SMS_SENDER", default="")

# ─────────────────────────────────────────────────────────────────────────────
# SLA defaults (report §15-9). The SLA scan command uses these when a State
# declares no per-state override. reminder_lead_hours = how long BEFORE the
# due date a "near deadline" nudge fires.
# ─────────────────────────────────────────────────────────────────────────────
SLA_REMINDER_LEAD_HOURS = env.int("SLA_REMINDER_LEAD_HOURS", default=4)
# Escalation target role when a task blows its deadline (empty = no escalate).
SLA_ESCALATION_ROLE = env("SLA_ESCALATION_ROLE", default="manager")

# The only supported production scheduler/worker is Celery with Redis. The
# management commands remain the task bodies and local/manual entry points.
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://127.0.0.1:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://127.0.0.1:6379/1")
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_BEAT_SCHEDULE = {
    "flush-notifications-every-minute": {
        "task": "pen.workflow.flush_notifications",
        "schedule": 60.0,
        "options": {"expires": 55},
    },
    "scan-workflow-sla-every-five-minutes": {
        "task": "pen.workflow.scan_sla",
        "schedule": 300.0,
        "options": {"expires": 290},
    },
    "reconcile-attendance-projections-every-five-minutes": {
        "task": "pen.forms.reconcile_education_projections",
        "schedule": 300.0,
        "options": {"expires": 290},
    },
}

# CORS: deny cross-origin requests by default. Add trusted frontend origins
# through the environment variable in deployments.
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CORS_ALLOW_CREDENTIALS = env.bool("CORS_ALLOW_CREDENTIALS", default=False)

# Browser security. Secure cookies are enabled only in production because
# local HTTP development cannot send Secure cookies.
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False  # JS API client needs the CSRF cookie.
CSRF_COOKIE_SAMESITE = "Lax"
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
    SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} request_id={request_id} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "filters": ["request_id"],
        },
    },
    "filters": {
        "request_id": {"()": "apps.core.middleware.RequestIDLogFilter"},
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "apps.workflow": {"level": "DEBUG", "propagate": False, "handlers": ["console"]},
        "apps.tasks": {"level": "DEBUG", "propagate": False, "handlers": ["console"]},
    },
}

# Persian / Jalali Configuration
USE_L10N = True
USE_THOUSAND_SEPARATOR = True
FORMAT_MODULE_PATH = "pen.formats"
FIRST_DAY_OF_WEEK = 6
DATE_FORMAT = "Y/m/d"
DATETIME_FORMAT = "Y/m/d H:i"
TIME_FORMAT = "H:i"
YEAR_MONTH_FORMAT = "Y/m"
MONTH_DAY_FORMAT = "m/d"
SHORT_DATE_FORMAT = "Y/m/d"
SHORT_DATETIME_FORMAT = "Y/m/d H:i"
DATE_INPUT_FORMATS = [
    "%Y/%m/%d", "%Y-%m-%d", "%y/%m/%d", "%y-%m-%d",
]
TIME_INPUT_FORMATS = ["%H:%M", "%H:%M:%S"]
DATETIME_INPUT_FORMATS = [
    "%Y/%m/%d %H:%M", "%Y-%m-%d %H:%M",
    "%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S.%f", "%Y/%m/%d %H:%M:%S.%f",
]
THOUSAND_SEPARATOR = ","
DECIMAL_SEPARATOR = "."
NUMBER_GROUPING = 3
LOCALE_PATHS = [BASE_DIR / "locale"]
JALALI_MONTH_NAMES = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
]

# ────────────────────────────────────────
#  API Auth: Token expiry (optional)
#  Set TOKEN_EXPIRY_DAYS=0 to disable expiry
# ────────────────────────────────────────
TOKEN_EXPIRY_DAYS = env.int("TOKEN_EXPIRY_DAYS", default=90)

# Forms app security. bleach + python-magic are the production path; when they
# are missing, rich-text and MIME validation fail closed unless this explicit
# development/test opt-in is set. DEBUG alone never enables the fallback.
FORMS_ALLOW_SECURITY_FALLBACKS = env.bool("FORMS_ALLOW_SECURITY_FALLBACKS", default=False)
