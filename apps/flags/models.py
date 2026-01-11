"""
Feature flag models.
"""
from django.db import models
from apps.core.models import BaseModel


class FeatureFlag(BaseModel):
    """
    Feature Flag for toggling application features dynamically.
    
    Backend driven toggle that can be consumed by frontend.
    """
    key = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="Unique key for the feature flag (e.g., FEATURE_CSR)"
    )
    enabled = models.BooleanField(
        default=False,
        help_text="Whether this feature is globally enabled"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of what this flag controls"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'feature_flags'
        verbose_name = 'Feature Flag'
        verbose_name_plural = 'Feature Flags'
        ordering = ['key']

    def __str__(self):
        status = "ON" if self.enabled else "OFF"
        return f"{self.key} ({status})"
