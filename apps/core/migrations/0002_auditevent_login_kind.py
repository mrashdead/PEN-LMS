from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="auditevent",
            name="kind",
            field=models.CharField(
                choices=[
                    ("login", "ورود موفق"),
                    ("logout", "خروج موفق"),
                    ("access_denied", "رد دسترسی"),
                    ("download", "دانلود فایل"),
                    ("sensitive_read", "خواندن داده‌ی حساس"),
                    ("field_change", "تغییر فیلد حساس"),
                ],
                db_index=True,
                max_length=32,
            ),
        ),
    ]
