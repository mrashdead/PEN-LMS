import uuid

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("playhouse", "0006_playhousemember_national_code"),
    ]

    operations = [
        migrations.CreateModel(
            name="PlayhouseCafePreset",
            fields=[
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("name", models.CharField(help_text="نام آیتم آماده کافه", max_length=200)),
                ("price", models.DecimalField(decimal_places=0, help_text="قیمت پیش‌فرض (تومان)", max_digits=12)),
            ],
            options={
                "verbose_name": "آیتم آماده کافه خانه بازی",
                "verbose_name_plural": "آیتم‌های آماده کافه خانه بازی",
                "db_table": "playhouse_cafe_preset",
                "ordering": ("name",),
            },
        ),
    ]
