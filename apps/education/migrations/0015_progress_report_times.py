from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("education", "0014_free_enrollment")]
    operations = [
        migrations.AddField(model_name="studentprogressreport", name="start_time", field=models.TimeField(blank=True, null=True)),
        migrations.AddField(model_name="studentprogressreport", name="end_time", field=models.TimeField(blank=True, null=True)),
    ]
