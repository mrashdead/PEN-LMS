import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


def backfill_request_catalog(apps, schema_editor):
    """Create deterministic request types and request projections for legacy data."""
    FormSchema = apps.get_model("forms", "FormSchema")
    FormSubmission = apps.get_model("forms", "FormSubmission")
    RequestType = apps.get_model("forms", "RequestType")
    Request = apps.get_model("forms", "Request")
    db_alias = schema_editor.connection.alias

    status_map = {
        "draft": "draft",
        "submitted": "submitted",
        "processing": "in_review",
        "approved": "approved",
        "rejected": "rejected",
        "archived": "archived",
    }

    schemas = FormSchema.objects.using(db_alias).all().iterator()
    for schema in schemas:
        code = f"form-{schema.slug}"[:120]
        request_type, _ = RequestType.objects.using(db_alias).get_or_create(
            code=code,
            defaults={
                "title": schema.title,
                "description": schema.description,
                "kind": "request",
                "is_active": True,
                "workflow_definition_id": schema.workflow_definition_id,
                "metadata": {"legacy_schema_bridge": True},
            },
        )
        if schema.request_type_id != request_type.pk:
            FormSchema.objects.using(db_alias).filter(pk=schema.pk).update(
                request_type_id=request_type.pk,
            )

    submissions = FormSubmission.objects.using(db_alias).select_related(
        "form_schema", "workflow_instance",
    ).iterator()
    for submission in submissions:
        request_type = RequestType.objects.using(db_alias).get(
            code=f"form-{submission.form_schema.slug}"[:120],
        )
        workflow = getattr(submission, "workflow_instance", None)
        request_status = status_map.get(submission.status, "submitted")
        if workflow is not None:
            request_status = {
                "running": "in_review",
                "completed": "approved",
                "rejected": "rejected",
                "cancelled": "cancelled",
            }.get(workflow.status, request_status)
        Request.objects.using(db_alias).get_or_create(
            form_submission_id=submission.pk,
            defaults={
                "request_type_id": request_type.pk,
                "requester_id": submission.submitted_by_id,
                "subject_person_id": submission.subject_person_id,
                "request_number": submission.submission_number,
                "status": request_status,
                "submitted_at": submission.submitted_at,
                "last_action_at": submission.last_action_at or submission.updated_at,
                "metadata": {
                    "schema_slug": submission.form_schema.slug,
                    "schema_version": submission.schema_version_snapshot,
                    "backfilled": True,
                },
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("forms", "0004_formsubmission_projection_attempts_and_more"),
        ("workflow", "0012_remove_entityworkflow_uniq_workflow_entity_link_and_more"),
        ("persons", "0009_alter_guardianprofile_options_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="RequestType",
            fields=[
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("code", models.SlugField(db_index=True, max_length=120, unique=True)),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True, default="")),
                ("kind", models.CharField(choices=[("informational", "اطلاعاتی"), ("request", "درخواستی"), ("operational", "عملیاتی")], db_index=True, default="request", max_length=20)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("allowed_roles", models.ManyToManyField(blank=True, related_name="request_types", to="accounts.role")),
                ("workflow_definition", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="request_types", to="workflow.workflowdefinition")),
            ],
            options={
                "verbose_name": "Request Type (نوع درخواست)",
                "verbose_name_plural": "Request Types (انواع درخواست)",
                "db_table": "forms_request_type",
                "ordering": ("code",),
            },
        ),
        migrations.AddField(
            model_name="formschema",
            name="request_type",
            field=models.ForeignKey(blank=True, help_text="نوع کسب‌وکاری درخواستی که این نسخهٔ فرم ایجاد می‌کند.", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="form_schemas", to="forms.requesttype"),
        ),
        migrations.CreateModel(
            name="Request",
            fields=[
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("request_number", models.CharField(blank=True, help_text="شمارهٔ قابل پیگیری؛ معمولاً از شمارهٔ submission یا workflow می‌آید.", max_length=200, null=True, unique=True)),
                ("status", models.CharField(choices=[("draft", "پیش‌نویس"), ("submitted", "ارسال‌شده"), ("in_review", "در حال بررسی"), ("awaiting_action", "منتظر اقدام"), ("changes_requested", "نیازمند اصلاح"), ("approved", "تأییدشده"), ("rejected", "ردشده"), ("cancelled", "لغوشده"), ("completed", "تکمیل‌شده"), ("blocked_assignment", "بدون مسئول"), ("archived", "بایگانی‌شده")], db_index=True, default="draft", max_length=24)),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("last_action_at", models.DateTimeField(blank=True, null=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("form_submission", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="business_request", to="forms.formsubmission")),
                ("request_type", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="requests", to="forms.requesttype")),
                ("requester", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="business_requests", to=settings.AUTH_USER_MODEL)),
                ("subject_person", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="business_requests", to="persons.person")),
            ],
            options={
                "verbose_name": "Request (درخواست)",
                "verbose_name_plural": "Requests (درخواست‌ها)",
                "db_table": "forms_request",
                "ordering": ("-created_at",),
            },
        ),
        migrations.AddIndex(
            model_name="requesttype",
            index=models.Index(fields=["code", "is_active"], name="forms_reque_code_f2b6d4_idx"),
        ),
        migrations.AddIndex(
            model_name="requesttype",
            index=models.Index(fields=["kind", "is_active"], name="forms_reque_kind_a31fed_idx"),
        ),
        migrations.AddIndex(
            model_name="request",
            index=models.Index(fields=["request_type", "status"], name="forms_reque_request_b4571c_idx"),
        ),
        migrations.AddIndex(
            model_name="request",
            index=models.Index(fields=["requester", "status"], name="forms_reque_request_b2cbee_idx"),
        ),
        migrations.AddIndex(
            model_name="request",
            index=models.Index(fields=["subject_person", "status"], name="forms_reque_subject_622f33_idx"),
        ),
        migrations.AddIndex(
            model_name="request",
            index=models.Index(fields=["status", "created_at"], name="forms_reque_status_c362c3_idx"),
        ),
        migrations.RunPython(backfill_request_catalog, migrations.RunPython.noop),
    ]
