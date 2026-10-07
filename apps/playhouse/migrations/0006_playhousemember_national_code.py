from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("playhouse", "0005_alter_playhouseconfig_is_open_now"),
    ]

    operations = [
        migrations.AddField(
            model_name="playhousemember",
            name="national_code",
            field=models.CharField(
                blank=True,
                db_index=True,
                default="",
                help_text="کد ملی کودک برای ثبت مراجعه و اتصال به پرونده موجود",
                max_length=10,
            ),
        ),
    ]
