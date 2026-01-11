"""
KYC models - Registration, KycDocument, VerificationAudit.

Handles:
- Registration review workflow (pending → approved/rejected)
- KYC document upload and storage (MinIO)
- Audit trail for all registration actions
- Aadhaar last-4 encryption (privacy compliance)
"""
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from apps.core.models import BaseModel


class Registration(BaseModel):
    """
    Registration record for Worker or Contractor pending admin approval.
    
    Supports generic relationship to either WorkerProfile or ContractorProfile.
    Tracks review status, reviewer, and audit trail.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('needs_more_info', 'Needs More Information'),
    ]
    
    SOURCE_CHOICES = [
        ('web', 'Web'),
        ('mobile', 'Mobile App'),
        ('kiosk', 'Kiosk'),
    ]
    
    ROLE_CHOICES = [
        ('worker', 'Worker'),
        ('contractor', 'Contractor'),
    ]
    
    # Generic relation to Worker or Contractor profile
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={'model__in': ('workerprofile', 'contractorprofile')}
    )
    object_id = models.UUIDField()
    applicant = GenericForeignKey('content_type', 'object_id')
    
    # User reference (denormalized for quick lookups)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='kyc_registrations',
        help_text="User who submitted this registration"
    )
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        db_index=True,
        help_text="Worker or Contractor"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
        help_text="Current review status"
    )
    
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='mobile',
        help_text="Where registration was submitted from"
    )
    
    # Review tracking
    submitted_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When registration was submitted"
    )
    
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When registration was reviewed"
    )
    
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_kyc_registrations',
        help_text="Admin who reviewed this registration"
    )
    
    reviewer_notes = models.TextField(
        blank=True,
        help_text="Internal notes from reviewer"
    )
    
    # Extensible metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional registration data (city, required_docs, etc.)"
    )
    
    class Meta:
        db_table = 'kyc_registrations'
        verbose_name = 'Registration'
        verbose_name_plural = 'Registrations'
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['status', 'submitted_at'], name='kyc_reg_status_submitted_idx'),
            models.Index(fields=['role', 'status'], name='kyc_reg_role_status_idx'),
            models.Index(fields=['user', 'status'], name='kyc_reg_user_status_idx'),
        ]
    
    def __str__(self):
        user_phone = self.user.phone if self.user else 'Unknown'
        return f'{self.role.title()} Registration - {user_phone} ({self.get_status_display()})'
    
    @property
    def is_pending(self):
        """Check if registration is pending review."""
        return self.status == 'pending'
    
    @property
    def is_approved(self):
        """Check if registration is approved."""
        return self.status == 'approved'
    
    @property
    def days_pending(self):
        """Calculate days since submission."""
        if self.reviewed_at:
            delta = self.reviewed_at - self.submitted_at
        else:
            delta = timezone.now() - self.submitted_at
        return delta.days
    
    def approve(self, reviewed_by, notes=''):
        """
        Approve registration.
        
        Sets status to approved, records reviewer and timestamp.
        """
        self.status = 'approved'
        self.reviewed_by = reviewed_by
        self.reviewed_at = timezone.now()
        self.reviewer_notes = notes
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'reviewer_notes', 'updated_at'])
    
    def reject(self, reviewed_by, notes=''):
        """
        Reject registration.
        
        Sets status to rejected, records reviewer and timestamp.
        """
        self.status = 'rejected'
        self.reviewed_by = reviewed_by
        self.reviewed_at = timezone.now()
        self.reviewer_notes = notes
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'reviewer_notes', 'updated_at'])
    
    def request_more_info(self, reviewed_by, notes=''):
        """
        Request more information from applicant.
        
        Sets status to needs_more_info.
        """
        self.status = 'needs_more_info'
        self.reviewed_by = reviewed_by
        self.reviewed_at = timezone.now()
        self.reviewer_notes = notes
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'reviewer_notes', 'updated_at'])


class KycDocument(BaseModel):
    """
    Uploaded KYC document (Aadhaar, Photo, etc.) stored in MinIO.
    
    Links to Registration and stores MinIO file key for retrieval.
    Supports OCR data extraction and verification status.
    """
    
    DOC_TYPE_CHOICES = [
        ('aadhaar_front', 'Aadhaar Front'),
        ('aadhaar_back', 'Aadhaar Back'),
        ('photo', 'Photograph'),
        ('id_proof', 'ID Proof'),
        ('address_proof', 'Address Proof'),
        ('license', 'Professional License'),
        ('gst_certificate', 'GST Certificate'),
    ]
    
    # Link to registration
    registration = models.ForeignKey(
        Registration,
        on_delete=models.CASCADE,
        related_name='documents',
        null=True,
        blank=True,
        help_text="Associated registration (if part of registration flow)"
    )
    
    # Alternative: Direct relation to User for standalone uploads
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='kyc_documents',
        help_text="User who uploaded this document"
    )
    
    doc_type = models.CharField(
        max_length=20,
        choices=DOC_TYPE_CHOICES,
        db_index=True,
        help_text="Type of document"
    )
    
    file_key = models.CharField(
        max_length=500,
        unique=True,
        help_text="MinIO object key (e.g., kyc/user_123/aadhaar_front_uuid.jpg)"
    )
    
    file_size = models.IntegerField(
        help_text="File size in bytes"
    )
    
    mime_type = models.CharField(
        max_length=100,
        help_text="MIME type (e.g., image/jpeg, application/pdf)"
    )
    
    original_filename = models.CharField(
        max_length=255,
        blank=True,
        help_text="Original filename (sanitized)"
    )
    
    # OCR and verification
    ocr_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Extracted data from document (OCR results)"
    )
    
    is_verified = models.BooleanField(
        default=False,
        help_text="Whether document has been verified by admin"
    )
    
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When document was verified"
    )
    
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='verified_kyc_documents',
        help_text="Admin who verified this document"
    )
    
    class Meta:
        db_table = 'kyc_documents'
        verbose_name = 'KYC Document'
        verbose_name_plural = 'KYC Documents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['registration', 'doc_type'], name='kyc_doc_reg_type_idx'),
            models.Index(fields=['uploaded_by', 'doc_type'], name='kyc_doc_user_type_idx'),
        ]
    
    def __str__(self):
        user_info = f"User {self.uploaded_by.phone}" if self.uploaded_by else "Unknown"
        return f'{self.get_doc_type_display()} - {user_info}'
    
    @property
    def file_size_mb(self):
        """Get file size in MB."""
        return round(self.file_size / (1024 * 1024), 2)


class VerificationAudit(BaseModel):
    """
    Audit log for all registration review actions.
    
    Tracks every action taken on a registration for compliance and transparency.
    """
    
    ACTION_CHOICES = [
        ('submit', 'Submitted'),
        ('review_started', 'Review Started'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('needs_more_info', 'Needs More Info'),
        ('doc_uploaded', 'Document Uploaded'),
        ('doc_verified', 'Document Verified'),
        ('doc_deleted', 'Document Deleted'),
        ('status_changed', 'Status Changed'),
    ]
    
    registration = models.ForeignKey(
        Registration,
        on_delete=models.CASCADE,
        related_name='audits',
        help_text="Registration being audited"
    )
    
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        db_index=True,
        help_text="Action performed"
    )
    
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who performed the action"
    )
    
    comment = models.TextField(
        blank=True,
        help_text="Additional comments or notes"
    )
    
    change_payload = models.JSONField(
        default=dict,
        blank=True,
        help_text="Details of what changed (before/after values)"
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When action was performed"
    )
    
    class Meta:
        db_table = 'kyc_verification_audits'
        verbose_name = 'Verification Audit'
        verbose_name_plural = 'Verification Audits'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['registration', 'timestamp'], name='kyc_audit_reg_time_idx'),
            models.Index(fields=['action', 'timestamp'], name='kyc_audit_action_time_idx'),
        ]
    
    def __str__(self):
        actor_name = self.actor.phone if self.actor else 'System'
        return f'{self.get_action_display()} by {actor_name} on {self.registration}'
