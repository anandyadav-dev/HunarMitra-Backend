"""
Admin interface for CMS models.
"""
from django.contrib import admin
from unfold.admin import ModelAdmin
from apps.cms.models import Banner


@admin.register(Banner)
class BannerAdmin(ModelAdmin):
    """Admin interface for promotional banners."""
    
    list_display = (
        'title', 'slot', 'priority', 'active', 
        'starts_at', 'ends_at', 'created_at'
    )
    list_filter = ('active', 'slot', 'created_at')
    search_fields = ('title',)
    list_editable = ('priority', 'active')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Banner Information', {
            'fields': ('title', 'image_url', 'link')
        }),
        ('Placement & Priority', {
            'fields': ('slot', 'priority', 'active')
        }),
        ('Scheduling', {
            'fields': ('starts_at', 'ends_at'),
            'description': 'Optional: Set start and end times for banner visibility'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset."""
        return super().get_queryset(request).select_related()
