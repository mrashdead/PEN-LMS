"""Parse (lex) every pen-templates file with Django's real template engine.

No settings/database required — Lexer/Parser are self-contained. This catches
real Django template syntax errors (unclosed tags, bad filters, stray %}) that
a regex audit cannot.
"""
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

try:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pen.settings")
    import django

    django.setup()
    from django.template import engines
except ImportError:
    print("django not importable in this environment; parse audit skipped")
    sys.exit(0)

engine = engines["django"]

failures = 0
tpl_root = os.path.join(BASE, "frontend", "Admin", "pen-templates")
for dirpath, _, files in os.walk(tpl_root):
    for name in sorted(files):
        if not name.endswith(".html"):
            continue
        path = os.path.join(dirpath, name)
        rel = os.path.relpath(path, tpl_root)
        try:
            with open(path, encoding="utf-8") as fh:
                source = fh.read()
            engine.from_string(source)  # parse — will raise on any syntax error
            print(f"  OK  {rel}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"FAIL  {rel}: {exc}")

if failures:
    print(f"\n{failures} template(s) failed to parse")
    sys.exit(1)
print("\nALL TEMPLATES PARSE CLEANLY")
