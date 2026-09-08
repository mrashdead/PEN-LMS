"""
Private storage backend for form attachments.

Files are stored under MEDIA_ROOT/private/ and are NEVER served from a public
URL. Downloads go through a permission-checked DRF view. The storage name is a
UUID so the original filename never leaks into the filesystem path.

``PrivateMediaStorage.deconstruct`` intentionally drops runtime-derived kwargs
so the value serialized into migrations is a stable class reference.
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage


class PrivateMediaStorage(FileSystemStorage):
    """Filesystem storage rooted at a non-public directory."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("location", str(Path(settings.MEDIA_ROOT) / "private"))
        kwargs.setdefault("base_url", None)  # no public URL — downloads are view-based
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        path, args, kwargs = super().deconstruct()
        kwargs.pop("location", None)   # computed from MEDIA_ROOT at runtime
        kwargs.pop("base_url", None)   # always None by design
        return path, args, kwargs


private_storage = PrivateMediaStorage()


def build_upload_path(instance, filename: str) -> str:
    """
    ``upload_to`` callback — return a UUID-based storage path.

    The original filename is preserved ONLY as metadata on the model; the
    on-disk name is a UUID with (at most) a short, safe, lowercased extension.
    """
    ext = os.path.splitext(filename or "")[1].lower()
    # Only keep a short alphanumeric extension; strip anything else.
    if not ext or len(ext) > 6 or not ext[1:].isalnum():
        ext = ""
    return f"forms/{uuid.uuid4().hex}{ext}"
