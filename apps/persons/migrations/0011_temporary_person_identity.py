from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("persons", "0010_studentprofile_emergency_contact")]

    operations = [
        migrations.AlterField(
            model_name="person",
            name="national_code",
            field=models.CharField(blank=True, db_index=True, help_text="کد ملی — شناسه یکتای شخص (یکتا در میان اشخاص زنده)", max_length=10, null=True),
        ),
        migrations.AddField(
            model_name="person",
            name="temporary_id",
            field=models.UUIDField(blank=True, default=None, editable=False, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="person",
            name="is_temporary",
            field=models.BooleanField(db_index=True, default=False),
        ),
    ]
