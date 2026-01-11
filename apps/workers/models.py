"""
Workers app - Worker profiles and availability.
"""

from django.db import models
from django.conf import settings
from apps.core.models import BaseModel


class WorkerProfile(BaseModel):
    """Worker profile with location and availability."""
    
    AVAILABILITY_CHOICES = [
        ('available', 'Available'),
        ('busy', 'Busy'),
        ('offline', 'Offline'),
    ]
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='worker_profile'
    )
    
    # Availability tracking (Uber-like online/offline status)
    is_available = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Worker is online and available for bookings"
    )
    availability_updated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time availability was toggled"
    )
    
    # Location fields (already exist, kept for nearby search)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    availability_status = models.CharField(
        max_length=20,
        choices=AVAILABILITY_CHOICES,
        default='offline'
    )
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_jobs_completed = models.IntegerField(default=0)
    services = models.ManyToManyField('services.Service', related_name='workers', blank=True)
    
    # Pricing fields
    PRICE_TYPE_CHOICES = [
        ('per_hour', 'Per Hour'),
        ('per_day', 'Per Day'),
        ('per_job', 'Per Job'),
    ]
    
    price_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Worker's rate/price"
    )
    price_currency = models.CharField(max_length=3, default='INR')
    price_type = models.CharField(
        max_length=16,
        choices=PRICE_TYPE_CHOICES,
        default='per_day',
        help_text="Pricing model (per hour/day/job)"
    )
    min_charge = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum charge for service"
    )
    
    bio = models.TextField(blank=True)
    experience_years = models.IntegerField(default=0)
    intro_audio_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text="Audio URL for worker introduction (for Listen button)"
    )
    gallery = models.ManyToManyField(
        'media.MediaObject',
        blank=True,
        related_name='worker_galleries',
        help_text="Image gallery for worker profile"
    )
    
    class Meta:
        db_table = 'worker_profiles'
        verbose_name = 'Worker Profile'
        verbose_name_plural = 'Worker Profiles'
        indexes = [
            models.Index(
                fields=['is_available', 'latitude', 'longitude'],
                name='worker_nearby_idx'
            ),
        ]
    
    def __str__(self):
        return f'Worker Profile - {self.user.phone}'
