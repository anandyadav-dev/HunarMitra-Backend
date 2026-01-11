"""
Notifications app - Enhanced notification management with timeline events.
"""

from django.db import models
from django.conf import settings
from apps.core.models import BaseModel


class Notification(BaseModel):
    """
    Notification model for push notifications and in-app messages.
    """
    
    # Recipient (null for broadcast)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True,
        help_text="Recipient (null for broadcast notifications)"
    )
    
    # Content
    title = models.CharField(max_length=255)
    message = models.TextField()
    data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional payload (booking_id, type, etc.)"
    )
    
    # Classification
    TYPE_BOOKING_STATUS = 'booking_status'
    TYPE_JOB_APPLICATION = 'job_application'
    TYPE_ASSIGNMENT = 'assignment'
    TYPE_ATTENDANCE = 'attendance'
    TYPE_SYSTEM = 'system'
    TYPE_PROMO = 'promo'
    
    TYPE_CHOICES = [
        (TYPE_BOOKING_STATUS, 'Booking Status'),
        (TYPE_JOB_APPLICATION, 'Job Application'),
        (TYPE_ASSIGNMENT, 'Assignment'),
        (TYPE_ATTENDANCE, 'Attendance'),
        (TYPE_SYSTEM, 'System'),
        (TYPE_PROMO, 'Promo'),
    ]
    
    type = models.CharField(
        max_length=32,
        choices=TYPE_CHOICES,
        db_index=True,
        default=TYPE_SYSTEM
    )
    
    # State
    is_read = models.BooleanField(default=False, db_index=True)
    
    # Delivery channel
    CHANNEL_PUSH = 'push'
    CHANNEL_IN_APP = 'in_app'
    CHANNEL_EMAIL = 'email'
    
    CHANNEL_CHOICES = [
        (CHANNEL_PUSH, 'Push Notification'),
        (CHANNEL_IN_APP, 'In-App'),
        (CHANNEL_EMAIL, 'Email'),
    ]
    
    channel = models.CharField(
        max_length=16,
        choices=CHANNEL_CHOICES,
        default=CHANNEL_IN_APP
    )
    
    # Metadata for delivery tracking (FCM responses, etc.)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
            models.Index(fields=['type', '-created_at']),
        ]
    
    def __str__(self):
        recipient = self.user.phone if self.user else 'Broadcast'
        return f'{self.title} - {recipient}'


class TimelineEvent(BaseModel):
    """
    Timeline event model for tracking booking/job activity history.
    """
    
    # Relations
    booking = models.ForeignKey(
        'bookings.Booking',
        on_delete=models.CASCADE,
        related_name='timeline_events',
        null=True,
        blank=True,
        help_text="Related booking"
    )
    
    job = models.ForeignKey(
        'jobs.Job',
        on_delete=models.CASCADE,
        related_name='timeline_events',
        null=True,
        blank=True,
        help_text="Related job"
    )
    
    related_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who triggered this event"
    )
    
    # Event details
    EVENT_TYPE_BOOKING_REQUESTED = 'booking_requested'
    EVENT_TYPE_BOOKING_CONFIRMED = 'booking_confirmed'
    EVENT_TYPE_BOOKING_ON_THE_WAY = 'booking_on_the_way'
    EVENT_TYPE_BOOKING_ARRIVED = 'booking_arrived'
    EVENT_TYPE_BOOKING_COMPLETED = 'booking_completed'
    EVENT_TYPE_BOOKING_CANCELLED = 'booking_cancelled'
    EVENT_TYPE_JOB_APPLIED = 'job_applied'
    EVENT_TYPE_JOB_ACCEPTED = 'job_accepted'
    EVENT_TYPE_WORKER_ASSIGNED = 'worker_assigned'
    EVENT_TYPE_ATTENDANCE_MARKED = 'attendance_marked'
    EVENT_TYPE_PAYMENT_CAPTURED = 'payment_captured'
    EVENT_TYPE_PAYMENT_FAILED = 'payment_failed'
    EVENT_TYPE_CUSTOM = 'custom'
    
    EVENT_TYPE_CHOICES = [
        (EVENT_TYPE_BOOKING_REQUESTED, 'Booking Requested'),
        (EVENT_TYPE_BOOKING_CONFIRMED, 'Booking Confirmed'),
        (EVENT_TYPE_BOOKING_ON_THE_WAY, 'On The Way'),
        (EVENT_TYPE_BOOKING_ARRIVED, 'Arrived'),
        (EVENT_TYPE_BOOKING_COMPLETED, 'Completed'),
        (EVENT_TYPE_BOOKING_CANCELLED, 'Cancelled'),
        (EVENT_TYPE_JOB_APPLIED, 'Job Applied'),
        (EVENT_TYPE_JOB_ACCEPTED, 'Job Accepted'),
        (EVENT_TYPE_WORKER_ASSIGNED, 'Worker Assigned'),
        (EVENT_TYPE_ATTENDANCE_MARKED, 'Attendance Marked'),
        (EVENT_TYPE_PAYMENT_CAPTURED, 'Payment Captured'),
        (EVENT_TYPE_PAYMENT_FAILED, 'Payment Failed'),
        (EVENT_TYPE_CUSTOM, 'Custom'),
    ]
    
    event_type = models.CharField(
        max_length=32,
        choices=EVENT_TYPE_CHOICES,
        db_index=True
    )
    
    actor_display = models.CharField(
        max_length=255,
        help_text="Human-readable actor name (e.g., 'John Doe', 'System')"
    )
    
    payload = models.JSONField(
        default=dict,
        blank=True,
        help_text="Event-specific data (status, worker_id, etc.)"
    )
    
    class Meta:
        db_table = 'timeline_events'
        verbose_name = 'Timeline Event'
        verbose_name_plural = 'Timeline Events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking', '-created_at']),
            models.Index(fields=['job', '-created_at']),
            models.Index(fields=['event_type', '-created_at']),
        ]
    
    def __str__(self):
        return f'{self.get_event_type_display()} by {self.actor_display} at {self.created_at}'


class Device(BaseModel):
    """Mobile/web device registered for push notifications."""
    
    # Platform choices
    PLATFORM_ANDROID = 'android'
    PLATFORM_IOS = 'ios'
    PLATFORM_WEB = 'web'
    
    PLATFORM_CHOICES = [
        (PLATFORM_ANDROID, 'Android'),
        (PLATFORM_IOS, 'iOS'),
        (PLATFORM_WEB, 'Web'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='devices',
        null=True,
        blank=True,
        help_text="User associated with device (null if unregistered)"
    )
    platform = models.CharField(
        max_length=10,
        choices=PLATFORM_CHOICES,
        help_text="Device platform"
    )
    registration_token = models.CharField(
        max_length=500,
        unique=True,
        db_index=True,
        help_text="FCM registration token"
    )
    last_seen = models.DateTimeField(
        auto_now=True,
        help_text="Last time device checked in"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether device is active"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Device info: model, OS version, app version"
    )
    
    class Meta:
        db_table = 'notification_devices'
        verbose_name = 'Device'
        verbose_name_plural = 'Devices'
        ordering = ['-last_seen']
        indexes = [
            models.Index(fields=['user', 'is_active'], name='device_user_active_idx'),
        ]
    
    def __str__(self):
        user_display = self.user.phone if self.user else 'Anonymous'
        return f'{user_display} - {self.get_platform_display()}'


class OutgoingPush(BaseModel):
    """Log of push notification delivery attempts."""
    
    # Status choices
    STATUS_QUEUED = 'queued'
    STATUS_SENT = 'sent'
    STATUS_FAILED = 'failed'
    STATUS_DELAYED = 'delayed'
    
    STATUS_CHOICES = [
        (STATUS_QUEUED, 'Queued'),
        (STATUS_SENT, 'Sent'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_DELAYED, 'Delayed'),
    ]
    
    notification = models.ForeignKey(
        Notification,
        on_delete=models.SET_NULL,
        related_name='outgoing_pushes',
        null=True,
        blank=True,
        help_text="Source notification"
    )
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='outgoing_pushes',
        null=True,
        blank=True,
        help_text="Target device"
    )
    payload = models.JSONField(
        default=dict,
        help_text="FCM payload sent"
    )
    provider_response = models.JSONField(
        default=dict,
        blank=True,
        help_text="FCM response data"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_QUEUED,
        db_index=True,
        help_text="Delivery status"
    )
    attempts = models.IntegerField(
        default=0,
        help_text="Number of delivery attempts"
    )
    last_attempt_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last delivery attempt timestamp"
    )
    
    class Meta:
        db_table = 'notification_outgoing_pushes'
        verbose_name = 'Outgoing Push'
        verbose_name_plural = 'Outgoing Pushes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at'], name='push_status_created_idx'),
            models.Index(fields=['device', 'status'], name='push_device_status_idx'),
        ]
    
    def __str__(self):
        return f'Push {self.id} - {self.get_status_display()} ({self.attempts} attempts)'
