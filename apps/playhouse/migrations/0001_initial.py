# Hand-authored initial migration for apps.playhouse (خانه بازی).
# No makemigrations in the sandbox (no pip/network); applied on the
# user's Postgres host. Mirrors apps.playhouse.models exactly.

import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('persons', '0008_person_search_and_student_parents'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PlayhouseConfig',
            fields=[
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('price_per_15_minutes', models.DecimalField(decimal_places=0, default=130000, help_text='هزینه هر ۱۵ دقیقه خانه بازی (تومان)', max_digits=12)),
            ],
            options={
                'verbose_name': 'تنظیمات خانه بازی',
                'verbose_name_plural': 'تنظیمات خانه بازی',
                'db_table': 'playhouse_config',
            },
        ),
        migrations.CreateModel(
            name='PlayhouseMember',
            fields=[
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('first_name', models.CharField(db_index=True, max_length=128)),
                ('last_name', models.CharField(db_index=True, max_length=128)),
                ('age', models.PositiveSmallIntegerField(blank=True, help_text='سن بچه (سال)', null=True)),
                ('guardian_mobile', models.CharField(blank=True, db_index=True, default='', help_text='شماره تماس والدین', max_length=20)),
                ('guardian_name', models.CharField(blank=True, default='', max_length=128)),
                ('notes', models.TextField(blank=True, default='')),
                ('person', models.ForeignKey(blank=True, help_text='لینک به دانش‌آموز / هویت موجود در سیستم (اختیاری)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='playhouse_sessions', to='persons.person')),
            ],
            options={
                'verbose_name': 'عضو خانه بازی',
                'verbose_name_plural': 'اعضای خانه بازی',
                'db_table': 'playhouse_member',
                'ordering': ('-created_at',),
                'constraints': [models.UniqueConstraint(condition=models.Q(('person__isnull', False)), fields=('person',), name='uniq_playhouse_member_person', violation_error_message='این شخص قبلاً به عنوان عضو خانه بازی ثبت شده است.')],
            },
        ),
        migrations.CreateModel(
            name='PlayhouseSession',
            fields=[
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('session_date', models.DateField(blank=True, db_index=True, null=True)),
                ('status', models.CharField(choices=[('waiting', 'در انتظار ورود'), ('active', 'داخل خانه بازی'), ('finished', 'پایان یافته'), ('cancelled', 'لغو شده')], db_index=True, default='waiting', max_length=16)),
                ('entry_at', models.DateTimeField(blank=True, help_text='زمان شروع (دستی)', null=True)),
                ('exit_at', models.DateTimeField(blank=True, help_text='زمان پایان (دستی)', null=True)),
                ('billable_minutes', models.PositiveIntegerField(default=0)),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sessions', to='playhouse.playhousemember')),
                ('operator', models.ForeignKey(help_text='اپراتور ثبت‌کننده (به‌صورت خودکار از کاربر جاری)', on_delete=django.db.models.deletion.PROTECT, related_name='playhouse_sessions', to=settings.AUTH_USER_MODEL)),
                ('ended_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ended_playhouse_sessions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'نوبت خانه بازی',
                'verbose_name_plural': 'نوبت‌های خانه بازی',
                'db_table': 'playhouse_session',
                'ordering': ('-created_at',),
                'indexes': [models.Index(fields=('session_date', 'status'), name='ph_sess_date_status_idx')],
            },
        ),
        migrations.CreateModel(
            name='PlayhouseInvoiceSeq',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.PositiveIntegerField()),
                ('day', models.PositiveIntegerField()),
                ('last_value', models.PositiveIntegerField(default=0)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'playhouse_invoice_seq',
                'constraints': [models.UniqueConstraint(fields=('year', 'day'), name='uniq_playhouse_invoice_seq')],
            },
        ),
        migrations.CreateModel(
            name='PlayhouseInvoice',
            fields=[
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('price_per_15_minutes', models.DecimalField(decimal_places=0, default=0, max_digits=12)),
                ('billed_minutes', models.PositiveIntegerField(default=0)),
                ('time_amount', models.DecimalField(decimal_places=0, default=0, max_digits=12)),
                ('invoice_number', models.CharField(blank=True, db_index=True, max_length=32, unique=True)),
                ('payment_method', models.CharField(blank=True, choices=[('pos', 'دستگاه پوز'), ('card_transfer', 'کارت به کارت')], default='', help_text='روش پرداخت انتخاب‌شده', max_length=16)),
                ('tracking_code', models.CharField(blank=True, default='', help_text='کد رهگیری پوز / کارت به کارت', max_length=64)),
                ('paid_at', models.DateTimeField(blank=True, null=True)),
                ('is_paid', models.BooleanField(db_index=True, default=False)),
                ('notes', models.TextField(blank=True, default='')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='invoices', to='playhouse.playhousemember')),
                ('operator', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='playhouse_invoices', to=settings.AUTH_USER_MODEL)),
                ('session', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='invoice', to='playhouse.playhousesession')),
            ],
            options={
                'verbose_name': 'فاکتور خانه بازی',
                'verbose_name_plural': 'فاکتورهای خانه بازی',
                'db_table': 'playhouse_invoice',
                'ordering': ('-created_at',),
                'indexes': [models.Index(fields=('is_paid', 'created_at'), name='ph_inv_ispay_created_idx')],
            },
        ),
        migrations.CreateModel(
            name='PlayhouseInvoiceItem',
            fields=[
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('name', models.CharField(help_text='نام آیتم کافه', max_length=200)),
                ('price', models.DecimalField(decimal_places=0, help_text='قیمت آیتم (تومان)', max_digits=12)),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='playhouse.playhouseinvoice')),
            ],
            options={
                'verbose_name': 'آیتم فاکتور',
                'verbose_name_plural': 'آیتم‌های فاکتور',
                'db_table': 'playhouse_invoice_item',
                'ordering': ('created_at',),
            },
        ),
    ]
