from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
import django.utils.timezone
import uuid


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("education", "0007_classsession_topic_enrollmentwaitlist_and_more"),
        ("persons", "0008_person_search_and_student_parents"),
    ]

    operations = [
        migrations.CreateModel(
            name="Lead",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("code", models.CharField(db_index=True, editable=False, max_length=24, unique=True)),
                ("student_name", models.CharField(max_length=200)),
                ("age", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("phone", models.CharField(max_length=20)),
                ("neighborhood", models.CharField(blank=True, default="", max_length=160)),
                ("father_job", models.CharField(blank=True, default="", max_length=160)),
                ("mother_job", models.CharField(blank=True, default="", max_length=160)),
                ("allergy_notes", models.TextField(blank=True, default="")),
                ("assessment_date", models.DateField(blank=True, db_index=True, null=True)),
                ("assessment_time", models.TimeField(blank=True, null=True)),
                ("status", models.CharField(choices=[("new", "لید جدید"), ("scheduled", "جلسه تعیین شد"), ("sent", "ارسال‌شده برای استاد"), ("assessed", "تعیین سطح‌شده"), ("recommended", "دوره معرفی شد"), ("enrolled", "ثبت‌نام‌شده"), ("lost", "بایگانی‌شده")], db_index=True, default="new", max_length=20)),
                ("assessment_score", models.PositiveSmallIntegerField(blank=True, null=True, validators=[django.core.validators.MaxValueValidator(100)])),
                ("assessment_result", models.TextField(blank=True, default="")),
                ("recommendation", models.TextField(blank=True, default="")),
                ("assessor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="lead_assessments", to="persons.person")),
                ("course", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="leads", to="education.course")),
                ("lesson", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="leads", to="education.lesson")),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_leads", to=settings.AUTH_USER_MODEL)),
                ("enrolled_person", models.ForeignKey(blank=True, limit_choices_to={"person_type": "student"}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="source_leads", to="persons.person")),
            ],
            options={"db_table": "leads_lead", "ordering": ("-created_at",)},
        ),
        migrations.AddConstraint(
            model_name="lead",
            constraint=models.CheckConstraint(condition=models.Q(("assessment_score__isnull", True), ("assessment_score__lte", 100), _connector="OR"), name="leads_score_lte_100"),
        ),
        migrations.AddIndex(model_name="lead", index=models.Index(fields=["status", "assessment_date"], name="leads_lead_status_062f6a_idx")),
        migrations.AddIndex(model_name="lead", index=models.Index(fields=["phone", "status"], name="leads_lead_phone_b71730_idx")),
    ]
