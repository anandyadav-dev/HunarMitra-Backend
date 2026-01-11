"""
Admin interface for Feature Flags.
"""
from django.contrib import admin
from unfold.admin import ModelAdmin
from apps.flags.models import FeatureFlag


@admin.register(FeatureFlag)
class FeatureFlagAdmin(ModelAdmin):
    """Admin interface for managing toggles."""
    
    list_display = ('key', 'enabled', 'description', 'updated_at')
    list_filter = ('enabled', 'created_at')
    search_fields = ('key', 'description')
    list_editable = ('enabled',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Feature Toggle', {
            'fields': ('key', 'enabled')
        }),
        ('Context', {
            'fields': ('description',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
