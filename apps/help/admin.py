"""
Admin configuration for Help & FAQ.
"""
from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.help.models import HelpPage, FAQ


@admin.register(HelpPage)
class HelpPageAdmin(ModelAdmin):
    """Admin interface for Help Pages."""
    
    list_display = ('title', 'slug', 'lang', 'is_active', 'order', 'created_at')
    list_filter = ('lang', 'is_active')
    search_fields = ('title', 'slug', 'content_html')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('order', 'title')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'lang')
        }),
        ('Content', {
            'fields': ('content_html',),
            'description': 'HTML content for the help page'
        }),
        ('Settings', {
            'fields': ('is_active', 'order')
        }),
    )


@admin.register(FAQ)
class FAQAdmin(ModelAdmin):
    """Admin interface for FAQs."""
    
    list_display = ('question', 'lang', 'is_active', 'order', 'created_at')
    list_filter = ('lang', 'is_active')
    search_fields = ('question', 'answer')
    ordering = ('order', 'question')
    
    fieldsets = (
        ('Question', {
            'fields': ('question', 'lang')
        }),
        ('Answer', {
            'fields': ('answer',)
        }),
        ('Settings', {
            'fields': ('is_active', 'order')
        }),
    )
