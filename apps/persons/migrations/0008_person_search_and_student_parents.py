from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("persons", "0007_guardian_profiles"),
    ]

    operations = [
        migrations.AlterField(
            model_name="person",
            name="first_name",
            field=models.CharField(db_index=True, max_length=128),
        ),
        migrations.AlterField(
            model_name="person",
            name="last_name",
            field=models.CharField(db_index=True, max_length=128),
        ),
        migrations.AddField(
            model_name="studentprofile",
            name="father_first_name",
            field=models.CharField(blank=True, default="", max_length=128),
        ),
        migrations.AddField(
            model_name="studentprofile",
            name="father_last_name",
            field=models.CharField(blank=True, default="", max_length=128),
        ),
        migrations.AddField(
            model_name="studentprofile",
            name="father_phone",
            field=models.CharField(blank=True, default="", max_length=11),
        ),
        migrations.AddField(
            model_name="studentprofile",
            name="mother_first_name",
            field=models.CharField(blank=True, default="", max_length=128),
        ),
        migrations.AddField(
            model_name="studentprofile",
            name="mother_last_name",
            field=models.CharField(blank=True, default="", max_length=128),
        ),
        migrations.AddField(
            model_name="studentprofile",
            name="mother_phone",
            field=models.CharField(blank=True, default="", max_length=11),
        ),
    ]
