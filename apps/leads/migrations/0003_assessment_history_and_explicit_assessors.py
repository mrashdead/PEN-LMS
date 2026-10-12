from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def preserve_current_assessments(apps, schema_editor):
    Lead = apps.get_model("leads", "Lead")
    Assessment = apps.get_model("leads", "LeadAssessment")
    Recommendation = apps.get_model("leads", "LeadRecommendation")
    histories = {}
    for lead in Lead.objects.exclude(assessment_result="").iterator():
        assessment = Assessment.objects.create(lead_id=lead.pk, assessor_id=lead.assessor_id,
                                               result=lead.assessment_result, created_at=lead.updated_at)
        histories[lead.pk] = assessment
    for lead in Lead.objects.filter(status__in=("recommended", "enrolled"), course__isnull=False).iterator():
        assessment = histories.get(lead.pk)
        if assessment:
            Recommendation.objects.create(
                lead_id=lead.pk, assessment_id=assessment.pk, assessor_id=lead.assessor_id,
                course_id=lead.course_id, lesson_id=lead.lesson_id, note=lead.recommendation,
                created_at=lead.updated_at,
            )


class Migration(migrations.Migration):
    dependencies = [
        ("leads", "0002_send_scheduled_leads_to_assessor"),
        ("persons", "0012_person_can_assess_leads"),
        ("education", "0013_enrollment_payment_ledger"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(name="LeadAssessment", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("result", models.TextField()), ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
            ("assessor", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="lead_assessment_history", to="persons.person")),
            ("lead", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assessments", to="leads.lead")),
            ("recorded_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="lead_assessments_recorded", to=settings.AUTH_USER_MODEL)),
        ], options={"ordering": ("created_at", "pk")}),
        migrations.CreateModel(name="LeadRecommendation", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("note", models.TextField(blank=True, default="")), ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
            ("assessment", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="recommendations", to="leads.leadassessment")),
            ("assessor", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="lead_recommendations", to="persons.person")),
            ("course", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="lead_recommendation_history", to="education.course")),
            ("lead", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="recommendations", to="leads.lead")),
            ("lesson", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="lead_recommendation_history", to="education.lesson")),
            ("recorded_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="lead_recommendations_recorded", to=settings.AUTH_USER_MODEL)),
        ], options={"ordering": ("created_at", "pk")}),
        migrations.RunPython(preserve_current_assessments, migrations.RunPython.noop),
        migrations.RemoveConstraint(model_name="lead", name="leads_score_lte_100"),
        migrations.RemoveField(model_name="lead", name="assessment_score"),
    ]
