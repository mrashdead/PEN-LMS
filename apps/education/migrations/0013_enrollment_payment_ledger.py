import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


def backfill_payment_ledger(apps, schema_editor):
    Enrollment = apps.get_model("education", "OfferingEnrollment")
    Payment = apps.get_model("education", "EnrollmentPayment")
    db = schema_editor.connection.alias
    for enrollment in Enrollment.objects.using(db).filter(is_deleted=False).iterator():
        if enrollment.payment_method == "cheque":
            cheques = enrollment.cheques if isinstance(enrollment.cheques, list) else []
            for cheque in cheques:
                amount = int(cheque.get("amount") or 0)
                if amount <= 0:
                    continue
                key = uuid.uuid4()
                Payment.objects.using(db).create(
                    id=key, enrollment_id=enrollment.pk, amount=amount, method="cheque",
                    tracking_code=f"PAY-{key.hex[:20].upper()}",
                    reference=str(cheque.get("tracking_no") or "")[:128],
                    cheque_payee=str(cheque.get("payee") or "")[:160],
                    paid_at=enrollment.created_at, recorded_by_id=None,
                )
            continue
        if enrollment.payment_method not in {"cash", "pos", "card_transfer"} or not enrollment.final_amount:
            continue
        key = uuid.uuid4()
        Payment.objects.using(db).create(
            id=key, enrollment_id=enrollment.pk, amount=enrollment.final_amount,
            method=enrollment.payment_method, tracking_code=f"PAY-{key.hex[:20].upper()}",
            reference=enrollment.reference or "", paid_at=enrollment.created_at,
            recorded_by_id=None,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("education", "0012_lesson_space_type_choices"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="offeringenrollment",
            name="payment_method",
            field=models.CharField(
                choices=[("cash", "نقدی"), ("pos", "کارت‌خوان (POS)"), ("cheque", "چک"),
                         ("card_transfer", "کارت‌به‌کارت"), ("mixed", "ترکیبی")],
                default="cash", max_length=16,
            ),
        ),
        migrations.CreateModel(
            name="EnrollmentPayment",
            fields=[
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("amount", models.PositiveIntegerField(help_text="مبلغ پرداخت به تومان")),
                ("method", models.CharField(choices=[("cash", "نقدی"), ("pos", "کارت‌خوان (POS)"), ("cheque", "چک"), ("card_transfer", "کارت‌به‌کارت")], max_length=16)),
                ("tracking_code", models.CharField(blank=True, max_length=32, unique=True)),
                ("payer_name", models.CharField(blank=True, default="", help_text="نام شخصی که مبلغ را پرداخت کرده است", max_length=160)),
                ("reference", models.CharField(blank=True, default="", help_text="شمارهٔ رسید یا مرجع بانکی", max_length=128)),
                ("cheque_number", models.CharField(blank=True, default="", max_length=64)),
                ("cheque_payee", models.CharField(blank=True, default="", max_length=160)),
                ("cheque_due_date", models.DateField(blank=True, null=True)),
                ("paid_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("enrollment", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="payments", to="education.offeringenrollment")),
                ("recorded_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="enrollment_payments", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "education_enrollment_payment",
                "ordering": ("-paid_at", "-created_at"),
            },
        ),
        migrations.RunPython(backfill_payment_ledger, migrations.RunPython.noop),
        migrations.AddIndex(
            model_name="enrollmentpayment",
            index=models.Index(fields=["enrollment", "-paid_at"], name="edu_payment_enroll_idx"),
        ),
        migrations.AddConstraint(
            model_name="enrollmentpayment",
            constraint=models.CheckConstraint(condition=models.Q(amount__gt=0), name="edu_payment_amount_gt_zero"),
        ),
    ]
