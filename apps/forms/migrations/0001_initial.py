import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

import apps.forms.storage


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0001_initial'),
        ('academics', '0003_alter_classenrollment_enrollment_date_and_more'),
        ('persons', '0003_studentparent_deleted_at_studentparent_is_deleted_and_more'),
        ('workflow', '0004_alter_actionlog_options_alter_entityworkflow_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='FormSchema',
            fields=[
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('description', models.TextField(blank=True, default='')),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('fields', models.JSONField(default=list, help_text='Ordered list of FieldDefinition objects (see schema_validation).')),
                ('published_at', models.DateTimeField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('slug', models.SlugField(db_index=True, max_length=120)),
                ('title', models.CharField(max_length=200)),
                ('version', models.PositiveIntegerField(default=1)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_form_schemas', to=settings.AUTH_USER_MODEL)),
                ('workflow_definition', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='form_schemas', to='workflow.workflowdefinition')),
            ],
            options={
                'verbose_name': 'Form Schema',
                'verbose_name_plural': 'Form Schemas',
                'db_table': 'forms_schema',
                'ordering': ('slug', '-version'),
            },
        ),
        migrations.CreateModel(
            name='FormSubmission',
            fields=[
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('data', models.JSONField(blank=True, default=dict)),
                ('notes', models.TextField(blank=True, default='')),
                ('submitted_at', models.DateTimeField(blank=True, null=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('schema_version_snapshot', models.PositiveIntegerField(default=1)),
                ('version_snapshot', models.JSONField(blank=True, default=dict, help_text='Immutable copy of the schema fields at submission time.')),
                ('client_ip', models.GenericIPAddressField(blank=True, null=True)),
                ('last_action_at', models.DateTimeField(blank=True, null=True)),
                ('submission_number', models.CharField(blank=True, max_length=200, unique=True)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('submitted', 'Submitted'), ('processing', 'Processing'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('archived', 'Archived')], db_index=True, default='draft', max_length=16)),
                ('class_group', models.ForeignKey(blank=True, help_text='کلاس مرتبط — برای محدودسازی دسترسی معلم', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='form_submissions', to='academics.classgroup')),
                ('form_schema', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='submissions', to='forms.formschema')),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_form_submissions', to=settings.AUTH_USER_MODEL)),
                ('subject_person', models.ForeignKey(blank=True, help_text='شخص مرتبط (دانش‌آموز/مدرس) — برای محدودسازی دسترسی دانش‌آموز و والدین', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='subject_form_submissions', to='persons.person')),
                ('submitted_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='form_submissions', to=settings.AUTH_USER_MODEL)),
                ('workflow_instance', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='form_submissions', to='workflow.instance')),
            ],
            options={
                'verbose_name': 'Form Submission',
                'verbose_name_plural': 'Form Submissions',
                'db_table': 'forms_submission',
                'ordering': ('-created_at',),
            },
        ),
        migrations.CreateModel(
            name='FormAttachment',
            fields=[
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('checksum', models.CharField(blank=True, max_length=128)),
                ('field_key', models.CharField(max_length=100)),
                ('file', models.FileField(max_length=500, storage=apps.forms.storage.PrivateMediaStorage(), upload_to=apps.forms.storage.build_upload_path)),
                ('mime_type', models.CharField(max_length=150)),
                ('original_filename', models.CharField(max_length=255)),
                ('file_size', models.PositiveBigIntegerField()),
                ('submission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='forms.formsubmission')),
                ('uploaded_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='form_attachments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Form Attachment',
                'verbose_name_plural': 'Form Attachments',
                'db_table': 'forms_attachment',
                'ordering': ('uploaded_at',),
            },
        ),
        migrations.CreateModel(
            name='FormComment',
            fields=[
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('body', models.TextField()),
                ('is_internal', models.BooleanField(default=False)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='form_comments', to=settings.AUTH_USER_MODEL)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='forms.formcomment')),
                ('submission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='forms.formsubmission')),
            ],
            options={
                'verbose_name': 'Form Comment',
                'verbose_name_plural': 'Form Comments',
                'db_table': 'forms_comment',
                'ordering': ('created_at',),
            },
        ),
        migrations.CreateModel(
            name='SubmissionSequence',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('last_value', models.PositiveIntegerField(default=0)),
                ('slug', models.SlugField(max_length=120)),
                ('year', models.PositiveIntegerField()),
            ],
            options={
                'verbose_name': 'Submission Sequence',
                'verbose_name_plural': 'Submission Sequences',
                'db_table': 'forms_submission_sequence',
            },
        ),
        migrations.AddField(
            model_name='formschema',
            name='allowed_roles',
            field=models.ManyToManyField(blank=True, related_name='form_schemas', to='accounts.role'),
        ),
        # Explicit index names (stable, readable) instead of auto hashes.
        migrations.AddIndex(
            model_name='formschema',
            index=models.Index(fields=['slug', 'is_active'], name='forms_schema_slug_active_idx'),
        ),
        migrations.AddIndex(
            model_name='formschema',
            index=models.Index(fields=['workflow_definition'], name='forms_schema_workflow_idx'),
        ),
        migrations.AddConstraint(
            model_name='formschema',
            constraint=models.UniqueConstraint(fields=('slug', 'version'), name='uniq_forms_schema_slug_version'),
        ),
        migrations.AddConstraint(
            model_name='formschema',
            constraint=models.UniqueConstraint(condition=models.Q(('is_active', True), ('is_deleted', False)), fields=('slug',), name='uniq_forms_schema_active_per_slug'),
        ),
        migrations.AddIndex(
            model_name='formsubmission',
            index=models.Index(fields=['form_schema', 'submitted_by', 'status'], name='forms_sub_schema_user_status_idx'),
        ),
        migrations.AddIndex(
            model_name='formsubmission',
            index=models.Index(fields=['status', 'created_at'], name='forms_sub_status_created_idx'),
        ),
        migrations.AddIndex(
            model_name='formsubmission',
            index=models.Index(fields=['submitted_by', 'created_at'], name='forms_sub_user_created_idx'),
        ),
        migrations.AddIndex(
            model_name='formsubmission',
            index=models.Index(fields=['form_schema', 'created_at'], name='forms_sub_schema_created_idx'),
        ),
        migrations.AddIndex(
            model_name='formsubmission',
            index=models.Index(fields=['class_group'], name='forms_sub_class_group_idx'),
        ),
        migrations.AddIndex(
            model_name='formsubmission',
            index=models.Index(fields=['subject_person'], name='forms_sub_subject_person_idx'),
        ),
        migrations.AddIndex(
            model_name='formattachment',
            index=models.Index(fields=['submission', 'field_key'], name='forms_attach_sub_field_idx'),
        ),
        migrations.AddIndex(
            model_name='formcomment',
            index=models.Index(fields=['submission', 'created_at'], name='forms_comment_sub_created_idx'),
        ),
        migrations.AddIndex(
            model_name='submissionsequence',
            index=models.Index(fields=['slug', 'year'], name='forms_seq_slug_year_idx'),
        ),
        migrations.AddConstraint(
            model_name='submissionsequence',
            constraint=models.UniqueConstraint(fields=('slug', 'year'), name='uniq_forms_submission_sequence'),
        ),
    ]
