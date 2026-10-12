from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("education", "0015_progress_report_times")]

    operations = [
        migrations.AddField(
            model_name="studentprogressreport",
            name="class_report_id",
            field=models.UUIDField(blank=True, db_index=True, editable=False, null=True),
        ),
    ]
