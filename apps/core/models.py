"""
Base models for HunarMitra.
"""

import uuid
from django.db import models


class UUIDModel(models.Model):
    """Abstract base model with UUID primary key."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    """Abstract base model with timestamp fields."""
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class Theme(UUIDModel, TimeStampedModel):
    """
    Theme configuration for the application.
    Only one theme can be active at a time.
    """

    name = models.CharField(max_length=100)
    primary_color = models.CharField(max_length=7, default="#2563EB", help_text="Hex color code")
    accent_color = models.CharField(max_length=7, default="#F59E0B", help_text="Hex color code")
    background_color = models.CharField(
        max_length=7, default="#F9FAFB", help_text="Hex color code"
    )
    logo_s3_key = models.CharField(
        max_length=500, blank=True, help_text="S3/MinIO key for logo image"
    )
    hero_image_s3_key = models.CharField(
        max_length=500, blank=True, help_text="S3/MinIO key for hero/banner image"
    )
    fonts = models.JSONField(
        default=list,
        blank=True,
        help_text='Array of font objects: [{"family": "Inter", "s3_key": "fonts/inter.woff"}]',
    )
    metadata = models.JSONField(
        default=dict, blank=True, help_text="Additional theme metadata"
    )
    active = models.BooleanField(default=False, help_text="Only one theme can be active")
    created_by = models.ForeignKey(
        "users.User", on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-active", "-created_at"]

    def __str__(self):
        return f"{self.name} {'(Active)' if self.active else ''}"

    def save(self, *args, **kwargs):
        # Ensure only one active theme
        if self.active:
            Theme.objects.filter(active=True).exclude(id=self.id).update(active=False)
        super().save(*args, **kwargs)


class Banner(UUIDModel, TimeStampedModel):
    """
    Promotional banners displayed in the app.
    """

    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    image_s3_key = models.CharField(
        max_length=500, help_text="S3/MinIO key for banner image"
    )
    action = models.JSONField(
        default=dict,
        help_text='Action on tap: {"type": "url"|"route", "value": "https://..." or "/route"}',
    )
    display_order = models.IntegerField(default=0, help_text="Lower values appear first")
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "-created_at"]

    def __str__(self):
        return f"{self.title} (Order: {self.display_order})"


class BaseModel(UUIDModel, TimeStampedModel):
    """Abstract base model combining UUID and timestamps."""
    
    class Meta:
        abstract = True


class Translation(UUIDModel, TimeStampedModel):
    """
    Translation strings for i18n support.
    """
    
    LANG_CHOICES = [
        ('en', 'English'),
        ('hi', 'Hindi'),
    ]
    
    key = models.CharField(max_length=255, db_index=True, help_text="Translation key (e.g., 'apply_now')")
    lang = models.CharField(max_length=2, choices=LANG_CHOICES, help_text="Language code")
    value = models.TextField(help_text="Translated text")
    
    class Meta:
        unique_together = [['key', 'lang']]
        ordering = ['key', 'lang']
        indexes = [
            models.Index(fields=['key', 'lang']),
        ]
    
    def __str__(self):
        return f"{self.key} ({self.lang}): {self.value[:50]}"
