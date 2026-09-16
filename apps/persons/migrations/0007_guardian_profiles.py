# Hand-written: dynamic-onboarding profiles + guardianship (تکفل).
#
# Adds Person.Type.GUARDIAN back as a first-class type (the StudentParent
# table deleted in 0006 is replaced by the richer StudentGuardian link below),
# plus the role-specific profile rows the onboarding wizard writes atomically:
# StudentProfile, GuardianProfile, StudentGuardian, StaffProfile.
#
# NOTE: no data migration is included — soft-deleted 0001-era
# persons_student_parent rows still exist in DBs that had them; they are
# superseded by persons_student_guardian and can be archived later if desired.

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("persons", "0006_alter_person_person_type_and_more"),
        ("education", "0003_remove_lesson_assessment_method_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── guardian becomes a Person type again ────────────────────────────
        migrations.AlterField(
            model_name="person",
            name="person_type",
            field=models.CharField(
                choices=[
                    ("student", "دانش‌آموز"),
                    ("teacher", "معلم / مدرس"),
                    ("employee", "کارمند"),
                    ("guardian", "ولی / سرپرست (والدین)"),
                ],
                db_index=True,
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name="persontypeassignment",
            name="type",
            field=models.CharField(
                choices=[
                    ("student", "دانش‌آموز"),
                    ("teacher", "معلم / مدرس"),
                    ("employee", "کارمند"),
                    ("guardian", "ولی / سرپرست (والدین)"),
                ],
                db_index=True,
                max_length=32,
            ),
        ),
        # ── StudentProfile ──────────────────────────────────────────────────
        migrations.CreateModel(
            name="StudentProfile",
            fields=[
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("grade_level", models.CharField(blank=True, default="", help_text="پایه/پادگان تحصیلی (نمایشی؛ ساختار درختی در education.Department).", max_length=32)),
                ("class_section", models.CharField(blank=True, default="", help_text="شعبه کلاس", max_length=32)),
                ("school_year", models.CharField(blank=True, default="", help_text="سال تحصیلی، مثال 1405-1406", max_length=16)),
                ("enrollment_date", models.DateField(blank=True, null=True)),
                ("birth_certificate_no", models.CharField(blank=True, default="", max_length=32)),
                ("health_notes", models.TextField(blank=True, default="", help_text="محدودیت/بیماری اعلام‌شده — PII پزشکی؛ فقط حافظان کامل می‌بینند.")),
                ("has_special_needs", models.BooleanField(default=False)),
                ("is_custody_case", models.BooleanField(default=False, help_text="وضعیت تکفل: دانش‌آموز تحت تکفل والد غیراز ولایت/قیم خاص است.")),
                ("custody_note", models.CharField(blank=True, default="", max_length=256)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("person", models.OneToOneField(
                    limit_choices_to={"person_type": "student"},
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="student_profile",
                    to="persons.person",
                )),
            ],
            options={
                "verbose_name": "Student Profile (پروفایل دانش‌آموز)",
                "verbose_name_plural": "Student Profiles (پروفایل‌های دانش‌آموز)",
                "db_table": "persons_student_profile",
                "ordering": ("-created_at",),
            },
        ),
        # ── GuardianProfile ─────────────────────────────────────────────────
        migrations.CreateModel(
            name="GuardianProfile",
            fields=[
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("occupation", models.CharField(blank=True, default="", max_length=128)),
                ("education_level", models.CharField(blank=True, default="", max_length=64)),
                ("preferred_contact", models.CharField(blank=True, default="", help_text="کانال ترجیحی اطلاع‌رسانی: sms / call / in_app", max_length=20)),
                ("is_primary", models.BooleanField(default=False, help_text="ولی اصلی — مخاطب رسمی مؤسسه برای اعلان‌ها و صورت‌حساب.")),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("person", models.OneToOneField(
                    limit_choices_to={"person_type": "guardian"},
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="guardian_profile",
                    to="persons.person",
                )),
            ],
            options={
                "verbose_name": "Guardian Profile (پروفایل ولی)",
                "verbose_name_plural": "Guardian Profiles (پروفایل اولیا)",
                "db_table": "persons_guardian_profile",
                "ordering": ("-is_primary", "person__last_name"),
            },
        ),
        # ── StaffProfile ────────────────────────────────────────────────────
        migrations.CreateModel(
            name="StaffProfile",
            fields=[
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("kind", models.CharField(
                    choices=[("teaching", "مدرس (تدریس)"), ("administrative", "کارمند اداری"), ("technical", "کارمند فنی")],
                    db_index=True, default="administrative", max_length=20,
                )),
                ("contract_no", models.CharField(blank=True, db_index=True, default="", max_length=64)),
                ("contract_type", models.CharField(blank=True, default="", help_text="نوع قرارداد: رسمی / پیمانی / حق‌التدریس / پروژه‌ای", max_length=32)),
                ("contract_start", models.DateField(blank=True, null=True)),
                ("contract_end", models.DateField(blank=True, db_index=True, null=True)),
                ("hourly_rate", models.PositiveIntegerField(default=0, help_text="حق‌التدریس هر ساعت (تومان) — ۰ = نامشخص/پرداخت ماهانه")),
                ("weekly_max_hours", models.PositiveSmallIntegerField(default=0, help_text="سقف ساعات هفتگی تدریس — ورودی موتور زمان‌بندی")),
                ("specialization", models.CharField(blank=True, default="", help_text="تخصص/حوزه‌ی تدریس (متن آزاد؛ دپارتمان مرجع از education.Department)", max_length=256)),
                ("academic_degree", models.CharField(blank=True, default="", max_length=64)),
                ("experience_years", models.PositiveSmallIntegerField(default=0)),
                ("bio", models.TextField(blank=True, default="", help_text="سوابق و رزومه (خلاصه).")),
                ("credentials", models.JSONField(blank=True, default=list, help_text="مدارک/گواهینامه‌ها: [{title, issuer, issued_at, file}]")),
                ("is_verified", models.BooleanField(default=False, help_text="مدارک توسط امور اداری بررسی/تأیید شده است.")),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("department", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="staff",
                    to="education.department",
                )),
                ("person", models.OneToOneField(
                    limit_choices_to={"person_type__in": ["teacher", "employee"]},
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="staff_profile",
                    to="persons.person",
                )),
            ],
            options={
                "verbose_name": "Staff/Teacher Profile (پروفایل کارمند/مدرس)",
                "verbose_name_plural": "Staff/Teacher Profiles (پروفایل کارمندان/مدرسان)",
                "db_table": "persons_staff_profile",
                "ordering": ("kind", "person__last_name"),
            },
        ),
        # ── StudentGuardian (تکفل) ──────────────────────────────────────────
        migrations.CreateModel(
            name="StudentGuardian",
            fields=[
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("relation", models.CharField(
                    choices=[("father", "پدر"), ("mother", "مادر"),
                             ("legal_guardian", "قیم / سرپرست قانونی"), ("other", "سایر")],
                    default="other", max_length=32,
                )),
                ("custody_status", models.CharField(
                    choices=[("under_custody", "تحت تکفل"), ("custody_other", "تکفل با والد دیگر"),
                             ("full_guardian", "ولایت/سرپرستی کامل"), ("visitation", "فقط ملاقات (بدون حق امضا)")],
                    default="under_custody", max_length=20,
                )),
                ("can_view_grades", models.BooleanField(default=True)),
                ("can_view_attendance", models.BooleanField(default=True)),
                ("can_submit_requests", models.BooleanField(default=True)),
                ("can_receive_billing", models.BooleanField(default=False)),
                ("phone_override", models.CharField(blank=True, default="", help_text="شماره تماس این رابطه (اگر با Person.mobile متفاوت است).", max_length=20)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("valid_from", models.DateField(blank=True, null=True)),
                ("valid_to", models.DateField(blank=True, null=True)),
                ("guardian", models.ForeignKey(
                    limit_choices_to={"person_type": "guardian"},
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="ward_links",
                    to="persons.person",
                )),
                ("student", models.ForeignKey(
                    limit_choices_to={"person_type": "student"},
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="guardians",
                    to="persons.person",
                )),
            ],
            options={
                "verbose_name": "Student-Guardian link (تکفل)",
                "verbose_name_plural": "Student-Guardian links (تکفلات)",
                "db_table": "persons_student_guardian",
                "ordering": ("student", "relation"),
            },
        ),
        # ── constraints & indexes ───────────────────────────────────────────
        migrations.AddConstraint(
            model_name="studentguardian",
            constraint=models.UniqueConstraint(
                condition=models.Q(("is_deleted", False)),
                fields=("student", "guardian"),
                name="uniq_persons_student_guardian_alive",
                violation_error_message="این ولی قبلاً به این دانش‌آموز متصل شده است.",
            ),
        ),
        migrations.AddConstraint(
            model_name="studentguardian",
            constraint=models.CheckConstraint(
                condition=~models.Q(student=models.F("guardian")),
                name="chk_persons_guardian_not_self",
            ),
        ),
        migrations.AddIndex(
            model_name="studentguardian",
            index=models.Index(fields=["guardian", "is_active"], name="persons_sg_guardian_active_idx"),
        ),
        migrations.AddIndex(
            model_name="studentguardian",
            index=models.Index(fields=["student", "is_active"], name="persons_sg_student_active_idx"),
        ),
        migrations.AddConstraint(
            model_name="staffprofile",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(("contract_end__isnull", True))
                    | models.Q(("contract_start__isnull", True))
                    | models.Q(contract_end__gt=models.F("contract_start"))
                ),
                name="chk_persons_contract_end_after_start",
            ),
        ),
        migrations.AddIndex(
            model_name="staffprofile",
            index=models.Index(fields=["kind", "is_active"], name="persons_sp_kind_active_idx"),
        ),
        migrations.AddIndex(
            model_name="staffprofile",
            index=models.Index(fields=["department"], name="persons_sp_department_idx"),
        ),
        migrations.AddIndex(
            model_name="studentprofile",
            index=models.Index(fields=["grade_level", "is_active"], name="persons_stu_grade_active_idx"),
        ),
    ]
