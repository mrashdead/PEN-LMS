"""
Initial migration for apps.staff — hand-authored (project convention for new
apps, cf. apps/playhouse/migrations/0001_initial.py) so the schema is reviewed
before it touches the user's PostgreSQL.
"""
from django.conf import settings
import django.core.validators
from django.db import migrations, models

import apps.core.fields
import apps.core.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("accounts", "0003_user_uniq_user_employee_code_alive"),
        ("contenttypes", "0002_remove_content_type_name"),
        ("persons", "0009_alter_guardianprofile_options_and_more"),
        ("workflow", "0013_state_assignment_policy"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ReviewHistory",
            fields=[
                ("created_at", models.DateTimeField(db_index=True, default=apps.core.models.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("id", models.UUIDField(default=apps.core.models.uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("record_type", models.CharField(choices=[("timesheet", "ساعت کاری"), ("leave", "مرخصی"), ("work_report", "گزارش کاری")], db_index=True, max_length=16)),
                ("record_id", models.UUIDField(db_index=True)),
                ("from_status", models.CharField(choices=[("pending", "در انتظار بررسی"), ("approved", "تأییدشده"), ("rejected", "ردشده"), ("cancelled", "لغوشده")], default="pending", max_length=16)),
                ("to_status", models.CharField(choices=[("pending", "در انتظار بررسی"), ("approved", "تأییدشده"), ("rejected", "ردشده"), ("cancelled", "لغوشده")], max_length=16)),
                ("comment", models.TextField(blank=True, default="")),
                ("rejection_reason", models.TextField(blank=True, default="")),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("actor", models.ForeignKey(db_index=True, on_delete=models.deletion.PROTECT, related_name="staff_review_actions", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "staff_review_history",
                "verbose_name": "Review History (تاریخچه بررسی)",
                "verbose_name_plural": "Review Histories (تاریخچه‌های بررسی)",
                "ordering": ("-created_at",),
            },
        ),
        migrations.CreateModel(
            name="LeaveType",
            fields=[
                ("created_at", models.DateTimeField(db_index=True, default=apps.core.models.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("id", models.UUIDField(default=apps.core.models.uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("code", models.SlugField(db_index=True, max_length=64)),
                ("name", models.CharField(max_length=128)),
                ("accrual", models.CharField(choices=[("unlimited", "نامحدود"), ("annual", "سالانه (استحقاقی)"), ("sick", "استعلاجی"), ("unpaid", "بدون حقوق")], db_index=True, default="unlimited", max_length=16)),
                ("default_days", models.PositiveSmallIntegerField(default=0)),
                ("requires_document", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
            ],
            options={
                "db_table": "staff_leave_type",
                "verbose_name": "Leave Type (نوع مرخصی)",
                "verbose_name_plural": "Leave Types (انواع مرخصی)",
                "ordering": ("name",),
            },
        ),
        migrations.CreateModel(
            name="TimesheetEntry",
            fields=[
                ("created_at", models.DateTimeField(db_index=True, default=apps.core.models.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("id", models.UUIDField(default=apps.core.models.uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("work_date", models.DateField(db_index=True, help_text="تاریخ کاری (شمسی در ورودی/خروجی)")),
                ("kind", models.CharField(choices=[("regular", "عادی"), ("overtime", "اضافه‌کار"), ("holiday", "تعطیلی کارگاهی")], db_index=True, default="regular", max_length=16)),
                ("check_in", models.DateTimeField(db_index=True, help_text="زمان ورود")),
                ("check_out", models.DateTimeField(blank=True, db_index=True, help_text="زمان خروج", null=True)),
                ("override_minutes", models.PositiveIntegerField(blank=True, help_text="اصلاح دستی مدت کارکرد (دقیقه) — خالی = محاسبه از ورود/خروج.", null=True)),
                ("note", models.CharField(blank=True, default="", max_length=500)),
                ("status", models.CharField(choices=[("pending", "در انتظار بررسی"), ("approved", "تأییدشده"), ("rejected", "ردشده"), ("cancelled", "لغوشده")], db_index=True, default="pending", max_length=16)),
                ("rejection_reason", models.TextField(blank=True, default="")),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("user", models.ForeignKey(db_index=True, on_delete=models.deletion.CASCADE, related_name="timesheet_entries", to=settings.AUTH_USER_MODEL)),
                ("person", models.ForeignKey(blank=True, help_text="پروفایل اشخاص کارمند/مدرس — مثل سایر ماژول‌ها، هویت اینجا تکرار نمی‌شود.", null=True, on_delete=models.deletion.SET_NULL, related_name="timesheet_entries", to="persons.person")),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name="reviewed_timesheets", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "staff_timesheet_entry",
                "verbose_name": "Timesheet Entry (ساعت کاری)",
                "verbose_name_plural": "Timesheet Entries (ساعت‌های کاری)",
                "ordering": ("-work_date", "-check_in"),
            },
        ),
        migrations.AddConstraint(
            model_name="timesheetentry",
            constraint=models.UniqueConstraint(condition=models.Q(is_deleted=False), fields=("user", "work_date", "kind"), name="uniq_staff_timesheet_user_date_kind_alive", violation_error_message="برای این کاربر در این روز قبلاً ساعت کاری ثبت شده است."),
        ),
        migrations.AddConstraint(
            model_name="timesheetentry",
            constraint=models.CheckConstraint(condition=models.Q(check_out__isnull=True) | models.Q(check_out__gt=models.F("check_in")), name="chk_staff_timesheet_checkout_after_checkin"),
        ),
        migrations.CreateModel(
            name="LeaveRequest",
            fields=[
                ("created_at", models.DateTimeField(db_index=True, default=apps.core.models.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("id", models.UUIDField(default=apps.core.models.uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("start_date", models.DateField(db_index=True)),
                ("end_date", models.DateField(db_index=True)),
                ("unit", models.CharField(choices=[("day", "روز"), ("half_day", "نیم‌روز"), ("hour", "ساعت")], db_index=True, default="day", max_length=16)),
                ("duration", models.DecimalField(decimal_places=2, default=0, help_text="مدت مرخصی بر حسب unit (پس از اعتبارسنجی محاسبه می‌شود).", max_digits=7, validators=[django.core.validators.MaxValueValidator(366)])),
                ("description", models.TextField(blank=True, default="")),
                ("attachment", models.FileField(blank=True, help_text="مدرک مرخصی استعلاجی (در صورت نیاز).", null=True, upload_to="staff/leave/")),
                ("status", models.CharField(choices=[("pending", "در انتظار بررسی"), ("approved", "تأییدشده"), ("rejected", "ردشده"), ("cancelled", "لغوشده")], db_index=True, default="pending", max_length=16)),
                ("rejection_reason", models.TextField(blank=True, default="")),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("user", models.ForeignKey(db_index=True, on_delete=models.deletion.PROTECT, related_name="leave_requests", to=settings.AUTH_USER_MODEL)),
                ("person", models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name="leave_requests", to="persons.person")),
                ("leave_type", models.ForeignKey(db_index=True, on_delete=models.deletion.PROTECT, related_name="requests", to="staff.leavetype")),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name="reviewed_leave_requests", to=settings.AUTH_USER_MODEL)),
                ("workflow_instance", models.ForeignKey(blank=True, help_text="مسیر گردش‌کار اختیاری (تأیید چندسطحی). گزارش از همین ردیف می‌خواند.", null=True, on_delete=models.deletion.SET_NULL, related_name="leave_requests", to="workflow.instance")),
            ],
            options={
                "db_table": "staff_leave_request",
                "verbose_name": "Leave Request (درخواست مرخصی)",
                "verbose_name_plural": "Leave Requests (درخواست‌های مرخصی)",
                "ordering": ("-start_date",),
            },
        ),
        migrations.AddConstraint(
            model_name="leaverequest",
            constraint=models.CheckConstraint(condition=models.Q(end_date__gte=models.F("start_date")), name="chk_staff_leave_date_range"),
        ),
        migrations.AddConstraint(
            model_name="leaverequest",
            constraint=models.CheckConstraint(condition=models.Q(duration__gte=0), name="chk_staff_leave_duration_positive"),
        ),
        migrations.CreateModel(
            name="WorkReport",
            fields=[
                ("created_at", models.DateTimeField(db_index=True, default=apps.core.models.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("id", models.UUIDField(default=apps.core.models.uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("report_date", models.DateField(db_index=True)),
                ("title", models.CharField(help_text="عنوان فعالیت اصلی روز", max_length=256)),
                ("description", models.TextField(blank=True, default="", help_text="توضیحات فعالیت")),
                ("spent_minutes", models.PositiveIntegerField(default=0, help_text="مدت زمان صرف‌شده (دقیقه)")),
                ("status", models.CharField(choices=[("pending", "در انتظار بررسی"), ("approved", "تأییدشده"), ("rejected", "ردشده"), ("cancelled", "لغوشده")], db_index=True, default="pending", max_length=16)),
                ("rejection_reason", models.TextField(blank=True, default="")),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("user", models.ForeignKey(db_index=True, on_delete=models.deletion.CASCADE, related_name="work_reports", to=settings.AUTH_USER_MODEL)),
                ("person", models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name="work_reports", to="persons.person")),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name="reviewed_work_reports", to=settings.AUTH_USER_MODEL)),
                ("timesheet", models.ForeignKey(blank=True, help_text="ساعت کاری همان روز — منبع حقیقت مدت زمان.", null=True, on_delete=models.deletion.SET_NULL, related_name="work_reports", to="staff.timesheetentry")),
            ],
            options={
                "db_table": "staff_work_report",
                "verbose_name": "Work Report (گزارش کاری)",
                "verbose_name_plural": "Work Reports (گزارش‌های کاری)",
                "ordering": ("-report_date",),
            },
        ),
        migrations.AddConstraint(
            model_name="workreport",
            constraint=models.CheckConstraint(condition=models.Q(spent_minutes__lte=1440), name="chk_staff_report_minutes_in_day"),
        ),
        migrations.AddIndex(
            model_name="reviewhistory",
            index=models.Index(fields=["record_type", "record_id", "-created_at"], name="staff_rev_record_created_idx"),
        ),
        migrations.AddIndex(
            model_name="reviewhistory",
            index=models.Index(fields=["actor", "-created_at"], name="staff_review_actor_created_idx"),
        ),
        migrations.AddIndex(
            model_name="leavetype",
            index=models.Index(fields=["accrual", "is_active"], name="staff_lt_accrual_active_idx"),
        ),
        migrations.AddIndex(
            model_name="timesheetentry",
            index=models.Index(fields=["work_date", "status"], name="staff_ts_date_status_idx"),
        ),
        migrations.AddIndex(
            model_name="timesheetentry",
            index=models.Index(fields=["user", "work_date"], name="staff_ts_user_date_idx"),
        ),
        migrations.AddIndex(
            model_name="timesheetentry",
            index=models.Index(fields=["status", "work_date"], name="staff_ts_status_date_idx"),
        ),
        migrations.AddIndex(
            model_name="leaverequest",
            index=models.Index(fields=["user", "status"], name="staff_lr_user_status_idx"),
        ),
        migrations.AddIndex(
            model_name="leaverequest",
            index=models.Index(fields=["start_date", "end_date"], name="staff_lr_range_idx"),
        ),
        migrations.AddIndex(
            model_name="leaverequest",
            index=models.Index(fields=["status", "start_date"], name="staff_lr_status_start_idx"),
        ),
        migrations.AddIndex(
            model_name="leaverequest",
            index=models.Index(fields=["leave_type", "status"], name="staff_lr_type_status_idx"),
        ),
        migrations.AddIndex(
            model_name="workreport",
            index=models.Index(fields=["user", "report_date"], name="staff_wr_user_date_idx"),
        ),
        migrations.AddIndex(
            model_name="workreport",
            index=models.Index(fields=["report_date", "status"], name="staff_wr_date_status_idx"),
        ),
        migrations.AddIndex(
            model_name="workreport",
            index=models.Index(fields=["status", "report_date"], name="staff_wr_status_date_idx"),
        ),
    ]
