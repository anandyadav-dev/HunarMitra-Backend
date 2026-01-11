"""
Media models for file/image storage tracking.
"""
from django.db import models
from django.conf import settings
from apps.core.models import BaseModel


class MediaObject(BaseModel):
    """
    Tracks uploaded media files (images, audio, etc.) stored in MinIO.
    
    Stores only metadata and URLs, not the actual file content.
    """
    
    FILE_TYPE_CHOICES = [
        ('image/jpeg', 'JPEG Image'),
        ('image/png', 'PNG Image'),
        ('image/webp', 'WebP Image'),
        ('audio/mpeg', 'MP3 Audio'),
        ('audio/wav', 'WAV Audio'),
    ]
    
    key = models.CharField(
        max_length=255,
        unique=True,
        help_text="MinIO object key (path in storage)"
    )
    url = models.URLField(
        max_length=500,
        help_text="Public URL to access the media"
    )
    file_type = models.CharField(
        max_length=32,
        choices=FILE_TYPE_CHOICES,
        help_text="MIME type of the file"
    )
    file_size = models.IntegerField(
        help_text="File size in bytes"
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_media'
    )
    
    class Meta:
        db_table = 'media_objects'
        verbose_name = 'Media Object'
        verbose_name_plural = 'Media Objects'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['uploaded_by', '-created_at']),
            models.Index(fields=['file_type']),
        ]
    
    def __str__(self):
        return f"{self.file_type} - {self.key}"
