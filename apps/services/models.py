"""
Service model for skills and services.
"""

from django.db import models
from django.utils.text import slugify
from apps.core.models import TimeStampedModel


class Service(TimeStampedModel):
    """Model representing a service or skill category."""
    
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    
    # Bilingual titles for UI display
    title_en = models.CharField(
        max_length=100,
        help_text="English title for service"
    )
    title_hi = models.CharField(
        max_length=100,
        blank=True,
        help_text="Hindi title for service"
    )
    
    # Category grouping
    category = models.CharField(
        max_length=50,
        blank=True,
        help_text="Category grouping (e.g., construction, home_services)"
    )
    
    description = models.TextField(blank=True)
    icon_s3_key = models.CharField(max_length=255, blank=True, help_text='S3/MinIO key for service icon')
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0, help_text='Order in which service appears in lists')
    
    class Meta:
        db_table = 'services'
        verbose_name = 'Service'
        verbose_name_plural = 'Services'
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.title_en or self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.title_en:
            self.title_en = self.name
        super().save(*args, **kwargs)
