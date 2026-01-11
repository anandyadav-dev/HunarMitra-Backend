"""
Jobs app - Job postings and applications.
"""

from django.db import models
from django.conf import settings
from apps.core.models import BaseModel


class Job(BaseModel):
    """Job posting model."""
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    poster = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posted_jobs'
    )
    contractor = models.ForeignKey(
        'contractors.ContractorProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='jobs',
        help_text="Contractor responsible for this job"
    )
    service = models.ForeignKey(
        'services.Service',
        on_delete=models.PROTECT,
        related_name='jobs'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    location = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    assigned_worker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_jobs'
    )
    scheduled_date = models.DateTimeField(null=True, blank=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    instruction_audio_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text="Audio URL for job instructions (for Listen button)"
    )
    photos = models.ManyToManyField(
        'media.MediaObject',
        blank=True,
        related_name='job_photos',
        help_text="Photos attached to the job"
    )
    
    class Meta:
        db_table = 'jobs'
        verbose_name = 'Job'
        verbose_name_plural = 'Jobs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.title} - {self.service.name}'


class JobApplication(BaseModel):
    """Worker application to a job."""
    
    STATUS_APPLIED = 'applied'
    STATUS_ACCEPTED = 'accepted'
    STATUS_DECLINED = 'declined'
    
    STATUS_CHOICES = [
        (STATUS_APPLIED, 'Applied'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_DECLINED, 'Declined'),
    ]
    
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    worker = models.ForeignKey(
        'workers.WorkerProfile',
        on_delete=models.CASCADE,
        related_name='job_applications'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_APPLIED
    )
    applied_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'job_applications'
        verbose_name = 'Job Application'
        verbose_name_plural = 'Job Applications'
        ordering = ['-applied_at']
        unique_together = [['job', 'worker']]
    
    def __str__(self):
        return f'{self.worker.user.get_full_name()} → {self.job.title} ({self.status})'
