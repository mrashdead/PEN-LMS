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
    "django_filters",
    "corsheaders",
    "apps.core",
    "apps.accounts",
    "apps.workflow",
    "apps.persons",
    "apps.tasks",

]

MIDDLEWARE: list[str] = [
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
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES: dict[str, Any] = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST"),
        "PORT": env("DB_PORT"),
        "CONN_MAX_AGE": env.int("DB_CONN_MAX_AGE", default=60),
        "OPTIONS": {
            "connect_timeout": 10,
            "options": "-c statement_timeout=30000",  # 30s
        },
        "ATOMIC_REQUESTS": False,  # کنترل تراکنش دستی در Engine
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
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

# Logging (minimal production-ready)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
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

# ─────────────────────────────────────────────────────────
#  Persian / Jalali Configuration
# ─────────────────────────────────────────────────────────

# Format localization (numbers, dates)
USE_L10N = True
USE_THOUSAND_SEPARATOR = True

# Django admin: force Persian locale for admin interface
# (already set: LANGUAGE_CODE = "fa-ir")

# Number formatting: use Persian digits in admin
FORMAT_MODULE_PATH = "pen.formats"

# First day of week: Saturday (0) for Persian calendar
FIRST_DAY_OF_WEEK = 6  # Saturday = 6, Sunday = 0, Monday = 1

# Date formats (used as fallback)
DATE_FORMAT = "Y/m/d"
DATETIME_FORMAT = "Y/m/d H:i"
TIME_FORMAT = "H:i"
YEAR_MONTH_FORMAT = "Y/m"
MONTH_DAY_FORMAT = "m/d"
SHORT_DATE_FORMAT = "Y/m/d"
SHORT_DATETIME_FORMAT = "Y/m/d H:i"
DATE_INPUT_FORMATS = [
    "%Y/%m/%d",
    "%Y-%m-%d",
    "%y/%m/%d",
    "%y-%m-%d",
]
TIME_INPUT_FORMATS = [
    "%H:%M",
    "%H:%M:%S",
]
DATETIME_INPUT_FORMATS = [
    "%Y/%m/%d %H:%M",
    "%Y-%m-%d %H:%M",
    "%Y/%m/%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y/%m/%d %H:%M:%S.%f",
]

# Decimal / Thousand separators
THOUSAND_SEPARATOR = ","
DECIMAL_SEPARATOR = "."
NUMBER_GROUPING = 3

# Locale paths (for custom translations)
LOCALE_PATHS = [
    BASE_DIR / "locale",
]

# Django admin extras
if DEBUG:
    # Show admin in Persian (RTL) - already enabled via LANGUAGE_CODE
    pass

# Persian names for months (used in admin)
JALALI_MONTH_NAMES = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
]
