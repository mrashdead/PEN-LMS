"""
Migration 0009: Add subject_person to Instance.

یکپارچه‌سازی فرم‌ها و گردش‌کار (§forms-workflow unification):

  - Instance.subject_person: FK به Person — شخص هدف درخواست
    (مثلاً دانش‌آموزی که حضور و غیاب برایش ثبت می‌شود).

  - WorkflowEngineService._enqueue_notifications به subject_person.user هم
    اعلان می‌فرستد (اگر کاربر متصل داشته باشد).

  - FormSubmissionService._start_workflow این فیلد را از داده‌ی فرم
    (submission.subject_person_id) به create_instance پاس می‌دهد.

مقداردهی اولیه: تمام نمونه‌های موجود بدون subject_person می‌مانند
(null) — only new submissions get a target set.
"""
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0008_request_tracking_numbers"),
        ("persons", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="instance",
            name="subject_person",
            field=models.ForeignKey(
                blank=True,
                help_text=(
                    "شخص هدف این درخواست (دانش‌آموز/کارمند/مدرس). از داده‌ی فرم استخراج "
                    "می‌شود و گیرنده‌ی اصلی اعلان‌هاست — واحد یکپارچه‌سازی فرم‌ها و گردش‌کار."
                ),
                null=True,
                on_delete=models.SET_NULL,
                related_name="subject_workflow_instances",
                to="persons.Person",
            ),
        ),
        migrations.AddIndex(
            model_name="instance",
            index=models.Index(
                fields=["subject_person"],
                name="workflow_ins_subjec_idx",
            ),
        ),
    ]