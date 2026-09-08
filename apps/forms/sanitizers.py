"""
Text and rich-text sanitization adapters.

Production path uses the real ``bleach`` library with an explicit allowlist.
A strict allowlist rebuilder built on ``html.parser`` exists ONLY as an
opt-in development/test fallback and is NOT equivalent to bleach.

Policy:
  - bleach installed → always used.
  - bleach missing and FORMS_ALLOW_SECURITY_FALLBACKS is not True →
    ``RichTextSanitizerUnavailable`` (fail closed).
  - DEBUG is deliberately NOT consulted: a security decision must never hinge
    on DEBUG alone. The fallback is enabled only by the explicit setting.

Plain text needs no external library: control characters are stripped and
output is HTML-escaped by Django templates.
"""
from __future__ import annotations

import html
import re
from html.parser import HTMLParser

from django.conf import settings

try:  # pragma: no cover - depends on environment
    import bleach

    HAS_BLEACH = True
except ImportError:  # pragma: no cover
    bleach = None
    HAS_BLEACH = False

# Explicit rich-text allowlist.
ALLOWED_TAGS = [
    "p", "br", "strong", "em", "b", "i", "u", "ul", "ol", "li",
    "h3", "h4", "blockquote", "code", "pre", "a",
]
ALLOWED_ATTRIBUTES = {"a": ["href", "title"]}
ALLOWED_PROTOCOLS = ["http", "https", "mailto"]

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_WS = re.compile(r"[ \t]+")


class RichTextSanitizerUnavailable(RuntimeError):
    """Raised when rich text must be sanitized but no safe engine is available."""


def _fallback_allowed() -> bool:
    # Explicit opt-in only. Never derived from DEBUG.
    return bool(getattr(settings, "FORMS_ALLOW_SECURITY_FALLBACKS", False))


class _AllowlistRebuilder(HTMLParser):
    """DEV/TEST-ONLY fallback: rebuilds HTML emitting only allowlisted tags."""

    VOID_TAGS = {"br"}
    _URL_ATTRS = {"href", "src"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self._open: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag not in ALLOWED_TAGS:
            return
        rendered = [tag]
        for name, value in attrs or []:
            if name not in ALLOWED_ATTRIBUTES.get(tag, []):
                continue
            value = value or ""
            if name in self._URL_ATTRS and not self._safe_url(value):
                continue
            rendered.append(f'{name}="{html.escape(value, quote=True)}"')
        if tag in self.VOID_TAGS:
            self.out.append(f"<{tag}/>")
        else:
            self.out.append(f"<{' '.join(rendered)}>")
            self._open.append(tag)

    def handle_endtag(self, tag):
        if tag in ALLOWED_TAGS and tag not in self.VOID_TAGS and tag in self._open:
            while self._open:
                opened = self._open.pop()
                self.out.append(f"</{opened}>")
                if opened == tag:
                    break

    def handle_data(self, data):
        self.out.append(html.escape(data, quote=False))

    def result(self) -> str:
        while self._open:
            self.out.append(f"</{self._open.pop()}>")
        return "".join(self.out)

    @staticmethod
    def _safe_url(value: str) -> bool:
        lowered = value.strip().lower().replace("\x00", "")
        return bool(lowered) and not re.match(r"^(javascript|data|vbscript|file):", lowered)


def sanitize_text(value: str | None) -> str:
    """Plain text: strip control chars, collapse spaces, trim."""
    if value is None:
        return ""
    value = _CONTROL_CHARS.sub("", str(value))
    value = _WS.sub(" ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def sanitize_rich_text(value: str | None) -> str:
    """Return sanitized HTML safe to render with ``|safe``."""
    if value is None or not str(value).strip():
        return ""
    if HAS_BLEACH:  # production path
        return bleach.clean(
            str(value),
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            protocols=ALLOWED_PROTOCOLS,
            strip=True,
        )
    if not _fallback_allowed():
        raise RichTextSanitizerUnavailable(
            "rich_text fields require the 'bleach' package. Install bleach, or "
            "set FORMS_ALLOW_SECURITY_FALLBACKS=True only in development/tests."
        )
    rebuilder = _AllowlistRebuilder()
    rebuilder.feed(str(value))
    rebuilder.close()
    return rebuilder.result()
