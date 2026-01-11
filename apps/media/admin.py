"""
Admin configuration for media app.
"""
from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import MediaObject


@admin.register(MediaObject)
class MediaObjectAdmin(ModelAdmin):
    """Admin interface for MediaObject."""
    
    list_display = ['key', 'file_type', 'file_size_kb', 'uploaded_by', 'created_at']
    list_filter = ['file_type', 'created_at']
    search_fields = ['key', 'uploaded_by__phone']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('File Information', {
            'fields': ('key', 'url', 'file_type', 'file_size')
        }),
        ('Upload Info', {
            'fields': ('uploaded_by', 'created_at', 'updated_at')
        }),
    )
    
    def file_size_kb(self, obj):
        """Display file size in KB."""
        return f"{obj.file_size / 1024:.2f} KB"
    file_size_kb.short_description = "Size"
