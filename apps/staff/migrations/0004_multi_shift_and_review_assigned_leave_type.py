from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("staff", "0003_leaverequest_start_end_time"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="timesheetentry",
            name="uniq_staff_timesheet_user_date_kind_alive",
        ),
        migrations.AlterField(
            model_name="leaverequest",
            name="leave_type",
            field=models.ForeignKey(
                blank=True,
                help_text="درخواست‌کننده نوع را تعیین نمی‌کند؛ مسئول بررسی هنگام تصمیم آن را ثبت می‌کند.",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="requests",
                to="staff.leavetype",
            ),
        ),
    ]
