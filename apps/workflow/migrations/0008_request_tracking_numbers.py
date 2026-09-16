# Hand-written: human Tracking ID for workflow requests.
#   Instance.tracking_number (REQ-<year>-000123, live-unique when non-empty)
#   RequestSequence — ONE counter row per year (global, not per workflow code)
#
# Why global-per-year and not per-(code, year): the number carries only a year,
# so a per-code counter would hand "REQ-2026-000001" to the first instance of
# every process at once and the live-unique index could never be built. The
# first migration attempt failed on exactly that UniqueViolation against real
# data; this version is the corrected one.
#
# The RunPython backfill numbers EXISTING instances oldest-first across the
# whole year (all workflow codes interleaved) and seeds each year row to the
# last value used, so a post-migrate create never collides with legacy data.

from django.db import migrations, models


def backfill_tracking_numbers(apps, schema_editor):
    Instance = apps.get_model("workflow", "Instance")
    RequestSequence = apps.get_model("workflow", "RequestSequence")
    db = schema_editor.connection.alias

    # Oldest-first, year by year: the sequence is per year, so each year
    # restarts at 1 and the ordering inside a year is creation order.
    counters: dict[int, int] = {}
    instances = (
        Instance.objects.using(db)
        .filter(tracking_number="")
        .order_by("created_at")
    )
    for inst in instances:
        year = inst.created_at.year
        counters[year] = counters.get(year, 0) + 1
        inst.tracking_number = f"REQ-{year}-{counters[year]:06d}"
        inst.save(update_fields=["tracking_number"])

    for year, last in counters.items():
        RequestSequence.objects.using(db).get_or_create(
            year=year, defaults={"last_value": last}
        )


def unbackfill_tracking_numbers(apps, schema_editor):
    Instance = apps.get_model("workflow", "Instance")
    Instance.objects.using(schema_editor.connection.alias).update(tracking_number="")


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0007_notificationoutbox_is_read_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="instance",
            name="tracking_number",
            field=models.CharField(
                blank=True, db_index=True, default="", max_length=32,
                help_text="شناسه پیگیری انسانی، مثال REQ-2026-000123 — هنگام ایجاد پر می‌شود.",
            ),
        ),
        migrations.CreateModel(
            name="RequestSequence",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("year", models.PositiveIntegerField(unique=True)),
                ("last_value", models.PositiveIntegerField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Request Sequence (شمارنده پیگیری)",
                "verbose_name_plural": "Request Sequences (شمارنده‌های پیگیری)",
                "db_table": "workflow_request_sequence",
                "ordering": ("year",),
            },
        ),
        migrations.RunPython(
            backfill_tracking_numbers, unbackfill_tracking_numbers,
            elidable=False,
        ),
        migrations.AddConstraint(
            model_name="instance",
            constraint=models.UniqueConstraint(
                condition=models.Q(is_deleted=False) & ~models.Q(tracking_number=""),
                fields=("tracking_number",),
                name="uniq_workflow_tracking_number_alive",
            ),
        ),
    ]
