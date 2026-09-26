"""
Initial migration for apps.calls — hand-authored (project convention).
"""
from django.conf import settings
import django.core.validators
from django.db import migrations, models

import apps.core.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("accounts", "0003_user_uniq_user_employee_code_alive"),
        ("contenttypes", "0002_remove_content_type_name"),
        ("education", "0008_offeringenrollment_final_class_enrollment_and_more"),
        ("leads", "0001_initial"),
        ("persons", "0009_alter_guardianprofile_options_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CallSubject",
            fields=[
                ("created_at", models.DateTimeField(db_index=True, default=apps.core.models.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("id", models.UUIDField(default=apps.core.models.uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("code", models.SlugField(db_index=True, max_length=64)),
                ("name", models.CharField(max_length=128)),
                ("department", models.CharField(blank=True, db_index=True, default="", max_length=128)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
            ],
            options={
                "db_table": "calls_call_subject",
                "verbose_name": "Call Subject (موضوع تماس)",
                "verbose_name_plural": "Call Subjects (موضوع‌های تماس)",
                "ordering": ("name",),
            },
        ),
        migrations.AddConstraint(
            model_name="callsubject",
            constraint=models.UniqueConstraint(condition=models.Q(is_deleted=False), fields=("code",), name="uniq_calls_subject_code_alive"),
        ),
        migrations.CreateModel(
            name="InboundCall",
            fields=[
                ("created_at", models.DateTimeField(db_index=True, default=apps.core.models.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("id", models.UUIDField(default=apps.core.models.uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("caller_name", models.CharField(blank=True, default="", help_text="نام تماس‌گیرنده (خالی = ناشناس).", max_length=256)),
                ("caller_phone", models.CharField(db_index=True, help_text="شماره تماس گیرنده — پیش‌شماره و اعداد لاتین.", max_length=20, validators=[django.core.validators.RegexValidator(r"^[0-9+\\-\\s()]{3,20}$", "شماره تلفن معتبر نیست.")])),
                ("department", models.CharField(blank=True, db_index=True, default="", max_length=128)),
                ("direction", models.CharField(choices=[("inbound", "دریافتی"), ("outbound", "خروجی (پیگیری)")], db_index=True, default="inbound", max_length=16)),
                ("called_at", models.DateTimeField(db_index=True, help_text="تاریخ و ساعت تماس")),
                ("subject", models.CharField(db_index=True, help_text="موضوع تماس — متن کوتاه قابل فیلتر.", max_length=256)),
                ("description", models.TextField(blank=True, default="")),
                ("result", models.CharField(choices=[("answered", "پاسخ داده شد"), ("no_answer", "پاسخ داده نشد"), ("busy", "اشغال"), ("voicemail", "پیام صوتی"), ("transferred", "ارجاع به بخش دیگر"), ("follow_up_agreed", "قرار شد دوباره تماس گرفته شود"), ("other", "سایر")], db_index=True, default="answered", max_length=24)),
                ("follow_up_status", models.CharField(choices=[("none", "بدون نیاز به پیگیری"), ("pending", "نیازمند پیگیری"), ("in_progress", "در حال پیگیری"), ("done", "پیگیری شد"), ("missed", "تماس مجدد ناموفق")], db_index=True, default="none", max_length=16)),
                ("next_follow_up_at", models.DateTimeField(blank=True, db_index=True, help_text="تاریخ و ساعت پیگیری بعدی", null=True)),
                ("follow_up_note", models.TextField(blank=True, default="")),
                ("receiver", models.ForeignKey(db_index=True, on_delete=models.deletion.PROTECT, related_name="received_calls", to=settings.AUTH_USER_MODEL)),
                ("person", models.ForeignKey(blank=True, help_text="اگر تماس‌گیرنده شخص ثبت‌شده است، هویت اینجا وصل می‌شود.", null=True, on_delete=models.deletion.SET_NULL, related_name="inbound_calls", to="persons.person")),
                ("department_ref", models.ForeignKey(blank=True, help_text="بخش مرتبط — وقتی به education.Department نگاشت می‌شود، گزارش یکپارچه است.", null=True, on_delete=models.deletion.SET_NULL, related_name="inbound_calls", to="education.department")),
                ("assignee", models.ForeignKey(blank=True, db_index=True, help_text="مسئول پیگیری (خالی = خود دریافت‌کننده).", null=True, on_delete=models.deletion.SET_NULL, related_name="assigned_call_followups", to=settings.AUTH_USER_MODEL)),
                ("related_lead", models.ForeignKey(blank=True, help_text="اگر تماس به یک لید ارتباط دارد (قیف ورودی).", null=True, on_delete=models.deletion.SET_NULL, related_name="calls", to="leads.lead")),
                ("subject_ref", models.ForeignKey(blank=True, db_index=True, help_text="موضوع استاندارد کاتالوگ — گزارش روی این کلید فیلتر می‌کند.", null=True, on_delete=models.deletion.SET_NULL, related_name="calls", to="calls.callsubject")),
            ],
            options={
                "db_table": "calls_inbound_call",
                "verbose_name": "Inbound Call (تماس دریافتی)",
                "verbose_name_plural": "Inbound Calls (تماس‌های دریافتی)",
                "ordering": ("-called_at",),
            },
        ),
        migrations.AddConstraint(
            model_name="inboundcall",
            constraint=models.CheckConstraint(condition=~models.Q(caller_phone=""), name="chk_calls_phone_required"),
        ),
        migrations.AddConstraint(
            model_name="inboundcall",
            constraint=models.CheckConstraint(condition=models.Q(next_follow_up_at__isnull=True) | models.Q(follow_up_status__in=["pending", "in_progress"]), name="chk_calls_followup_next_only_when_pending"),
        ),
        migrations.CreateModel(
            name="CallFollowUpLog",
            fields=[
                ("created_at", models.DateTimeField(db_index=True, default=apps.core.models.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("id", models.UUIDField(default=apps.core.models.uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("previous_status", models.CharField(choices=[("none", "بدون نیاز به پیگیری"), ("pending", "نیازمند پیگیری"), ("in_progress", "در حال پیگیری"), ("done", "پیگیری شد"), ("missed", "تماس مجدد ناموفق")], max_length=16)),
                ("new_status", models.CharField(choices=[("none", "بدون نیاز به پیگیری"), ("pending", "نیازمند پیگیری"), ("in_progress", "در حال پیگیری"), ("done", "پیگیری شد"), ("missed", "تماس مجدد ناموفق")], max_length=16)),
                ("note", models.TextField(blank=True, default="")),
                ("next_follow_up_at", models.DateTimeField(blank=True, null=True)),
                ("call", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="follow_up_logs", to="calls.inboundcall")),
                ("actor", models.ForeignKey(db_index=True, on_delete=models.deletion.PROTECT, related_name="call_follow_up_logs", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "calls_follow_up_log",
                "verbose_name": "Call Follow-up Log (تاریخچه پیگیری)",
                "verbose_name_plural": "Call Follow-up Logs (تاریخچه‌های پیگیری)",
                "ordering": ("-created_at",),
            },
        ),
        migrations.AddIndex(
            model_name="inboundcall",
            index=models.Index(fields=["called_at", "result"], name="calls_date_result_idx"),
        ),
        migrations.AddIndex(
            model_name="inboundcall",
            index=models.Index(fields=["receiver", "called_at"], name="calls_receiver_date_idx"),
        ),
        migrations.AddIndex(
            model_name="inboundcall",
            index=models.Index(fields=["follow_up_status", "next_follow_up_at"], name="calls_followup_next_idx"),
        ),
        migrations.AddIndex(
            model_name="inboundcall",
            index=models.Index(fields=["subject", "called_at"], name="calls_subject_date_idx"),
        ),
        migrations.AddIndex(
            model_name="inboundcall",
            index=models.Index(fields=["department", "called_at"], name="calls_dept_date_idx"),
        ),
        migrations.AddIndex(
            model_name="callfollowuplog",
            index=models.Index(fields=["call", "-created_at"], name="calls_log_call_created_idx"),
        ),
        migrations.AddIndex(
            model_name="callfollowuplog",
            index=models.Index(fields=["actor", "-created_at"], name="calls_log_actor_created_idx"),
        ),
    ]
