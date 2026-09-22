"""
Playhouse AppConfig — registers the app under ``apps.playhouse``.
"""
from __future__ import annotations

from django.apps import AppConfig


class PlayhouseConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.playhouse"
    verbose_name = "خانه بازی"
    verbose_name_plural = "خانه بازی"