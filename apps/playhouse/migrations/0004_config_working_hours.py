# Adds working-hours fields to PlayhouseConfig (singleton settings page).
# Hand-authored (sandbox has no pip/network) — depends on 0003.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('playhouse', '0003_playhousesession_pause_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='playhouseconfig',
            name='open_time',
            field=models.TimeField(blank=True, help_text='ساعت باز شدن خانه بازی (اختیاری)', null=True),
        ),
        migrations.AddField(
            model_name='playhouseconfig',
            name='close_time',
            field=models.TimeField(blank=True, help_text='ساعت بسته شدن خانه بازی (اختیاری)', null=True),
        ),
        migrations.AddField(
            model_name='playhouseconfig',
            name='is_open_now',
            field=models.BooleanField(db_index=True, default=True, help_text='اگر خاموش باشد، ثبت ورود جدید مسدود می‌شود'),
        ),
    ]
