"""
Seed the dynamic-form schema catalog.

    python manage.py seed_form_schemas [--dry-run] [--force] [--schema-version N]
                                       [--deactivate-old] [slug ...]

Contract (fail-closed, all-or-nothing):

  1. Every selected schema definition is structurally pre-validated
     (``validate_form_fields``) BEFORE any database write.
  2. Every relation key used by the selection is resolved through the fixed
     server-side registry. Required targets that are not installed abort the
     whole run with ONE actionable error listing every affected schema and
     relation — zero database changes. (Since the education app landed, the
     full catalog seeds: Lesson/Course/CourseOffering/Department/Location
     all resolve; ``academic.venue`` keeps its text-fallback declaration as
     a safety net.)
  3. Optional targets that are not installed may only be replaced by their
     explicitly declared fallback (currently ``academic.venue`` → text), and
     the substitution is recorded in ``FormSchema.metadata``.
  4. Successful writes happen in a single atomic transaction.
  5. Idempotent: an existing (slug, version) row is skipped unless --force.
     --deactivate-old marks every other version of the slug inactive.

Catalog v2 (2026-09): rebuilt from the owner's field list. Notable changes
from v1: lesson.syllabus is a rich_text EDITOR field (no mandatory file
upload — the owner asked to type it in-place); course-offering gained
``offering_lessons`` («مشخصات برگزاری: چه درس‌هایی») and course/lead
wording aligned with the owner's spec. attendance/grade keys stay untouched
— they are projection contracts (services._project_into_education, the
education unique (group,date,number) constraint and the test suite).

RESEEDING from v1-(old) to v2 fields on a DB that already has v1 rows:
the (slug, version) row is skipped without --force. To pick up the new
field definitions run:

    python manage.py seed_form_schemas --force --deactivate-old
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
    # ═════════════════════════════════════════════════════════════════════
    # Catalog v2 — rebuilt from the OWNER'S field list verbatim (2026-09).
    # Slugs/workflow codes/attendance & grade field keys are CONTRACTS used
    # by the projection layer (apps/forms/services._project_into_education),
    # the education tables (unique (group,date,number)) and the test suite —
    # they must not be renamed. syllabus is now a rich_text EDITOR field:
    # the owner asked for typing it in-place instead of a mandatory upload.
    # ═════════════════════════════════════════════════════════════════════

    # ── فرم درس (lesson) ─────────────────────────────────────────────────
    "lesson": {
        "title": "تعریف درس",
        "description": "فرم تعریف درس، سرفصل و مشخصات آموزشی آن.",
        "version": 1,
        "allowed_roles": ["manager", "supervisor", "workflow_admin"],
        "workflow_code": "form-approval",
        "fields": [
            _f("lesson_title", "text", 1, "عنوان درس", required=True,
               validators={"min_length": 3, "max_length": 200}),
            # سرفصل: ویرایش مستقیم در ادیتور (rich_text) — آپلود فایل اجباری نیست.
            _f("syllabus", "rich_text", 2, "سرفصل", required=True,
               max_length=50000),
            _f("duration_hours", "number", 3, "مدت زمان (ساعت)", required=True,
               validators={"min_value": 1, "max_value": 1000}),
            _f("description", "textarea", 4, "توضیحات درس", max_length=5000),
            _f("target_audience", "multi_select", 5, "مخاطبان درس", required=True, options=[
                {"value": "student", "label": "دانش‌آموز"},
                {"value": "employee", "label": "کارمند"},
                {"value": "teacher", "label": "معلم"},
                {"value": "parent", "label": "والدین"},
            ]),
            _f("prerequisites", "multi_relation", 6, "پیش‌نیاز",
               relation={"registry_key": "academic.lesson", "lookup": "id",
                         "required": False}),
            _f("assessment_method", "select", 7, "نحوه آزمون", required=True, options=[
                {"value": "written", "label": "کتبی"},
                {"value": "oral", "label": "شفاهی"},
                {"value": "practical", "label": "عملی"},
                {"value": "project", "label": "پروژه"},
                {"value": "none", "label": "بدون آزمون"},
            ]),
            _f("required_equipment", "textarea", 8, "تجهیزات مورد نیاز (سیستم و نرم‌افزار و غیره)",
               max_length=2000),
            _f("venue_type", "select", 9, "فضای آموزش", required=True, options=[
                {"value": "classroom", "label": "کلاس"},
                {"value": "lab", "label": "آزمایشگاه"},
                {"value": "workshop", "label": "کارگاه"},
                {"value": "online", "label": "آنلاین"},
                {"value": "hybrid", "label": "ترکیبی"},
            ]),
            _f("learning_resources", "textarea", 10, "منابع آموزش", max_length=5000),
            _f("topics", "textarea", 11, "سرفصل‌ها", required=True, max_length=5000),
            _f("tuition_amount", "number", 12, "شهریه",
               validators={"min_value": 0, "max_value": 1000000000}),
        ],
    },
    # ── فرم دوره (course) ────────────────────────────────────────────────
    "course": {
        "title": "تعریف دوره",
        "description": "فرم تعریف دوره آموزشی و دروس آن.",
        "version": 1,
        "allowed_roles": ["manager", "supervisor", "workflow_admin"],
        "workflow_code": "form-approval",
        "fields": [
            _f("course_title", "text", 1, "عنوان دوره", required=True,
               validators={"min_length": 3, "max_length": 200}),
            _f("department", "relation", 2, "دپارتمان", required=True,
               relation={"registry_key": "academic.department", "lookup": "id"}),
            _f("description", "textarea", 3, "توضیحات دوره", max_length=5000),
            _f("lessons", "multi_relation", 4, "دروس", required=True,
               relation={"registry_key": "academic.lesson", "lookup": "id"}),
            _f("objectives", "textarea", 5, "اهداف", required=True, max_length=5000),
        ],
    },
    # ── فرم برگزاری دوره (course-offering) ───────────────────────────────
    "course-offering": {
        "title": "برگزاری دوره",
        "description": "فرم برگزاری یک دوره: ظرفیت، تاریخ، محل، استاد و زمان‌بندی.",
        "version": 1,
        "allowed_roles": ["manager", "supervisor", "workflow_admin", "employee"],
        "workflow_code": "form-approval",
        "fields": [
            _f("course", "relation", 1, "انتخاب دوره", required=True,
               relation={"registry_key": "academic.course", "lookup": "id"}),
            _f("capacity", "number", 2, "ظرفیت", required=True,
               validators={"min_value": 1, "max_value": 500}),
            _f("start_date", "date", 3, "تاریخ شروع", required=True),
            # مشخصات برگزاری: چه درس‌هایی در این برگزاری قرار دارد
            _f("offering_lessons", "multi_relation", 4, "درس‌های این برگزاری",
               required=True,
               relation={"registry_key": "academic.lesson", "lookup": "id"}),
            _f("venue", "relation", 5, "محل برگزاری",
               relation={"registry_key": "academic.venue", "lookup": "id",
                         "required": False}),
            _f("instructor", "relation", 6, "استاد", required=True,
               relation={"registry_key": "persons.person", "lookup": "id",
                         "filter": {"person_type": "teacher", "is_active": True}}),
            # زمان برگزاری: روز و ساعت (متن آزاد مثلا «شنبه و دوشنبه 16-14»)
            _f("schedule", "text", 7, "زمان برگزاری (روز و ساعت)", required=True,
               validators={"max_length": 300},
               placeholder="شنبه و دوشنبه ۱۴ تا ۱۶"),
        ],
    },
    # ── فرم تشکیل کلاس (class-session-setup) ─────────────────────────────
    "class-session-setup": {
        "title": "تشکیل کلاس",
        "description": "نهایی‌سازی کلاس: برگزاری، درس، استاد، محل و زمان قطعی.",
        "version": 1,
        "allowed_roles": ["manager", "supervisor", "workflow_admin"],
        "workflow_code": "form-approval",
        "fields": [
            _f("course_offering", "relation", 1, "برگزاری دوره", required=True,
               relation={"registry_key": "academic.course_offering", "lookup": "id"}),
            _f("lesson", "relation", 2, "درس", required=True,
               relation={"registry_key": "academic.lesson", "lookup": "id"}),
            _f("instructor", "relation", 3, "استاد", required=True,
               relation={"registry_key": "persons.person", "lookup": "id",
                         "filter": {"person_type": "teacher", "is_active": True}}),
            _f("venue", "relation", 4, "محل برگزاری کلاس",
               relation={"registry_key": "academic.venue", "lookup": "id",
                         "required": False}),
            _f("confirmed_start_date", "date", 5, "تاریخ شروع قطعی", required=True),
            # روز و ساعت قطعی کلاس
            _f("confirmed_schedule", "text", 6, "روز و ساعت قطعی", required=True,
               validators={"max_length": 300},
               placeholder="دوشنبه‌ها ۱۶ تا ۱۷:۳۰"),
        ],
    },
    # ── فرم حضور و غیاب (attendance) — keys are projection CONTRACTS ─────
    "attendance": {
        "title": "ثبت حضور و غیاب",
        "description": "ثبت گروهی حضور/غیاب دانش‌آموزان یک کلاس در یک جلسه.",
        "version": 1,
        "allowed_roles": ["teacher", "manager"],
        "workflow_code": "form-review",
        "fields": [
            _f("class_group", "relation", 1, "کلاس", required=True,
               relation={"registry_key": "academic.class_group", "lookup": "id",
                         "filter": {"is_active": True}}),
            # A session is identified by (class, date, number) — the date is
            # required for the daily/weekly/monthly session reports and for
            # the projection's unique constraint (B4). session_number alone
            # would conflate the same number across different days.
            _f("session_date", "date", 2, "تاریخ جلسه", required=True),
            _f("session_number", "number", 3, "جلسه (شماره)", required=True,
               validators={"min_value": 1, "max_value": 500}),
            _f("attendance_list", "attendance_table", 4, "لیست اسامی کلاس",
               required=True, statuses=["present", "absent", "late", "excused"],
               max_rows=200),
            _f("session_start", "time", 5, "ساعت شروع جلسه", required=True),
            _f("session_end", "time", 6, "ساعت پایان جلسه", required=True,
               after="session_start"),
        ],
    },
    # ── فرم نمره و کارنامه (grade-report) — توصیفی و انتقادی، بدون عدد ──
    # Per-student verdict + mandatory reason live INSIDE grade_list rows
    # (result = قبول/مردود, teacher_note = «چرایی» that the teacher must
    # write). A form-level final grade would be wrong here: this form covers
    # a whole class, so the verdict is necessarily per student.
    "grade-report": {
        "title": "نمره و کارنامه (توصیفی)",
        "description": "کارنامه توصیفی و انتقادی: قبول/مردود هر دانش‌آموز همراه با "
                       "چرایی که استاد باید بنویسد.",
        "version": 1,
        "allowed_roles": ["teacher", "manager"],
        "workflow_code": "form-review",
        "fields": [
            _f("class_group", "relation", 1, "کلاس", required=True,
               relation={"registry_key": "academic.class_group", "lookup": "id",
                         "filter": {"is_active": True}}),
            _f("instructor", "relation", 2, "استاد", required=True,
               relation={"registry_key": "persons.person", "lookup": "id",
                         "filter": {"person_type": "teacher", "is_active": True}}),
            _f("grade_list", "grade_table", 3, "لیست نمره و نتیجه نهایی", required=True,
               results=["passed", "failed"], max_rows=200),
        ],
    },
    # ── فرم لید / تعیین سطح (lead-assessment) ────────────────────────────
    "lead-assessment": {
        "title": "ثبت‌نام و تعیین سطح",
        "description": "ثبت مشخصات دانش‌آموز، زمان ارزیابی و دوره و درس پیشنهادی.",
        "version": 2,
        "allowed_roles": ["employee", "supervisor", "manager", "workflow_admin"],
        "workflow_code": "lead-assessment",
        "fields": [
            _f("student_name", "text", 1, "نام دانش‌آموز", required=True,
               validators={"min_length": 3, "max_length": 120}),
            _f("age", "number", 2, "سن", required=True,
               validators={"min_value": 3, "max_value": 100}),
            _f("contact_number", "text", 3, "شماره تماس", required=True,
               validators={"regex": "^09[0-9]{9}$"},
               placeholder="09123456789"),
            _f("home_area", "text", 4, "محدوده آدرس منزل (محله)", required=True,
               max_length=200, placeholder="محله قصردشت"),
            _f("father_job", "text", 5, "شغل پدر", required=True, max_length=120),
            _f("mother_job", "text", 6, "شغل مادر", required=True, max_length=120),
            _f("allergies", "textarea", 7, "حساسیت یا آلرژی", max_length=1000),
            # نوبت تعیین سطح: روز و ساعت جلسه
            _f("assessment_day_time", "datetime", 8,
               "روز و ساعت جلسه تعیین سطح", required=True),
            _f("assessor", "relation", 9, "مسئول یا گیرنده تعیین سطح", required=True,
               relation={"registry_key": "persons.person", "lookup": "id",
                         "filter": {"is_active": True}}),
            # انتخاب دوره/درس توسط گیرنده تعیین سطح → ثبت‌نام شخص باز می‌شود.
            _f("recommended_course", "relation", 10, "دوره مورد نظر",
               relation={"registry_key": "academic.course", "lookup": "id",
                         "required": False}),
            _f("recommended_lesson", "relation", 11, "درس مورد نظر",
               relation={"registry_key": "academic.lesson", "lookup": "id",
                         "required": False, "course_field": "recommended_course"}),
        ],
    },
    # ── فرم ثبت‌نام دانش‌آموز — Request → workflow → domain action ───────
    "student-registration": {
        "title": "ثبت‌نام دانش‌آموز در برگزاری",
        "description": "درخواست ثبت‌نام، بررسی ظرفیت و مالی، تأیید نهایی و ایجاد عضویت کلاس.",
        "version": 1,
        "allowed_roles": ["student", "employee", "supervisor", "manager", "workflow_admin"],
        "workflow_code": "student-registration",
        "metadata": {"domain_action": "student_registration", "subject_field": "student"},
        "fields": [
            _f("offering", "relation", 1, "برگزاری دوره", required=True,
               relation={"registry_key": "academic.course_offering", "lookup": "id"}),
            _f("student", "relation", 2, "دانش‌آموز", required=True,
               relation={"registry_key": "persons.person", "lookup": "id",
                         "filter": {"person_type": "student", "is_active": True}}),
            _f("class_group", "relation", 3, "کلاس قطعی (اختیاری تا زمان تشکیل کلاس)",
               relation={"registry_key": "academic.class_group", "lookup": "id",
                         "required": False, "filter": {"is_active": True}}),
            _f("discount_type", "select", 4, "نوع تخفیف", options=[
                {"value": "none", "label": "بدون تخفیف"},
                {"value": "percent", "label": "درصدی"},
                {"value": "amount", "label": "مبلغ ثابت"},
            ]),
            _f("discount_value", "number", 5, "مقدار تخفیف", validators={"min_value": 0}),
            _f("payment_method", "select", 6, "روش پرداخت", options=[
                {"value": "cash", "label": "نقدی"},
                {"value": "pos", "label": "کارت‌خوان"},
                {"value": "cheque", "label": "چک"},
            ]),
            _f("payment_reference", "text", 7, "کد پیگیری پرداخت", max_length=128),
        ],
    },
}

# Explicit catalogue metadata; request UI never infers a category from slugs.
SCHEMA_CATEGORIES = {
    "lesson": "courses",
    "course": "courses",
    "course-offering": "classes",
    "class-session-setup": "classes",
    "attendance": "classes",
    "grade-report": "classes",
    "lead-assessment": "persons",
    "student-registration": "persons",
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
                "metadata": {
                    **dict(entry.get("metadata") or {}),
                    **({"relation_fallbacks": fallback_notes} if fallback_notes else {}),
                },
                "request_type_code": entry.get("request_type_code", slug),
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
        # supervisor is an additive role; keep old installations seedable and
        # attach it automatically once seed_roles creates it.
        missing_roles = sorted(
            (set(wanted_roles) - existing) - {"supervisor", "student", "guardian"}
        )
        if missing_roles:
            raise CommandError(
                f"missing role(s): {', '.join(missing_roles)} — run "
                "`python manage.py seed_roles` first. No database changes were made."
            )

        # Workflow definitions referenced by the catalog must exist or be
        # created by seed_form_workflows — a dangling FK would break submit.
        from apps.workflow.models import WorkflowDefinition
        from apps.forms.models import RequestType

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

            request_type, _ = RequestType.objects.get_or_create(
                code=item["request_type_code"],
                defaults={
                    "title": item["title"],
                    "description": item["description"],
                    "kind": RequestType.Kind.REQUEST,
                    "workflow_definition": workflow,
                    "metadata": item["metadata"],
                },
            )
            if options["force"]:
                request_type.title = item["title"]
                request_type.description = item["description"]
                request_type.workflow_definition = workflow
                request_type.metadata = item["metadata"]
                request_type.is_active = True
                request_type.save(update_fields=[
                    "title", "description", "workflow_definition", "metadata", "is_active", "updated_at"
                ])
            request_type.allowed_roles.set(Role.objects.filter(code__in=item["allowed_roles"]))

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
                    "request_type": request_type,
                    "category": SCHEMA_CATEGORIES.get(item["slug"], "general"),
                    "workflow_config": {
                        "execution_mode": "workflow" if workflow else "direct",
                        "allow_on_behalf": item["slug"] == "lesson",
                        "eligible_initiator_roles": item["allowed_roles"],
                        "routing_rules": [],
                    },
                },
            )
            if not created:
                if options["force"]:
                    schema.title = item["title"]
                    schema.description = item["description"]
                    schema.fields = item["fields"]
                    schema.metadata = item["metadata"]
                    schema.workflow_definition = workflow
                    schema.request_type = request_type
                    schema.category = SCHEMA_CATEGORIES.get(item["slug"], "general")
                    schema.workflow_config = {
                        "execution_mode": "workflow" if workflow else "direct",
                        "allow_on_behalf": item["slug"] == "lesson",
                        "eligible_initiator_roles": item["allowed_roles"],
                        "routing_rules": [],
                    }
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
