from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("playhouse", "0002_rename_ph_inv_ispay_created_idx_playhouse_i_is_paid_93e244_idx_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="playhousesession",
            name="status",
            field=models.CharField(
                choices=[
                    ("waiting", "در انتظار ورود"),
                    ("active", "داخل خانه بازی"),
                    ("paused", "متوقف شده"),
                    ("finished", "پایان یافته"),
                    ("cancelled", "لغو شده"),
                ],
                db_index=True,
                default="waiting",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="playhousesession",
            name="paused_at",
            field=models.DateTimeField(blank=True, help_text="زمان توقف موقت تایمر", null=True),
        ),
        migrations.AddField(
            model_name="playhousesession",
            name="paused_seconds",
            field=models.PositiveIntegerField(
                default=0,
                help_text="مجموع ثانیه‌های توقف که از زمان قابل محاسبه کم می‌شود",
            ),
        ),
    ]
