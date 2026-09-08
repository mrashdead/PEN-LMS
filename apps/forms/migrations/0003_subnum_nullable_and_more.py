# Hand-written to match apps/forms/models.py (submission_number nullable).
# PostgreSQL allows many NULLs under a UNIQUE constraint, so drafts no longer
# collide on the shared empty string; SQLite (tests) behaves the same.
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forms', '0002_rename_forms_attach_sub_field_idx_forms_attac_submiss_7981b1_idx_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='formsubmission',
            name='submission_number',
            field=models.CharField(blank=True, help_text='FORM-{SLUG}-{YEAR}-{SEQ}; NULL until allocated.', max_length=200, null=True, unique=True),
        ),
    ]
