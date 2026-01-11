"""
Admin configuration for users app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin
from unfold.decorators import display

from apps.users.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    """Admin interface for custom User model with Unfold styling."""

    list_display = [
        "phone",
        "get_full_name",
        "role_badge",
        "ekyc_status_badge",
        "language_preference",
        "is_active_badge",
        "date_joined",
    ]
    list_filter = ["role", "ekyc_status", "is_active", "is_staff", "language_preference", "created_at"]
    list_filter_submit = True
    search_fields = ["phone", "first_name", "last_name"]
    ordering = ["-created_at"]
    readonly_fields = ["date_joined", "last_login", "aadhaar_masked_display"]
    
    # Unfold-specific
    compressed_fields = True
    warn_unsaved_form = True

    fieldsets = (
        (
            "Authentication",
            {
                "fields": ("phone", "password"),
            },
        ),
        (
            "Personal Information",
            {
                "fields": ("first_name", "last_name", "language_preference"),
            },
        ),
        (
            "eKYC Verification",
            {
                "fields": ("ekyc_status", "aadhaar_masked_display"),
                "description": "eKYC status and masked Aadhaar (only last 4 digits, encrypted)",
            },
        ),
        (
            "Role & Permissions",
            {
                "fields": ("role", "is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
            },
        ),
        (
            "Important Dates",
            {
                "fields": ("last_login", "date_joined"),
                "classes": ("collapse",),
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("phone", "password1", "password2", "role", "first_name", "last_name"),
            },
        ),
    )

    @display(description="Role", label={
        "worker": "primary",
        "contractor": "info",
        "admin": "danger",
    })
    def role_badge(self, obj):
        """Display role as a badge."""
        return obj.role


    @display(description="Status", label={"Active": "success", "Inactive": "danger"})
    def is_active_badge(self, obj):
        """Display active status as badge."""
        return obj.is_active
    
    @display(description="eKYC", label={
        "none": "secondary",
        "ocr_scanned": "warning",
        "verified": "success",
    })
    def ekyc_status_badge(self, obj):
        """Display eKYC status as badge."""
        return obj.ekyc_status
    
    @display(description="Aadhaar")
    def aadhaar_masked_display(self, obj):
        """
        Display masked Aadhaar.
        
        Security: Never shows full Aadhaar, only XXXX-1234 format.
        """
        return obj.aadhaar_last4_masked or "Not provided"
