"""Offline template audit for pen-templates.

Checks (no Django required — pure text/regex):
  1. Tag balance: every {% block %}/{% if %}/{% for %}/{% with %}/{% comment %}
     has its matching end tag.
  2. Every {% url 'name' %} resolves to a name defined in the project urlconfs.
  3. Every {% static 'path' %} file exists under frontend/Admin/src or static/.
  4. Every {% extends %} / {% include %} path exists under pen-templates/.
  5. Every {% load %} library exists (django builtin or <app>/templatetags/).
  6. Emits render_test/index.html: static snapshots (chrome inlined from
     base.html) so the design can be verified in a plain browser WITHOUT
     Django/Postgres. Open render_test/dashboard.html etc. directly.
"""
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL_ROOT = os.path.join(BASE, "frontend", "Admin", "pen-templates")
STATIC_ROOTS = [os.path.join(BASE, "frontend", "Admin", "src")]

errors = []

# ── gather url names from urlconfs ───────────────────────────────────────
URL_NAME_RE = re.compile(r"""name\s*=\s*['"]([\w:-]+)['"]""")
import glob as _glob

url_names = set()
url_files = [os.path.join(BASE, "pen", "urls.py")]
url_files += _glob.glob(os.path.join(BASE, "apps", "*", "*urls.py"))
for f in url_files:
    if os.path.isfile(f):
        url_names.update(URL_NAME_RE.findall(open(f, encoding="utf-8").read()))
# DRF login/logout + auth token names
url_names |= {"login", "logout", "api-token-auth"}

# ── gather template tag libraries ────────────────────────────────────────
tag_libs = {"static", "i18n", "l10n", "messages", "tz", "cache"}
for app_dir in sorted(_glob.glob(os.path.join(BASE, "apps", "*", "templatetags", "*.py"))):
    name = os.path.basename(app_dir)
    if name != "__init__.py":
        tag_libs.add(name[:-3])

# ── walk templates ───────────────────────────────────────────────────────
OPEN_PAIR = [("block", "endblock"), ("if", "endif"), ("for", "endfor"),
             ("with", "endwith"), ("comment", "endcomment")]

tag_re = re.compile(r"\{%\s*.*?\s*%\}", re.S)
comment_re = re.compile(r"\{%[-\s]*comment[-\s]*%\}.*?\{%[-\s]*endcomment[-\s]*%\}", re.S)

def walk(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    rel = os.path.relpath(path, TPL_ROOT)

    # Strip {% comment %}…{% endcomment %} so literal tag-words inside prose
    # (e.g. "{% with %}" mentioned in a docstring) don't skew the balance.
    tags = tag_re.findall(comment_re.sub("", text))
    # 1) balance (only top-level keywords, not elif/else/empty which are fine)
    for opener, closer in OPEN_PAIR:
        opens = sum(1 for t in tags if re.match(r"\{%-?\s*" + opener + r"\b", t))
        closes = sum(1 for t in tags if re.match(r"\{%-?\s*" + closer + r"\b", t))
        if opens != closes:
            errors.append(f"{rel}: {opener}/{closer} imbalance ({opens} vs {closes})")

    # 2) url names
    for m in re.finditer(r"\{%\s*url\s+['\"]([^'\"]+)['\"]", text):
        name = m.group(1)
        if name not in url_names:
            errors.append(f"{rel}: url '{name}' not found in urlconfs")

    # 3) static paths ({% static %} and {% asset_v_url %})
    for m in re.finditer(r"\{%\s*(?:static|asset_v_url)\s+['\"]([^'\"]+)['\"]", text):
        p = m.group(1)
        if not any(os.path.isfile(os.path.join(r, p)) for r in STATIC_ROOTS):
            errors.append(f"{rel}: static file missing: {p}")

    # 4) extends / include
    for kw in ("extends", "include"):
        for m in re.finditer(r"\{%\s*" + kw + r"\s+['\"]([^'\"]+)['\"]", text):
            p = m.group(1)
            if p.startswith("admin/") or p.startswith("rest_framework/") or p.startswith("registration/"):
                continue
            full = os.path.join(TPL_ROOT, p)
            if not os.path.isfile(full):
                errors.append(f"{rel}: {kw} target missing: {p}")

    # 5) load libs
    for m in re.finditer(r"\{%\s*load\s+([^%]+?)\s*%\}", text):
        for lib in m.group(1).split():
            if lib == "as" or lib == "from":
                continue
            if lib not in tag_libs:
                errors.append(f"{rel}: unknown template lib '{lib}'")

for dirpath, _, files in os.walk(TPL_ROOT):
    for f in sorted(files):
        if f.endswith(".html"):
            walk(os.path.join(dirpath, f))

print("url names discovered:", len(url_names))
if errors:
    print(f"\n{len(errors)} PROBLEM(S):")
    for e in errors:
        print(" -", e)
    sys.exit(1)
print("ALL TEMPLATE AUDIT CHECKS PASSED")


# ── 6) static render previews (no Django needed) ─────────────────────
# Emits render_test/*.html under pen-templates with {% static %} paths
# resolved relative to frontend/Admin/src so file:// preview works.
STATIC_URL_PREFIX = "../src/"  # render_test/ sits beside src/ inside pen-templates

def to_preview(html):
    html = re.sub(r"\{%\s*static\s+['\"]([^'\"]+)['\"]\s*%\}", STATIC_URL_PREFIX + r"\1", html)
    html = re.sub(r"\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}", "", html, flags=re.S)
    html = re.sub(r"\{#.*?#\}", "", html, flags=re.S)   # {# … #} incl. multiline
    html = re.sub(r"\{%.*?%\}", "", html, flags=re.S)      # strip remaining tags
    html = re.sub(r"\{\{.*?\}\}", "…", html, flags=re.S)   # strip variables
    return html

preview_dir = os.path.join(TPL_ROOT, "render_test")
os.makedirs(preview_dir, exist_ok=True)

def read_tpl(rel):
    with open(os.path.join(TPL_ROOT, rel), encoding="utf-8") as fh:
        return fh.read()

def extract(src, block):
    m = re.search(r"\{%\s*block\s+" + block + r"\s*%\}(.*?)\{%\s*endblock\s*%\}", src, re.S)
    return m.group(1) if m else ""

INCLUDE_RE = re.compile(r"\{%\s*include\s+['\"]([^'\"]+)['\"][^%]*%\}")

def inline_includes(src, depth=0):
    """Recursively replace {% include "partials/x.html" %} with its content."""
    if depth > 6:
        return src
    def repl(m):
        try:
            return read_tpl(m.group(1))
        except OSError:
            return ""
    out = INCLUDE_RE.sub(repl, src)
    return out if out == src else inline_includes(out, depth + 1)

made = []
for rel in ["dashboard/home.html", "forms/submission_list.html"]:
    page = read_tpl(rel)
    base = read_tpl("base.html")
    merged = base
    merged = merged.replace("{% block title %}Pen LMS{% endblock %}", extract(page, "title"))
    for blk in ("head_css", "extra_head", "page_heading", "content", "page_js"):
        pat = re.compile(r"\{%\s*block\s+" + blk + r"\s*%\}(.*?)\{%\s*endblock\s*%\}", re.S)
        merged = pat.sub(lambda m, b=blk: extract(page, b) or m.group(1) if extract(page, b) else "", merged, count=1)
    merged = inline_includes(merged)
    out_name = os.path.basename(rel)
    with open(os.path.join(preview_dir, out_name), "w", encoding="utf-8") as fh:
        fh.write(to_preview(merged))
    made.append(out_name)

print("render previews:", ", ".join(made), "→ frontend/Admin/pen-templates/render_test/")
