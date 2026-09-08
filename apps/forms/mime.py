"""
MIME type detection adapter.

Production path uses ``python-magic`` (libmagic). A minimal magic-byte sniffer
exists ONLY as an opt-in development/test fallback — it recognizes a few
common signatures and is explicitly NOT equivalent to libmagic.

Policy mirrors sanitizers.py:
  - python-magic installed → always used.
  - Missing and FORMS_ALLOW_SECURITY_FALLBACKS is not True →
    ``MimeTypeDetectorUnavailable`` (fail closed).
  - DEBUG is deliberately NOT consulted (never a security decision).

libmagic requirement: python-magic needs the libmagic shared library
(debian: ``apt install libmagic1``, alpine: ``apk add file``). On Windows use
``python-magic-bin`` which bundles it.
"""
from __future__ import annotations

from django.conf import settings

try:  # pragma: no cover - depends on environment
    import magic as _magic

    HAS_MAGIC = True
except ImportError:  # pragma: no cover
    _magic = None
    HAS_MAGIC = False


class MimeTypeDetectorUnavailable(RuntimeError):
    """Raised when MIME validation is required but no detector is available."""


def _fallback_allowed() -> bool:
    # Explicit opt-in only. Never derived from DEBUG.
    return bool(getattr(settings, "FORMS_ALLOW_SECURITY_FALLBACKS", False))


# (offset, bytes) signatures for the DEV/TEST fallback sniffer.
_SIGNATURES: tuple[tuple[int, bytes], ...] = (
    (0, b"%PDF"),
    (0, b"\x89PNG\r\n\x1a\n"),
    (0, b"\xff\xd8\xff"),  # JPEG
    (0, b"GIF87a"),
    (0, b"GIF89a"),
    (0, b"PK\x03\x04"),  # zip-based: docx, xlsx, pptx, odt
    (0, b"\xd0\xcf\x11\xe0"),  # legacy OLE2: doc, xls
    (0, b"%!PS"),  # postscript
)


def _sniff(head: bytes) -> str:
    if head[:4] == b"PK\x03\x04":
        return "application/zip"
    if head[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        return "application/x-ole-storage"
    if head[:4] == b"%PDF":
        return "application/pdf"
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if head[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if head[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if head[:4] == b"%!PS":
        return "application/postscript"
    return "application/octet-stream"


def detect_mime(fileobj) -> str:
    """
    Detect the real MIME type of a file by content, never by client hint.

    Reads the head of the file and seeks back, so callers keep their cursor.
    """
    pos = fileobj.tell()
    head = fileobj.read(4096)
    fileobj.seek(pos)

    if HAS_MAGIC:
        if hasattr(_magic, "from_buffer"):
            return _magic.from_buffer(head, mime=True) or "application/octet-stream"
        magic_cookie = _magic.open(_magic.MAGIC_MIME_TYPE)  # type: ignore[attr-defined]
        magic_cookie.load()
        return magic_cookie.buffer(head) or "application/octet-stream"

    if not _fallback_allowed():
        raise MimeTypeDetectorUnavailable(
            "File uploads require 'python-magic' (libmagic). Install it, or set "
            "FORMS_ALLOW_SECURITY_FALLBACKS=True only in development/tests."
        )
    return _sniff(head)
