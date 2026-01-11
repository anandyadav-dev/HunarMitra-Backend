"""
Admin configuration for Services app.
"""

from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Service


@admin.register(Service)
class ServiceAdmin(ModelAdmin):
    """Admin interface for Service model."""
    
    list_display = ('title_en', 'title_hi', 'slug', 'category', 'is_active', 'display_order', 'created_at')
    list_filter = ('is_active', 'category')
    search_fields = ('name', 'title_en', 'title_hi', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('display_order', 'name')
    
    fieldsets = (
        ('Basic Information', {'fields': ('name', 'slug', 'title_en', 'title_hi', 'category')}),
        ('Content', {'fields': ('description',)}),
        ('Media', {'fields': ('icon_s3_key',)}),
        ('Settings', {'fields': ('is_active', 'display_order')}),
    )
