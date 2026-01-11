"""
Attendance app - Kiosk-based attendance tracking.
"""

from django.db import models
from django.conf import settings
from apps.core.models import BaseModel


class AttendanceKiosk(BaseModel):
    """Kiosk terminal for attendance registration."""
    
    contractor = models.ForeignKey(
        'contractors.ContractorProfile',
        on_delete=models.CASCADE,
        related_name='kiosks',
        null=True,
        blank=True,
        help_text="Contractor who owns/manages this site"
    )
    device_uuid = models.CharField(max_length=100, unique=True)
    location_name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'attendance_kiosks'
        verbose_name = 'Attendance Kiosk'
        verbose_name_plural = 'Attendance Kiosks'
    
    def __str__(self):
        return f'{self.location_name} ({self.device_uuid})'


class AttendanceLog(BaseModel):
    """Attendance check-in/check-out log."""
    
    worker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attendance_logs'
    )
    kiosk = models.ForeignKey(
        AttendanceKiosk,
        on_delete=models.PROTECT,
        related_name='logs'
    )
    check_in = models.DateTimeField(auto_now_add=True)
    check_out = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'attendance_logs'
        verbose_name = 'Attendance Log'
        verbose_name_plural = 'Attendance Logs'
        ordering = ['-check_in']
    
    def __str__(self):
        return f'{self.worker.phone} - {self.kiosk.location_name} - {self.check_in.date()}'
    
    @property
    def duration_hours(self):
        """Calculate duration in hours if checked out."""
        if self.check_out:
            delta = self.check_out - self.check_in
            return round(delta.total_seconds() / 3600, 2)
        return None


class Attendance(BaseModel):
    """
    Daily attendance record for workers.
    
    Tracks worker presence at a site for a specific date.
    Supports both stub (for testing) and biometric methods.
    """
    
    METHOD_CHOICES = [
        ('stub', 'Stub'),
        ('biometric', 'Biometric'),
    ]
    
    worker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    kiosk = models.ForeignKey(
        AttendanceKiosk,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendances',
        help_text="Kiosk/site where attendance was marked"
    )
    method = models.CharField(
        max_length=20,
        choices=METHOD_CHOICES,
        default='stub',
        help_text="Method used to mark attendance"
    )
    device_id = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="Device identifier (e.g., KIOSK_001)"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="Exact time when attendance was marked"
    )
    date = models.DateField(
        db_index=True,
        help_text="Date of attendance (derived from timestamp)"
    )
    
    class Meta:
        db_table = 'attendances'
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendances'
        ordering = ['-date', '-timestamp']
        unique_together = [['worker', 'date']]
        indexes = [
            models.Index(fields=['worker', 'date']),
            models.Index(fields=['kiosk', 'date']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f'{self.worker.phone} - {self.date} ({self.method})'
    
    def save(self, *args, **kwargs):
        """Auto-set date from timestamp if not provided."""
        if not self.date and self.timestamp:
            self.date = self.timestamp.date()
        elif not self.date:
            from django.utils import timezone
            self.date = timezone.now().date()
        super().save(*args, **kwargs)
