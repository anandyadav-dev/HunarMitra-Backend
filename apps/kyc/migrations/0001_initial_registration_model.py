# Generated manually for KYC app

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Registration',
            fields=[
                ('id', models.UUIDField(default='uuid.uuid4', editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('object_id', models.UUIDField()),
                ('role', models.CharField(choices=[('worker', 'Worker'), ('contractor', 'Contractor')], db_index=True, help_text='Worker or Contractor', max_length=20)),
                ('status', models.CharField(choices=[('pending', 'Pending Review'), ('under_review', 'Under Review'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('needs_more_info', 'Needs More Information')], db_index=True, default='pending', help_text='Current review status', max_length=20)),
                ('source', models.CharField(choices=[('web', 'Web'), ('mobile', 'Mobile App'), ('kiosk', 'Kiosk')], default='mobile', help_text='Where registration was submitted from', max_length=20)),
                ('submitted_at', models.DateTimeField(auto_now_add=True, db_index=True, help_text='When registration was submitted')),
                ('reviewed_at', models.DateTimeField(blank=True, help_text='When registration was reviewed', null=True)),
                ('reviewer_notes', models.TextField(blank=True, help_text='Internal notes from reviewer')),
                ('metadata', models.JSONField(blank=True, default=dict, help_text='Additional registration data (city, required_docs, etc.)')),
                ('content_type', models.ForeignKey(limit_choices_to={'model__in': ('workerprofile', 'contractorprofile')}, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('reviewed_by', models.ForeignKey(blank=True, help_text='Admin who reviewed this registration', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_kyc_registrations', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(help_text='User who submitted this registration', on_delete=django.db.models.deletion.CASCADE, related_name='kyc_registrations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Registration',
                'verbose_name_plural': 'Registrations',
                'db_table': 'kyc_registrations',
                'ordering': ['-submitted_at'],
            },
        ),
        migrations.AddIndex(
            model_name='registration',
            index=models.Index(fields=['status', 'submitted_at'], name='kyc_reg_status_submitted_idx'),
        ),
        migrations.AddIndex(
            model_name='registration',
            index=models.Index(fields=['role', 'status'], name='kyc_reg_role_status_idx'),
        ),
        migrations.AddIndex(
            model_name='registration',
            index=models.Index(fields=['user', 'status'], name='kyc_reg_user_status_idx'),
        ),
    ]
