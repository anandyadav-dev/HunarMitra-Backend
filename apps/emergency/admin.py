"""
Admin interface for Emergency app.
"""
from django.contrib import admin
from django.utils import timezone
from unfold.admin import ModelAdmin
from .models import EmergencyRequest, EmergencyDispatchLog


@admin.register(EmergencyRequest)
class EmergencyRequestAdmin(ModelAdmin):
    """Admin for emergency requests."""
    
    list_display = [
        'id',
        'contact_phone',
        'urgency_level',
        'status',
        'assigned_worker',
        'service_required',
        'created_at'
    ]
    list_filter = ['status', 'urgency_level', 'created_at', 'service_required']
    search_fields = ['contact_phone', 'address_text', 'id']
    readonly_fields = ['created_at', 'updated_at', 'metadata']
    raw_id_fields = ['created_by', 'assigned_worker', 'assigned_contractor', 'site', 'service_required']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Contact', {
            'fields': ('created_by', 'contact_phone')
        }),
        ('Location', {
            'fields': ('site', 'location_lat', 'location_lng', 'address_text')
        }),
        ('Service Details', {
            'fields': ('service_required', 'service_description', 'urgency_level')
        }),
        ('Status & Assignment', {
            'fields': ('status', 'assigned_worker', 'assigned_contractor')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['escalate_to_contractors', 'mark_resolved']
    
    def escalate_to_contractors(self, request, queryset):
        """Escalate selected emergencies to contractors."""
        for emergency in queryset:
            emergency.metadata['escalated_at'] = timezone.now().isoformat()
            emergency.metadata['escalated_by'] = request.user.username
            emergency.metadata['escalation_reason'] = 'Manual escalation from admin'
            emergency.save(update_fields=['metadata', 'updated_at'])
        
        self.message_user(request, f'{queryset.count()} emergencies escalated to contractors')
    escalate_to_contractors.short_description = 'Escalate to contractors'
    
    def mark_resolved(self, request, queryset):
        """Mark selected emergencies as resolved."""
        updated = queryset.update(
            status=EmergencyRequest.STATUS_RESOLVED
        )
        self.message_user(request, f'{updated} emergencies marked as resolved')
    mark_resolved.short_description = 'Mark as resolved'


@admin.register(EmergencyDispatchLog)
class EmergencyDispatchLogAdmin(ModelAdmin):
    """Admin for dispatch logs."""
    
    list_display = [
        'emergency',
        'worker',
        'attempt_time',
        'status',
        'response_time'
    ]
    list_filter = ['status', 'attempt_time']
    search_fields = ['emergency__id', 'emergency__contact_phone', 'worker__user__phone']
    readonly_fields = ['attempt_time', 'created_at', 'updated_at']
    raw_id_fields = ['emergency', 'worker']
    date_hierarchy = 'attempt_time'
    
    fieldsets = (
        ('Dispatch Info', {
            'fields': ('emergency', 'worker', 'status')
        }),
        ('Timing', {
            'fields': ('attempt_time', 'response_time')
        }),
        ('Response Data', {
            'fields': ('raw_response',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
