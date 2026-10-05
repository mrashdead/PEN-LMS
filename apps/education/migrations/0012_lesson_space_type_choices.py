from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("education", "0011_purge_dead_course_lesson_links"),
    ]

    operations = [
        migrations.AlterField(
            model_name="lesson",
            name="space_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("", "نامشخص"),
                    ("theory", "کلاس تئوری"),
                    ("open_air", "فضای باز"),
                    ("workshop", "کارگاه"),
                    ("online", "کلاس آنلاین"),
                ],
                default="",
                help_text="نوع فضای آموزشی پیشنهادی",
                max_length=16,
            ),
        ),
    ]
