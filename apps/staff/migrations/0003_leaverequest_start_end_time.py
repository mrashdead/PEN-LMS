from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("staff", "0002_remove_leavetype_staff_lt_accrual_active_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="leaverequest",
            name="start_time",
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="leaverequest",
            name="end_time",
            field=models.TimeField(blank=True, null=True),
        ),
    ]
