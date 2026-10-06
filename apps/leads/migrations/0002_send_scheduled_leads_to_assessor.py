from django.db import migrations, models


def send_scheduled_leads(apps, schema_editor):
    Lead = apps.get_model("leads", "Lead")
    Lead.objects.filter(status="scheduled").update(status="sent")


class Migration(migrations.Migration):
    dependencies = [("leads", "0001_initial")]

    operations = [
        migrations.RunPython(send_scheduled_leads, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="lead",
            name="status",
            field=models.CharField(
                choices=[
                    ("new", "لید جدید"),
                    ("sent", "ارسال‌شده برای استاد"),
                    ("assessed", "تعیین سطح‌شده"),
                    ("recommended", "دوره معرفی شد"),
                    ("enrolled", "ثبت‌نام‌شده"),
                    ("lost", "بایگانی‌شده"),
                ],
                db_index=True,
                default="new",
                max_length=20,
            ),
        ),
    ]
