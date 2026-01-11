from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import WorkerProfile

@admin.register(WorkerProfile)
class WorkerProfileAdmin(ModelAdmin):
    """Admin for WorkerProfile with availability tracking."""
    
    list_display = (
        'user',
        'is_available_icon',
        'availability_status',
        'rating',
        'total_jobs_completed',
        'price_amount',
        'formatted_location',
    )
    
    list_filter = ('is_available', 'availability_status', 'price_type', 'created_at')
    
    search_fields = ('user__phone', 'user__first_name', 'user__last_name')
    
    readonly_fields = ('rating', 'total_jobs_completed', 'created_at', 'updated_at', 'availability_updated_at')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Availability', {
            'fields': ('is_available', 'availability_updated_at', 'availability_status'),
            'description': 'Worker online/offline status for realtime availability'
        }),
        ('Location & Availability', {
            'fields': ('latitude', 'longitude'),
            'description': 'Location for nearby search'
        }),
        ('Pricing', {
            'fields': ('price_amount', 'price_currency', 'price_type', 'min_charge'),
            'classes': ('collapse',)
        }),
        ('Performance', {
            'fields': ('rating', 'total_jobs_completed', 'experience_years')
        }),
        ('Details', {
            'fields': ('bio', 'intro_audio_url', 'services')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_available', 'mark_unavailable']
    
    def is_available_icon(self, obj):
        """Show availability with icon."""
        if obj.is_available:
            return '🟢 Online'
        return '⚫ Offline'
    is_available_icon.short_description = 'Online Status'
    
    def formatted_location(self, obj):
        """Display location if available."""
        if obj.latitude and obj.longitude:
            return f'{obj.latitude:.4f}, {obj.longitude:.4f}'
        return '-'
    formatted_location.short_description = 'Location'
    
    def mark_available(self, request, queryset):
        """Mark selected workers as available (online)."""
        from django.utils import timezone
        updated = queryset.update(
            is_available=True,
            availability_updated_at=timezone.now()
        )
        self.message_user(request, f'{updated} workers marked as available (online).')
    mark_available.short_description = 'Set workers as available (online)'
    
    def mark_unavailable(self, request, queryset):
        """Mark selected workers as unavailable (offline)."""
        from django.utils import timezone
        updated = queryset.update(
            is_available=False,
            availability_updated_at=timezone.now()
        )
        self.message_user(request, f'{updated} workers marked as unavailable (offline).')
    mark_unavailable.short_description = 'Set workers as unavailable (offline)'
