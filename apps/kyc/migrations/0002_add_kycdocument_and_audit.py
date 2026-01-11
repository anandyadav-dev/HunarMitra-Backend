# Generated manually for KYC app - KycDocument and VerificationAudit models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('kyc', '0001_initial_registration_model'),
    ]

    operations = [
        migrations.CreateModel(
            name='KycDocument',
            fields=[
                ('id', models.UUIDField(default='uuid.uuid4', editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('doc_type', models.CharField(choices=[('aadhaar_front', 'Aadhaar Front'), ('aadhaar_back', 'Aadhaar Back'), ('photo', 'Photograph'), ('id_proof', 'ID Proof'), ('address_proof', 'Address Proof'), ('license', 'Professional License'), ('gst_certificate', 'GST Certificate')], db_index=True, help_text='Type of document', max_length=20)),
                ('file_key', models.CharField(help_text='MinIO object key (e.g., kyc/user_123/aadhaar_front_uuid.jpg)', max_length=500, unique=True)),
                ('file_size', models.IntegerField(help_text='File size in bytes')),
                ('mime_type', models.CharField(help_text='MIME type (e.g., image/jpeg, application/pdf)', max_length=100)),
                ('original_filename', models.CharField(blank=True, help_text='Original filename (sanitized)', max_length=255)),
                ('ocr_data', models.JSONField(blank=True, default=dict, help_text='Extracted data from document (OCR results)')),
                ('is_verified', models.BooleanField(default=False, help_text='Whether document has been verified by admin')),
                ('verified_at', models.DateTimeField(blank=True, help_text='When document was verified', null=True)),
                ('registration', models.ForeignKey(blank=True, help_text='Associated registration (if part of registration flow)', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='kyc.registration')),
                ('uploaded_by', models.ForeignKey(help_text='User who uploaded this document', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='kyc_documents', to=settings.AUTH_USER_MODEL)),
                ('verified_by', models.ForeignKey(blank=True, help_text='Admin who verified this document', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='verified_kyc_documents', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'KYC Document',
                'verbose_name_plural': 'KYC Documents',
                'db_table': 'kyc_documents',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='VerificationAudit',
            fields=[
                ('id', models.UUIDField(default='uuid.uuid4', editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('action', models.CharField(choices=[('submit', 'Submitted'), ('review_started', 'Review Started'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('needs_more_info', 'Needs More Info'), ('doc_uploaded', 'Document Uploaded'), ('doc_verified', 'Document Verified'), ('doc_deleted', 'Document Deleted'), ('status_changed', 'Status Changed')], db_index=True, help_text='Action performed', max_length=20)),
                ('comment', models.TextField(blank=True, help_text='Additional comments or notes')),
                ('change_payload', models.JSONField(blank=True, default=dict, help_text='Details of what changed (before/after values)')),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True, help_text='When action was performed')),
                ('actor', models.ForeignKey(blank=True, help_text='User who performed the action', null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('registration', models.ForeignKey(help_text='Registration being audited', on_delete=django.db.models.deletion.CASCADE, related_name='audits', to='kyc.registration')),
            ],
            options={
                'verbose_name': 'Verification Audit',
                'verbose_name_plural': 'Verification Audits',
                'db_table': 'kyc_verification_audits',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='kycdocument',
            index=models.Index(fields=['registration', 'doc_type'], name='kyc_doc_reg_type_idx'),
        ),
        migrations.AddIndex(
            model_name='kycdocument',
            index=models.Index(fields=['uploaded_by', 'doc_type'], name='kyc_doc_user_type_idx'),
        ),
        migrations.AddIndex(
            model_name='verificationaudit',
            index=models.Index(fields=['registration', 'timestamp'], name='kyc_audit_reg_time_idx'),
        ),
        migrations.AddIndex(
            model_name='verificationaudit',
            index=models.Index(fields=['action', 'timestamp'], name='kyc_audit_action_time_idx'),
        ),
    ]
