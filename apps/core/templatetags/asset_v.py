"""Cache-busting for Pen static assets.

``{% load asset_v %}`` + ``{% asset_v_url 'assets/pen/js/resource.js' %}``
returns the static URL with ``?v=<mtime hash>``. The version changes
automatically whenever the file's mtime changes on disk — browser caches
break themselves after each edit/deploy, with zero manual maintenance.

Missing files fall back to the bare static URL (the template audit flags
missing paths separately).
"""
from __future__ import annotations

import hashlib
import os
import time

from django import template
from django.conf import settings
from django.templatetags.static import static
from django.contrib.staticfiles import finders

register = template.Library()

_MTIME_CACHE: dict[str, float] = {}


def _versioned(rel_path: str) -> str:
    url = static(rel_path)
    try:
        if settings.DEBUG or rel_path not in _MTIME_CACHE:
            found = finders.find(rel_path)
            mtime = os.path.getmtime(found) if found else time.time()
            _MTIME_CACHE[rel_path] = mtime
    except Exception:
        _MTIME_CACHE[rel_path] = time.time()
    token = hashlib.md5(str(_MTIME_CACHE[rel_path]).encode()).hexdigest()[:8]
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}v={token}"


@register.simple_tag
def asset_v_url(rel_path: str) -> str:
    return _versioned(rel_path or "")


@register.filter
def asset_v(rel_path: str) -> str:
    return _versioned(rel_path or "")
