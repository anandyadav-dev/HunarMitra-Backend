"""
Analytics admin configuration.
"""
from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Event, EventAggregateDaily


@admin.register(Event)
class EventAdmin(ModelAdmin):
    """Admin interface for analytics events."""
    
    list_display = ['id', 'event_type', 'user', 'anonymous_id', 'source', 'created_at']
    list_filter = ['event_type', 'source', 'created_at']
    search_fields = ['user__phone', 'anonymous_id', 'event_type', 'ip_address']
    readonly_fields = ['created_at', 'updated_at', 'ip_address', 'user_agent']
    date_hierarchy = 'created_at'
    raw_id_fields = ['user']
    
    fieldsets = [
        ('Event Details', {
            'fields': ['event_type', 'source', 'payload']
        }),
        ('User Information', {
            'fields': ['user', 'anonymous_id']
        }),
        ('Tracking', {
            'fields': ['ip_address', 'user_agent']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def has_add_permission(self, request):
        """Disable manual event creation in admin."""
        return False
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user')


@admin.register(EventAggregateDaily)
class EventAggregateDailyAdmin(ModelAdmin):
    """Admin interface for daily event aggregates."""
    
    list_display = ['date', 'event_type', 'source', 'count', 'unique_users', 'unique_anonymous']
    list_filter = ['date', 'event_type', 'source']
    search_fields = ['event_type']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'
    
    fieldsets = [
        ('Aggregate Details', {
            'fields': ['date', 'event_type', 'source']
        }),
        ('Counts', {
            'fields': ['count', 'unique_users', 'unique_anonymous']
        }),
        ('Metadata', {
            'fields': ['meta']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
