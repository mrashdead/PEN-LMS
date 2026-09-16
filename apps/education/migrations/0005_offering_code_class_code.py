# Hand-written: «برگزاری دوره» unique code + «تشکیل کلاس» class_code.
#
#   CourseOffering.code            — unique business key of a run
#       (OFFERING-1403-PY01); auto of-0001 when the form leaves it empty.
#   ClassSession.class_code        — final class code (CLS-PY-01) shared by
#       the sessions of one lesson within an offering; session numbering is
#       per (offering, class_code) instead of per offering.
#
# Backfill: existing offerings get sequential of-XXXX codes (oldest first,
# scanning soft-deleted rows too so retired codes are never reused).

import re

import django.core.validators
from django.db import migrations, models


def _backfill_offering_codes(apps, schema_editor):
    CourseOffering = apps.get_model("education", "CourseOffering")
    pattern = re.compile(r"^of-(\d{4})$")
    last = 0
    for value in CourseOffering._base_manager.values_list("code", flat=True):
        m = pattern.match(str(value or ""))
        if m:
            last = max(last, int(m.group(1)))
    qs = (
        CourseOffering._base_manager.filter(
            models.Q(code="") | models.Q(code__isnull=True)
        )
        .order_by("created_at")
    )
    for offering in qs:
        last += 1
        offering.code = f"of-{last:04d}"
        offering.save(update_fields=["code"])


class Migration(migrations.Migration):

    dependencies = [
        ("education", "0004_academic_holiday_offering_session_count"),
    ]

    operations = [
        migrations.AddField(
            model_name="courseoffering",
            name="code",
            field=models.CharField(
                blank=True,
                default="",
                help_text="عنوان/کد برگزاری — یکتا. مثال: OFFERING-1403-PY01؛ اگر خالی بماند به‌صورت خودکار of-0001 ساخته می‌شود.",
                max_length=64,
                validators=[
                    django.core.validators.RegexValidator(
                        "^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$",
                        "کد باید با حرف یا رقم شروع شود و فقط شامل حروف لاتین، رقم، «-»، «_» یا «.» باشد.",
                    )
                ],
            ),
        ),
        migrations.AddConstraint(
            model_name="courseoffering",
            constraint=models.UniqueConstraint(
                condition=models.Q(("is_deleted", False), ("code", ""), _negated=True),
                fields=("code",),
                name="uniq_edu_offering_code_alive",
            ),
        ),
        migrations.RunPython(
            _backfill_offering_codes,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AddField(
            model_name="classsession",
            name="class_code",
            field=models.CharField(
                blank=True,
                default="",
                help_text="کد کلاس — مثال CLS-PY-01 (خالی = جلسات قدیمی/بدون کلاس)",
                max_length=64,
                validators=[
                    django.core.validators.RegexValidator(
                        "^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$",
                        "کد باید با حرف یا رقم شروع شود و فقط شامل حروف لاتین، رقم، «-»، «_» یا «.» باشد.",
                    )
                ],
            ),
        ),
        migrations.RemoveConstraint(
            model_name="classsession",
            name="uniq_edu_session_number_alive",
        ),
        migrations.AddConstraint(
            model_name="classsession",
            constraint=models.UniqueConstraint(
                condition=models.Q(
                    ("is_deleted", False), ("offering__isnull", False)
                ),
                fields=("offering", "class_code", "session_number"),
                name="uniq_edu_session_class_number_alive",
            ),
        ),
    ]
