# Hand-written: session-generation engine inputs + holiday calendar.
#
#   CourseOffering.total_sessions / auto_skip_holidays
#       the class-formation form's "تعداد کل جلسات" and "پرش تعطیلات" knobs.
#   AcademicHoliday
#       the single source of truth the recurrence engine jumps over.

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("education", "0003_remove_lesson_assessment_method_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="courseoffering",
            name="total_sessions",
            field=models.PositiveSmallIntegerField(
                default=0,
                help_text="تعداد کل جلسات دوره (فرم تشکیل کلاس) — ۰ = توزیع بر اساس ساعات تدریس.",
            ),
        ),
        migrations.AddField(
            model_name="courseoffering",
            name="auto_skip_holidays",
            field=models.BooleanField(
                default=True,
                help_text="در تولید خودکار، روزهای تعطیل رسمی/جمعه‌ها حذف می‌شوند.",
            ),
        ),
        migrations.CreateModel(
            name="AcademicHoliday",
            fields=[
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("name", models.CharField(max_length=200)),
                ("scope", models.CharField(
                    choices=[("official", "تعطیل رسمی"), ("weekly", "تعطیل هفتگی"),
                             ("institute", "تعطیل مؤسسه")],
                    db_index=True, default="official", max_length=16,
                )),
                ("date_from", models.DateField(db_index=True)),
                ("date_to", models.DateField(db_index=True, help_text="برای تک‌روز = date_from")),
                ("weekday", models.PositiveSmallIntegerField(
                    blank=True, null=True,
                    choices=[(5, "شنبه"), (6, "یکشنبه"), (0, "دوشنبه"), (1, "سه‌شنبه"),
                             (2, "چهارشنبه"), (3, "پنجشنبه"), (4, "جمعه")],
                    help_text="فقط برای scope=weekly: روز هفته‌ی تکرارشونده (Python weekday).",
                )),
                ("all_day", models.BooleanField(
                    default=True,
                    help_text="خیر = فقط بخشی از روز (ساعت‌ها را در note قید کنید).",
                )),
                ("note", models.CharField(blank=True, default="", max_length=256)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("legacy_id", models.CharField(blank=True, db_index=True, default="", max_length=64)),
                ("location", models.ForeignKey(
                    blank=True, help_text="خالی = کل مؤسسه.",
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="holidays",
                    to="education.location",
                )),
            ],
            options={
                "verbose_name": "Holiday (تعطیلات)",
                "verbose_name_plural": "Holidays (تعطیلات)",
                "db_table": "education_academic_holiday",
                "ordering": ("date_from", "scope"),
            },
        ),
        migrations.AddConstraint(
            model_name="academicholiday",
            constraint=models.CheckConstraint(
                condition=models.Q(date_to__gte=models.F("date_from")),
                name="chk_edu_holiday_date_range",
            ),
        ),
        migrations.AddIndex(
            model_name="academicholiday",
            index=models.Index(fields=["date_from", "is_active"], name="edu_holiday_date_active_idx"),
        ),
        migrations.AddIndex(
            model_name="academicholiday",
            index=models.Index(fields=["scope", "weekday"], name="edu_holiday_scope_weekday_idx"),
        ),
    ]
