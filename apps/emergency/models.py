"""
Emergency models - urgent help requests and dispatch tracking.
"""
from django.db import models
from django.conf import settings
from apps.core.models import BaseModel


class EmergencyRequest(BaseModel):
    """Urgent help request from user with location and service details."""
    
    # Urgency levels
    URGENCY_LOW = 'low'
    URGENCY_MEDIUM = 'medium'
    URGENCY_HIGH = 'high'
    
    URGENCY_CHOICES = [
        (URGENCY_LOW, 'Low'),
        (URGENCY_MEDIUM, 'Medium'),
        (URGENCY_HIGH, 'High'),
    ]
    
    # Status choices
    STATUS_OPEN = 'open'
    STATUS_DISPATCHED = 'dispatched'
    STATUS_ACCEPTED = 'accepted'
    STATUS_ON_THE_WAY = 'on_the_way'
    STATUS_RESOLVED = 'resolved'
    STATUS_CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_DISPATCHED, 'Dispatched'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_ON_THE_WAY, 'On The Way'),
        (STATUS_RESOLVED, 'Resolved'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]
    
    # User & Contact
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='emergency_requests',
        help_text="User who created request (can be null for anonymous)"
    )
    contact_phone = models.CharField(
        max_length=20,
        db_index=True,
        help_text="Contact phone number for emergency"
    )
    
    # Location
    site = models.ForeignKey(
        'contractors.Site',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='emergencies',
        help_text="Related construction site (optional)"
    )
    location_lat = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="Emergency location latitude"
    )
    location_lng = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="Emergency location longitude"
    )
    address_text = models.TextField(
        help_text="Human-readable address"
    )
    
    # Service Details
    service_required = models.ForeignKey(
        'services.Service',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='emergencies',
        help_text="Service type needed"
    )
    service_description = models.TextField(
        blank=True,
        help_text="Additional service details or custom description"
    )
    
    # Priority & Status
    urgency_level = models.CharField(
        max_length=10,
        choices=URGENCY_CHOICES,
        default=URGENCY_HIGH,
        db_index=True,
        help_text="Urgency level of request"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_OPEN,
        db_index=True,
        help_text="Current status of emergency"
    )
    
    # Assignment
    assigned_worker = models.ForeignKey(
        'workers.WorkerProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_emergencies',
        help_text="Worker who accepted the emergency"
    )
    assigned_contractor = models.ForeignKey(
        'contractors.ContractorProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='escalated_emergencies',
        help_text="Contractor for escalated emergencies"
    )
    
    # Metadata & Audit
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Auto-assign audit, escalation notes, dispatch info"
    )
    
    class Meta:
        db_table = 'emergency_requests'
        verbose_name = 'Emergency Request'
        verbose_name_plural = 'Emergency Requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'urgency_level'], name='emergency_status_urgency_idx'),
            models.Index(fields=['contact_phone', 'created_at'], name='emergency_phone_created_idx'),
            models.Index(fields=['location_lat', 'location_lng'], name='emergency_location_idx'),
            models.Index(fields=['created_at', 'status'], name='emergency_created_status_idx'),
        ]
    
    def __str__(self):
        return f'Emergency {self.id} - {self.contact_phone} ({self.get_status_display()})'


class EmergencyDispatchLog(BaseModel):
    """Tracks dispatch attempts to workers for emergency requests."""
    
    # Dispatch status
    STATUS_NOTIFIED = 'notified'
    STATUS_ACCEPTED = 'accepted'
    STATUS_DECLINED = 'declined'
    STATUS_TIMEOUT = 'timeout'
    
    STATUS_CHOICES = [
        (STATUS_NOTIFIED, 'Notified'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_DECLINED, 'Declined'),
        (STATUS_TIMEOUT, 'Timeout'),
    ]
    
    emergency = models.ForeignKey(
        EmergencyRequest,
        on_delete=models.CASCADE,
        related_name='dispatch_logs',
        help_text="Emergency request being dispatched"
    )
    worker = models.ForeignKey(
        'workers.WorkerProfile',
        on_delete=models.CASCADE,
        related_name='emergency_notifications',
        help_text="Worker who was notified"
    )
    attempt_time = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When notification was sent"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NOTIFIED,
        db_index=True,
        help_text="Dispatch attempt status"
    )
    response_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When worker responded (accepted/declined)"
    )
    raw_response = models.JSONField(
        default=dict,
        blank=True,
        help_text="Raw notification response data (distance, FCM response, etc.)"
    )
    
    class Meta:
        db_table = 'emergency_dispatch_logs'
        verbose_name = 'Emergency Dispatch Log'
        verbose_name_plural = 'Emergency Dispatch Logs'
        ordering = ['-attempt_time']
        indexes = [
            models.Index(fields=['emergency', 'status'], name='dispatch_emergency_status_idx'),
            models.Index(fields=['worker', 'attempt_time'], name='dispatch_worker_time_idx'),
        ]
    
    def __str__(self):
        worker_name = self.worker.user.get_full_name() or self.worker.user.phone
        return f'{worker_name} - {self.emergency.id} - {self.get_status_display()}'
