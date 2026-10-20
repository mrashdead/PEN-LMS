from django.db import migrations, models
from django.utils import timezone


def auto_approve_manager_timesheets(apps, schema_editor):
    TimesheetEntry = apps.get_model("staff", "TimesheetEntry")
    ReviewHistory = apps.get_model("staff", "ReviewHistory")
    User = apps.get_model("accounts", "User")
    UserRole = apps.get_model("accounts", "UserRole")
    now = timezone.now()

    manager_ids = set(
        User.objects.filter(is_superuser=True).values_list("pk", flat=True)
    )
    manager_ids.update(
        UserRole.objects.filter(
            is_active=True,
            role__code__in=("manager", "workflow_admin"),
            role__is_active=True,
            role__is_deleted=False,
        )
        .filter(models.Q(valid_from__isnull=True) | models.Q(valid_from__lte=now))
        .filter(models.Q(valid_to__isnull=True) | models.Q(valid_to__gte=now))
        .values_list("user_id", flat=True)
    )

    entries = TimesheetEntry.objects.filter(
        user_id__in=manager_ids,
        status="pending",
        check_out__isnull=False,
        is_deleted=False,
    ).iterator()
    for entry in entries:
        previous = entry.status
        entry.status = "approved"
        entry.reviewed_by_id = entry.user_id
        entry.reviewed_at = entry.updated_at or now
        entry.save(update_fields=("status", "reviewed_by", "reviewed_at"))
        ReviewHistory.objects.create(
            record_type="timesheet",
            record_id=entry.pk,
            from_status=previous,
            to_status="approved",
            actor_id=entry.user_id,
            comment="تأیید خودکار ساعت‌های ثبت‌شده توسط مدیر.",
            metadata={"work_date": entry.work_date.isoformat(), "automatic": True},
        )


def preserve_approved_records(apps, schema_editor):
    # Approval history is append-only; reversing would misrepresent prior data.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_user_uniq_user_employee_code_alive"),
        ("staff", "0004_multi_shift_and_review_assigned_leave_type"),
    ]

    operations = [
        migrations.RunPython(auto_approve_manager_timesheets, preserve_approved_records),
    ]
