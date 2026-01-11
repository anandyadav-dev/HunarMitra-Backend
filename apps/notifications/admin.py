"""
Admin interface for Notifications app.
"""
from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Notification, TimelineEvent, Device, OutgoingPush


@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    """Admin interface for notifications."""
    
    list_display = [
        'id', 'user', 'type', 'title', 'is_read', 'channel', 'created_at'
    ]
    list_filter = ['type', 'is_read', 'channel', 'created_at']
    search_fields = ['user__phone', 'user__email', 'title', 'message']
    readonly_fields = ['created_at', 'updated_at', 'metadata']
    
    fieldsets = (
        ('Recipient', {
            'fields': ('user',)
        }),
        ('Content', {
            'fields': ('title', 'message', 'type', 'data')
        }),
        ('Delivery', {
            'fields': ('channel', 'is_read', 'metadata')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TimelineEvent)
class TimelineEventAdmin(ModelAdmin):
    """Admin interface for timeline events."""
    
    list_display = [
        'id', 'booking', 'job', 'event_type', 'actor_display', 'created_at'
    ]
    list_filter = ['event_type', 'created_at']
    search_fields = ['booking__id', 'job__id', 'actor_display']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Relations', {
            'fields': ('booking', 'job', 'related_user')
        }),
        ('Event Details', {
            'fields': ('event_type', 'actor_display', 'payload')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Device)
class DeviceAdmin(ModelAdmin):
    """Admin interface for registered devices."""
    
    list_display = ['id', 'user', 'platform', 'is_active', 'last_seen', 'created_at']
    list_filter = ['platform', 'is_active', 'created_at']
    search_fields = ['user__phone', 'registration_token', 'id']
    readonly_fields = ['last_seen', 'created_at', 'updated_at']
    raw_id_fields = ['user']
    date_hierarchy = 'created_at'
    
    actions = ['deactivate_devices']
    
    def deactivate_devices(self, request, queryset):
        """Deactivate selected devices."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} devices deactivated')
    deactivate_devices.short_description = 'Deactivate selected devices'


@admin.register(OutgoingPush)
class OutgoingPushAdmin(ModelAdmin):
    """Admin interface for outgoing push logs."""
    
    list_display = ['id', 'notification', 'device', 'status', 'attempts', 'last_attempt_at', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['notification__title', 'device__user__phone', 'id']
    readonly_fields = ['created_at', 'updated_at', 'provider_response', 'payload']
    raw_id_fields = ['notification', 'device']
    date_hierarchy = 'created_at'
    
    actions = ['requeue_failed']
    
    def requeue_failed(self, request, queryset):
        """Requeue failed pushes for retry."""
        from apps.notifications.tasks import send_push_batch
        from apps.notifications.models import OutgoingPush
        
        failed = queryset.filter(status=OutgoingPush.STATUS_FAILED)
        push_ids = list(failed.values_list('id', flat=True))
        
        if not push_ids:
            self.message_user(request, 'No failed pushes to requeue', level='WARNING')
            return
        
        # Reset and requeue
        failed.update(status=OutgoingPush.STATUS_QUEUED, attempts=0)
        
        from django.conf import settings
        batch_size = settings.FCM_BATCH_SIZE
        for i in range(0, len(push_ids), batch_size):
            batch = push_ids[i:i+batch_size]
            send_push_batch.delay(batch)
        
        self.message_user(request, f'{len(push_ids)} pushes requeued')
    requeue_failed.short_description = 'Requeue failed pushes'
