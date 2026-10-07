from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("persons", "0009_alter_guardianprofile_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="studentprofile",
            name="emergency_contact_name",
            field=models.CharField(blank=True, default="", max_length=128),
        ),
        migrations.AddField(
            model_name="studentprofile",
            name="emergency_phone",
            field=models.CharField(blank=True, default="", max_length=11),
        ),
    ]
