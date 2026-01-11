"""
Admin configuration for core app.
"""

from django.contrib import admin, messages
from django.utils.html import format_html
from django.core.cache import cache
from unfold.admin import ModelAdmin
from unfold.decorators import display, action

from apps.core.models import Banner, Theme, Translation
from apps.users.models import OTPLog


@admin.register(OTPLog)
class OTPLogAdmin(ModelAdmin):
    """ReadOnly Admin for OTP Logs."""
    list_display = ["phone", "action", "ip_address", "created_at"]
    list_filter = ["action", "created_at"]
    search_fields = ["phone", "request_id"]
    readonly_fields = [f.name for f in OTPLog._meta.fields]
    
    def has_add_permission(self, request):
        return False
        
    def has_change_permission(self, request, obj=None):
        return False
        
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Theme)
class ThemeAdmin(ModelAdmin):
    """Admin interface for Theme model with Unfold styling."""
    
    actions = ["publish_theme"]

    @action(description="Publish selected theme")
    def publish_theme(self, request, queryset):
        """Action to activate a theme and deactivate others."""
        if queryset.count() != 1:
            self.message_user(
                request, 
                "Please select exactly one theme to publish.", 
                level=messages.WARNING
            )
            return
            
        theme = queryset.first()
        theme.active = True
        theme.save()  # Signal will handle deactivation of others and cache clearing
        
        self.message_user(
            request,
            f"Theme '{theme.name}' has been published successfully.",
            level=messages.SUCCESS
        )

    list_display = [
        "name",
        "color_preview",
        "active_badge",
        "created_at",
    ]
    list_filter = ["active", "created_at"]
    list_filter_submit = True
    search_fields = ["name"]
    readonly_fields = ["created_at", "updated_at"]
    
    # Unfold-specific
    compressed_fields = True
    warn_unsaved_form = True

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": ("name", "active", "created_by"),
            },
        ),
        (
            "Colors",
            {
                "fields": ("primary_color", "accent_color", "background_color"),
                "description": "Define the color scheme for the application theme",
            },
        ),
        (
            "Branding",
            {
                "fields": ("logo_s3_key", "hero_image_s3_key", "fonts", "metadata"),
                "description": "Logo, hero image, and font configuration",
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    @display(description="Colors", label=True)
    def color_preview(self, obj):
        """Display color swatches."""
        return format_html(
            '<span style="background-color: {}; padding: 5px 15px; border-radius: 6px; color: white; margin-right: 5px;">Primary</span>'
            '<span style="background-color: {}; padding: 5px 15px; border-radius: 6px; color: white;">Accent</span>',
            obj.primary_color,
            obj.accent_color,
        )

    @display(description="Status", label={"Active": "success", "Inactive": "danger"})
    def active_badge(self, obj):
        """Display active status as badge."""
        return obj.active
    
    def save_model(self, request, obj, form, change):
        """Invalidate cache on theme save."""
        super().save_model(request, obj, form, change)
        cache.delete("theme_config_active")
        cache.delete("app_config_response")


@admin.register(Banner)
class BannerAdmin(ModelAdmin):
    """Admin interface for Banner model with Unfold styling."""

    list_display = [
        "title",
        "subtitle",
        "display_order",
        "active",
        "created_at",
    ]
    list_filter = ["active", "created_at"]
    list_filter_submit = True
    search_fields = ["title", "subtitle"]
    list_editable = ["display_order", "active"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["display_order"]
    
    # Unfold-specific
    compressed_fields = True
    warn_unsaved_form = True

    fieldsets = (
        (
            "Content",
            {
                "fields": ("title", "subtitle", "image_s3_key"),
                "description": "Banner content and image",
            },
        ),
        (
            "Behavior",
            {
                "fields": ("action", "display_order", "active"),
                "description": "Configure banner action and visibility",
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    @display(description="Status", label={"Active": "success", "Inactive": "danger"})
    def active_badge(self, obj):
        """Display active status as badge."""
        return obj.active


@admin.register(Translation)
class TranslationAdmin(ModelAdmin):
    """Admin interface for Translation model."""
    
    list_display = ["key", "lang", "value_preview", "created_at"]
    list_filter = ["lang", "created_at"]
    search_fields = ["key", "value"]
    readonly_fields = ["created_at", "updated_at"]
    
    fieldsets = (
        (
            "Translation",
            {
                "fields": ("key", "lang", "value"),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
    
    @display(description="Value")
    def value_preview(self, obj):
        """Preview of translation value."""
        return obj.value[:100] + "..." if len(obj.value) > 100 else obj.value
    
    def save_model(self, request, obj, form, change):
        """Invalidate i18n cache on save."""
        super().save_model(request, obj, form, change)
        cache.delete(f"i18n_translations_{obj.lang}")
