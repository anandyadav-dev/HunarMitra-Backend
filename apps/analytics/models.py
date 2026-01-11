"""
Analytics models - Event tracking and aggregation.
"""
from django.db import models
from django.conf import settings
from apps.core.models import BaseModel


class Event(BaseModel):
    """
    Analytics event tracking.
    
    Stores user actions, page views, and system events for analysis.
    Append-only for efficient write performance.
    """
    
    # Event types (recommended whitelist)
    EVENT_TYPE_PAGE_VIEW = 'page_view'
    EVENT_TYPE_BOOKING_CREATED = 'booking_created'
    EVENT_TYPE_BOOKING_STATUS = 'booking_status'
    EVENT_TYPE_JOB_APPLY = 'job_apply'
    EVENT_TYPE_EMERGENCY_REQUEST = 'emergency_request'
    EVENT_TYPE_SERVICE_SEARCH = 'service_search'
    
    EVENT_TYPES = [
        (EVENT_TYPE_PAGE_VIEW, 'Page View'),
        (EVENT_TYPE_BOOKING_CREATED, 'Booking Created'),
        (EVENT_TYPE_BOOKING_STATUS, 'Booking Status Change'),
        (EVENT_TYPE_JOB_APPLY, 'Job Application'),
        (EVENT_TYPE_EMERGENCY_REQUEST, 'Emergency Request'),
        (EVENT_TYPE_SERVICE_SEARCH, 'Service Search'),
    ]
    
    # Source platforms
    SOURCE_WEB = 'web'
    SOURCE_ANDROID = 'android'
    SOURCE_IOS = 'ios'
    SOURCE_KIOSK = 'kiosk'
    SOURCE_ADMIN = 'admin'
    
    SOURCE_CHOICES = [
        (SOURCE_WEB, 'Web'),
        (SOURCE_ANDROID, 'Android'),
        (SOURCE_IOS, 'iOS'),
        (SOURCE_KIOSK, 'Kiosk'),
        (SOURCE_ADMIN, 'Admin'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='analytics_events',
        null=True,
        blank=True,
        help_text="User if logged in"
    )
    anonymous_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text="Client-generated anonymous ID for tracking"
    )
    event_type = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Type of event"
    )
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default=SOURCE_WEB,
        db_index=True,
        help_text="Event source platform"
    )
    payload = models.JSONField(
        default=dict,
        blank=True,
        help_text="Event metadata (max 2KB)"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="Client IP address"
    )
    user_agent = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        help_text="Client user agent"
    )
    
    class Meta:
        db_table = 'analytics_events'
        verbose_name = 'Event'
        verbose_name_plural = 'Events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at'], name='analytics_created_idx'),
            models.Index(fields=['event_type', 'created_at'], name='analytics_type_created_idx'),
            models.Index(fields=['user', 'created_at'], name='analytics_user_created_idx'),
            models.Index(fields=['-created_at', 'event_type'], name='analytics_recent_type_idx'),
        ]
    
    def __str__(self):
        user_id = self.user_id or self.anonymous_id or 'unknown'
        return f'{self.event_type} by {user_id} at {self.created_at}'


class EventAggregateDaily(models.Model):
    """
    Pre-aggregated daily event counts for faster reporting.
    
    Computed by analytics_aggregate_daily management command.
    """
    
    date = models.DateField(
        db_index=True,
        help_text="Aggregation date"
    )
    event_type = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Event type"
    )
    source = models.CharField(
        max_length=20,
        blank=True,
        help_text="Source platform (optional)"
    )
    count = models.IntegerField(
        default=0,
        help_text="Number of events"
    )
    unique_users = models.IntegerField(
        default=0,
        help_text="Number of unique user IDs"
    )
    unique_anonymous = models.IntegerField(
        default=0,
        help_text="Number of unique anonymous IDs"
    )
    meta = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional aggregate metadata"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_event_aggregates_daily'
        verbose_name = 'Daily Event Aggregate'
        verbose_name_plural = 'Daily Event Aggregates'
        unique_together = [['date', 'event_type', 'source']]
        ordering = ['-date', 'event_type']
        indexes = [
            models.Index(fields=['date', 'event_type'], name='agg_date_type_idx'),
        ]
    
    def __str__(self):
        return f'{self.event_type} on {self.date}: {self.count} events'
