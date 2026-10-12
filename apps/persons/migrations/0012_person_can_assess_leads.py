from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("persons", "0011_temporary_person_identity")]
    operations = [migrations.AddField(
        model_name="person", name="can_assess_leads",
        field=models.BooleanField(db_index=True, default=False),
    )]
