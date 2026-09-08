"""
Seed the dynamic-form schema catalog.

    python manage.py seed_form_schemas [--dry-run] [--force] [--schema-version N]
                                       [--deactivate-old] [slug ...]

Contract (fail-closed, all-or-nothing):

  1. Every selected schema definition is structurally pre-validated
     (``validate_form_fields``) BEFORE any database write.
  2. Every relation key used by the selection is resolved through the fixed
     server-side registry. Required targets that are not installed (e.g. the
     planned ``education`` app models Lesson/Course/CourseOffering/Department)
     abort the whole run with ONE actionable error listing every affected
     schema and relation — zero database changes.
  3. Optional targets that are not installed may only be replaced by their
     explicitly declared fallback (currently ``academic.venue`` → text), and
     the substitution is recorded in ``FormSchema.metadata``.
  4. Successful writes happen in a single atomic transaction.
  5. Idempotent: an existing (slug, version) row is skipped unless --force.
     --deactivate-old marks every other version of the slug inactive.

In the current repository state the full catalog cannot seed (the education
app does not exist yet); ``seed_form_workflows`` followed by
``seed_form_schemas attendance grade-report`` works today because those schemas
only reference installed models.
"""
from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Role
from apps.forms import relations
from apps.forms.models import FormSchema
from apps.forms.schema_validation import SchemaDefinitionError, validate_form_fields

# ─────────────────────────────────────────────────────────────────────────────
# Catalog — field definitions follow apps/forms/schema_validation.py and the
# project spec (slugs: lesson, course, course-offering, class-session-setup,
# attendance, grade-report, lead-assessment).
# ─────────────────────────────────────────────────────────────────────────────

def _f(key: str, ftype: str, order: int, label: str, **extra: Any) -> dict:
    definition: dict[str, Any] = {"key": key, "type": ftype, "order": order, "label": label}
    definition.update(extra)
    return definition


SCHEMA_CATALOG: dict[str, dict[str, Any]] = {
    # ── 3.1 lesson (needs education.Lesson for prerequisites → fails closed) ──
    "lesson": {
        "title": "تعریف درس",
        "description": "فرم تعریف درس و سرفصل آن.",
        "version": 1,
        "allowed_roles": ["manager", "hr", "workflow_admin"],
        "workflow_code": "form-approval",
        "fields": [
            _f("lesson_title", "text", 1, "عنوان درس", required=True,
               validators={"min_length": 3, "max_length": 200}),
            _f("syllabus_file", "file", 2, "فایل سرفصل", required=True,
               validators={"allowed_extensions": ["pdf", "docx"],
                           "max_file_size": 10485760}),
            _f("duration_hours", "number", 3, "ساعات تدریس", required=True,
               validators={"min_value": 1, "max_value": 1000}),
            _f("description", "textarea", 4, "توضیحات", max_length=5000),
            _f("target_audience", "multi_select", 5, "مخاطبان", required=True, options=[
                {"value": "student", "label": "دانش‌آموز"},
                {"value": "employee", "label": "کارمند"},
                {"value": "teacher", "label": "معلم"},
                {"value": "parent", "label": "والدین"},
            ]),
            _f("prerequisites", "multi_relation", 6, "پیش‌نیازها",
               relation={"registry_key": "academic.lesson", "lookup": "id",
                         "required": False}),
            _f("assessment_method", "select", 7, "نحوه ارزشیابی", required=True, options=[
                {"value": "written", "label": "کتبی"},
                {"value": "oral", "label": "شفاهی"},
                {"value": "project", "label": "پروژه"},
                {"value": "none", "label": "بدون ارزشیابی"},
            ]),
            _f("required_equipment", "textarea", 8, "تجهیزات مورد نیاز", max_length=2000),
            _f("venue_type", "select", 9, "نوع مکان", required=True, options=[
                {"value": "classroom", "label": "کلاس"},
                {"value": "lab", "label": "آزمایشگاه"},
                {"value": "online", "label": "آنلاین"},
                {"value": "hybrid", "label": "ترکیبی"},
            ]),
            _f("learning_resources", "textarea", 10, "منابع یادگیری", max_length=2000),
            _f("topics", "textarea", 11, "مباحث", required=True, max_length=5000),
            _f("tuition_amount", "number", 12, "هزینه",
               validators={"min_value": 0, "max_value": 1000000000}),
        ],
    },
    # ── 3.2 course (needs education.Course/Department/Lesson) ──
    "course": {
        "title": "تعریف دوره",
        "description": "فرم تعریف دوره آموزشی.",
        "version": 1,
        "allowed_roles": ["manager", "hr", "workflow_admin"],
        "workflow_code": "form-approval",
        "fields": [
            _f("course_title", "text", 1, "عنوان دوره", required=True,
               validators={"min_length": 3, "max_length": 200}),
            _f("department", "relation", 2, "گروه آموزشی", required=True,
               relation={"registry_key": "academic.department", "lookup": "id"}),
            _f("description", "textarea", 3, "توضیحات", max_length=5000),
            _f("lessons", "multi_relation", 4, "دروس دوره", required=True,
               relation={"registry_key": "academic.lesson", "lookup": "id"}),
            _f("objectives", "textarea", 5, "اهداف یادگیری", required=True, max_length=5000),
        ],
    },
    # ── 3.3 course-offering (needs education.Course; venue has text fallback) ──
    "course-offering": {
        "title": "برگزاری دوره",
        "description": "فرم پیشنهاد برگزاری دوره.",
        "version": 1,
        "allowed_roles": ["manager", "hr", "workflow_admin", "employee"],
        "workflow_code": "form-approval",
        "fields": [
            _f("course", "relation", 1, "دوره", required=True,
               relation={"registry_key": "academic.course", "lookup": "id"}),
            _f("capacity", "number", 2, "ظرفیت", required=True,
               validators={"min_value": 1, "max_value": 500}),
            _f("start_date", "date", 3, "تاریخ شروع", required=True),
            _f("session_details", "textarea", 4, "جزئیات جلسات", required=True, max_length=5000),
            _f("venue", "relation", 5, "مکان برگزاری",
               relation={"registry_key": "academic.venue", "lookup": "id",
                         "required": False}),
            _f("instructor", "relation", 6, "مدرس", required=True,
               relation={"registry_key": "persons.person", "lookup": "id",
                         "filter": {"person_type": "teacher", "is_active": True}}),
            _f("schedule", "textarea", 7, "زمان‌بندی", required=True, max_length=2000),
        ],
    },
    # ── 3.4 class-session-setup (needs education.CourseOffering/Lesson) ──
    "class-session-setup": {
        "title": "نهایی‌سازی جلسات کلاس",
        "description": "فرم تایید زمان و مکان جلسات یک دوره در حال برگزاری.",
        "version": 1,
        "allowed_roles": ["manager", "hr", "workflow_admin"],
        "workflow_code": "form-approval",
        "fields": [
            _f("course_offering", "relation", 1, "دوره در حال برگزاری", required=True,
               relation={"registry_key": "academic.course_offering", "lookup": "id"}),
            _f("lesson", "relation", 2, "درس", required=True,
               relation={"registry_key": "academic.lesson", "lookup": "id"}),
            _f("instructor", "relation", 3, "مدرس", required=True,
               relation={"registry_key": "persons.person", "lookup": "id",
                         "filter": {"person_type": "teacher", "is_active": True}}),
            _f("venue", "relation", 4, "مکان",
               relation={"registry_key": "academic.venue", "lookup": "id",
                         "required": False}),
            _f("confirmed_start_date", "date", 5, "تاریخ شروع قطعی", required=True),
            _f("confirmed_schedule", "textarea", 6, "زمان‌بندی قطعی", required=True,
               max_length=2000),
        ],
    },
    # ── 3.5 attendance (installed models only — seeds today) ──
    "attendance": {
        "title": "ثبت حضور و غیاب",
        "description": "فرم ثبت گروهی حضور/غیاب دانش‌آموزان یک کلاس در یک جلسه.",
        "version": 1,
        "allowed_roles": ["teacher", "manager"],
        "workflow_code": "form-review",
        "fields": [
            _f("class_group", "relation", 1, "کلاس", required=True,
               relation={"registry_key": "academic.class_group", "lookup": "id",
                         "filter": {"is_active": True}}),
            _f("session_number", "number", 2, "شماره جلسه", required=True,
               validators={"min_value": 1, "max_value": 500}),
            _f("attendance_list", "attendance_table", 3, "حضور دانش‌آموزان",
               required=True, statuses=["present", "absent", "late", "excused"],
               max_rows=200),
            _f("session_start", "time", 4, "ساعت شروع", required=True),
            _f("session_end", "time", 5, "ساعت پایان", required=True,
               after="session_start"),
        ],
    },
    # ── 3.6 grade-report — descriptive evaluation, no numeric grades ──
    "grade-report": {
        "title": "کارنامه توصیفی",
        "description": "ارزشیابی توصیفی (قبول/مردود) با یادداشت معلم.",
        "version": 1,
        "allowed_roles": ["teacher", "manager"],
        "workflow_code": "form-review",
        "fields": [
            _f("class_group", "relation", 1, "کلاس", required=True,
               relation={"registry_key": "academic.class_group", "lookup": "id",
                         "filter": {"is_active": True}}),
            _f("instructor", "relation", 2, "مدرس", required=True,
               relation={"registry_key": "persons.person", "lookup": "id",
                         "filter": {"person_type": "teacher", "is_active": True}}),
            _f("grade_list", "grade_table", 3, "ارزشیابی دانش‌آموزان", required=True,
               results=["passed", "failed"], max_rows=200),
        ],
    },
    # ── 3.7 lead-assessment (recommended_course needs education.Course) ──
    "lead-assessment": {
        "title": "ارزیابی تعیین سطح",
        "description": "فرم لید و ارزیابی تعیین سطح (new → assessed → enrolled/closed).",
        "version": 1,
        "allowed_roles": ["employee", "hr", "manager", "workflow_admin"],
        "workflow_code": "lead-assessment",
        "fields": [
            _f("student_name", "text", 1, "نام دانش‌آموز", required=True,
               validators={"min_length": 3, "max_length": 120}),
            _f("age", "number", 2, "سن", required=True,
               validators={"min_value": 3, "max_value": 100}),
            _f("contact_number", "text", 3, "شماره تماس", required=True,
               validators={"regex": "^09[0-9]{9}$"},
               placeholder="09123456789"),
            _f("home_area", "text", 4, "محله محل سکونت", required=True,
               max_length=200, placeholder="محله قصردشت"),
            _f("father_job", "text", 5, "شغل پدر", required=True, max_length=120),
            _f("mother_job", "text", 6, "شغل مادر", required=True, max_length=120),
            _f("allergies", "textarea", 7, "حساسیت‌ها", max_length=1000),
            _f("assessment_slot", "datetime", 8, "اسلات ارزیابی (تعیین کارمند)"),
            _f("assessment_day_time", "datetime", 9, "زمان جلسه ارزیابی", required=True),
            _f("assessor", "relation", 10, "ارزیاب", required=True,
               relation={"registry_key": "persons.person", "lookup": "id",
                         "filter": {"is_active": True}}),
            _f("recommended_course", "relation", 11, "دوره پیشنهادی",
               relation={"registry_key": "academic.course", "lookup": "id",
                         "required": False}),
        ],
    },
}


class Command(BaseCommand):
    help = "Seed dynamic form schemas (idempotent, fail-closed preflight)"

    def add_arguments(self, parser) -> None:
        parser.add_argument("--dry-run", action="store_true",
                            help="Run the full preflight without writing anything.")
        parser.add_argument("--force", action="store_true",
                            help="Overwrite an existing (slug, version) schema.")
        parser.add_argument("--schema-version", type=int, default=None, dest="schema_version",
                            help="Seed at this schema version instead of the catalog default. "
                                 "(--version itself is reserved by Django's BaseCommand.)")
        parser.add_argument("--deactivate-old", action="store_true",
                            help="After seeding, deactivate other versions of each slug.")
        parser.add_argument("slugs", nargs="*",
                            help=f"Subset of schemas to seed. Default: all ({', '.join(SCHEMA_CATALOG)}).")

    # ── preflight ─────────────────────────────────────────────────────────

    def _preflight(self, slugs: list[str], version_override: int | None):
        """
        Validate every selected schema and resolve relations.

        Returns (prepared, problems):
          prepared — list of dicts ready to write (fallbacks applied).
          problems — list of actionable strings for unavailable REQUIRED
                     relations (empty means the run may write).
        """
        prepared: list[dict[str, Any]] = []
        problems: list[str] = []

        for slug in slugs:
            entry = SCHEMA_CATALOG[slug]
            fields = [dict(f) for f in entry["fields"]]  # deep-ish copy
            try:
                ordered = validate_form_fields(fields)
            except SchemaDefinitionError as exc:
                problems.append(f"[{slug}] schema is structurally invalid: {exc}")
                continue

            fallback_notes: list[dict[str, str]] = []
            usable = True
            for definition in ordered:
                relation = definition.get("relation")
                if not relation:
                    continue
                registry_key = relation.get("registry_key")
                try:
                    spec = relations.resolve(registry_key)
                except relations.UnknownRelationKey:
                    problems.append(
                        f"[{slug}] field '{definition['key']}' references relation "
                        f"'{registry_key}' which is not in the server-side allowlist."
                    )
                    usable = False
                    continue

                if spec.is_available():
                    continue
                if not spec.optional:
                    problems.append(
                        f"[{slug}] required relation '{spec.key}' maps to model "
                        f"'{spec.model_label}' which is not installed."
                    )
                    usable = False
                    continue
                if not spec.fallback or not spec.fallback.get("type"):
                    problems.append(
                        f"[{slug}] optional relation '{spec.key}' has no declared "
                        f"fallback and model '{spec.model_label}' is not installed."
                    )
                    usable = False
                    continue

                # Explicit, declared fallback — record it in metadata.
                definition["type"] = spec.fallback["type"]
                definition.pop("relation", None)
                fallback_notes.append({
                    "field_key": definition["key"],
                    "registry_key": spec.key,
                    "expected_model": spec.model_label,
                    "fallback_type": spec.fallback["type"],
                    "reason": spec.fallback.get("reason", ""),
                })

            if not usable:
                continue

            prepared.append({
                "slug": slug,
                "version": version_override or entry["version"],
                "title": entry["title"],
                "description": entry["description"],
                "fields": ordered,
                "allowed_roles": list(entry.get("allowed_roles", [])),
                "workflow_code": entry.get("workflow_code"),
                "metadata": {"relation_fallbacks": fallback_notes} if fallback_notes else {},
            })

        return prepared, problems

    # ── run ───────────────────────────────────────────────────────────────

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        slugs = options["slugs"] or list(SCHEMA_CATALOG)
        unknown = [s for s in slugs if s not in SCHEMA_CATALOG]
        if unknown:
            raise CommandError(
                f"unknown schema slug(s): {', '.join(unknown)}. "
                f"Available: {', '.join(SCHEMA_CATALOG)}"
            )

        prepared, problems = self._preflight(slugs, options["schema_version"])

        if problems:
            # Fail closed: nothing has been written yet (preflight is read-only).
            raise CommandError(
                "seed aborted — unavailable required relations / invalid schemas "
                "(no database changes were made):\n  - "
                + "\n  - ".join(problems)
            )

        # Role codes must exist (run seed_roles first) — actionable, not invented.
        wanted_roles = sorted({code for item in prepared for code in item["allowed_roles"]})
        existing = set(Role.objects.filter(code__in=wanted_roles).values_list("code", flat=True))
        missing_roles = sorted(set(wanted_roles) - existing)
        if missing_roles:
            raise CommandError(
                f"missing role(s): {', '.join(missing_roles)} — run "
                "`python manage.py seed_roles` first. No database changes were made."
            )

        # Workflow definitions referenced by the catalog must exist or be
        # created by seed_form_workflows — a dangling FK would break submit.
        from apps.workflow.models import WorkflowDefinition

        wanted_workflows = sorted({item["workflow_code"] for item in prepared if item["workflow_code"]})
        existing_workflows = set(
            WorkflowDefinition.objects.filter(code__in=wanted_workflows, is_active=True)
            .values_list("code", flat=True)
        )
        missing_workflows = sorted(set(wanted_workflows) - existing_workflows)
        if missing_workflows:
            raise CommandError(
                f"missing workflow definition(s): {', '.join(missing_workflows)} — run "
                "`python manage.py seed_form_workflows` first. "
                "No database changes were made."
            )

        if options["dry_run"]:
            for item in prepared:
                self.stdout.write(
                    f"[dry-run] would seed {item['slug']} v{item['version']} "
                    f"({len(item['fields'])} fields"
                    + (f", {len(item['metadata'].get('relation_fallbacks', []))} fallback(s)"
                       if item.get("metadata") else "")
                    + ")"
                )
            self.stdout.write(self.style.SUCCESS("dry-run complete — no writes"))
            return

        for item in prepared:
            if options["deactivate_old"]:
                # BEFORE activating the new version: the one-active-per-slug
                # constraint would reject activation while an old version is
                # still active. Deactivating old versions first is the only
                # order that satisfies both constraints.
                FormSchema.objects.filter(slug=item["slug"]).exclude(
                    version=item["version"]
                ).update(is_active=False, updated_at=timezone.now())

            workflow = None
            if item["workflow_code"]:
                workflow = WorkflowDefinition.objects.get(
                    code=item["workflow_code"], is_active=True
                )

            schema, created = FormSchema.objects.get_or_create(
                slug=item["slug"],
                version=item["version"],
                defaults={
                    "title": item["title"],
                    "description": item["description"],
                    "fields": item["fields"],
                    "is_active": True,
                    "metadata": item["metadata"],
                    "workflow_definition": workflow,
                },
            )
            if not created:
                if options["force"]:
                    schema.title = item["title"]
                    schema.description = item["description"]
                    schema.fields = item["fields"]
                    schema.metadata = item["metadata"]
                    schema.is_active = True
                    schema.full_clean()
                    schema.save()
                    state = "updated"
                else:
                    state = "exists (skipped — use --force to overwrite)"
            else:
                state = "created"

            roles = Role.objects.filter(code__in=item["allowed_roles"])
            schema.allowed_roles.set(roles)

            self.stdout.write(f"[{state}] {item['slug']} v{item['version']}")

        self.stdout.write(self.style.SUCCESS("form schemas ready"))
