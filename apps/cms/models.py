"""
CMS models - Promotional banners and content management.
"""
from django.db import models
from apps.core.models import BaseModel


class Banner(BaseModel):
    """
    Promotional banner model for dynamic home screen content.
    
    Supports scheduling and slot-based placement.
    """
    
    SLOT_CHOICES = [
        ('home_top', 'Home Top'),
        ('home_mid', 'Home Mid'),
        ('home_bottom', 'Home Bottom'),
        ('worker_top', 'Worker Top'),
        ('job_top', 'Job Top'),
    ]
    
    title = models.CharField(
        max_length=255,
        help_text="Banner title (internal use)"
    )
    image_url = models.URLField(
        max_length=500,
        help_text="Public URL to banner image (MinIO or CDN)"
    )
    link = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text="Optional destination URL when banner is clicked"
    )
    slot = models.CharField(
        max_length=50,
        choices=SLOT_CHOICES,
        default='home_top',
        db_index=True,
        help_text="Banner placement slot"
    )
    priority = models.IntegerField(
        default=0,
        db_index=True,
        help_text="Higher priority banners shown first"
    )
    active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this banner is currently active"
    )
    starts_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Banner becomes visible at this time (optional)"
    )
    ends_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Banner becomes hidden after this time (optional)"
    )
    
    class Meta:
        db_table = 'cms_banners'
        verbose_name = 'Banner'
        verbose_name_plural = 'Banners'
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['slot', 'active', 'priority']),
            models.Index(fields=['active', 'starts_at', 'ends_at']),
        ]
    
    def __str__(self):
        return f'{self.title} ({self.slot})'
    
    @property
    def is_visible(self):
        """Check if banner is currently visible based on schedule."""
        from django.utils import timezone
        now = timezone.now()
        
        if not self.active:
            return False
        
        if self.starts_at and now < self.starts_at:
            return False
        
        if self.ends_at and now > self.ends_at:
            return False
        
        return True
