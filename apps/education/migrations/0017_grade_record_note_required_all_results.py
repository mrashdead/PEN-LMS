from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("education", "0016_studentprogressreport_class_report_id")]

    operations = [
        migrations.AlterField(
            model_name="graderecord",
            name="teacher_note",
            field=models.CharField(
                help_text="بازخورد توصیفی مدرس — برای هر نتیجه اجباری است.",
                max_length=1000,
            ),
        ),
    ]
