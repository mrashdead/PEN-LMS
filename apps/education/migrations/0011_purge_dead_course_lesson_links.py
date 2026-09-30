"""پاک‌سازی ردیف‌های soft-deleted باقی‌ماندهٔ سرفصل دوره (CourseLesson).

هر «ذخیرهٔ ویرایش» دوره، تمام ردیف‌های CourseLesson را soft-delete می‌کرد و
از نو می‌ساخت. مدیر M2M جنگو جدول واسط را بدون فیلتر soft-delete آن join
می‌کند، پس همان درس پس از ویرایش **دوبار** در «درس‌ها» / «شهریهٔ کل» و در
برگزاری‌های ساخته‌شده از آن دوره دیده می‌شد (شهریه و ساعت تدریس دوبرابر).

منطق ویرایش در CourseSerializer اکنون diff-محور است و دیگر ردیف مرده
نمی‌سازد؛ این مهاجرت داده‌های خرابِ ثبت‌شده را یک‌بار برای همیشه پاک می‌کند.
ردیف‌های لینک تاریخچهٔ مستقل ندارند (سرفصل = همان ردیف‌های زنده)، بنابراین
حذف فیزیکی آن‌ها امن است. ردیف‌های زنده و اعتبارسنجی‌های یکتا دست‌نخورده‌اند.
"""
from django.db import migrations


def purge_dead_links(apps, schema_editor):
    # مهاجرت‌ها از مدیر ساده استفاده می‌کنند (SoftDeleteManager در مهاجرت
    # بارگذاری نمی‌شود) پس این delete واقعاً فیزیکی است.
    CourseLesson = apps.get_model("education", "CourseLesson")
    CourseLesson.objects.filter(is_deleted=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("education", "0010_studentprogressreport"),
    ]

    operations = [
        migrations.RunPython(purge_dead_links, migrations.RunPython.noop),
    ]
