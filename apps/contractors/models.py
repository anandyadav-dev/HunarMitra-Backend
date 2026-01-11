"""
Contractors app - Contractor profiles and site management.
"""

from django.db import models
from django.conf import settings
from apps.core.models import BaseModel


class ContractorProfile(BaseModel):
    """Contractor profile model."""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='contractor_profile'
    )
    company_name = models.CharField(max_length=200, blank=True)
    license_number = models.CharField(max_length=100, blank=True)
    gst_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    website = models.URLField(blank=True)
    experience_years = models.IntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_projects = models.IntegerField(default=0)
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this contractor profile is active"
    )
    
    class Meta:
        db_table = 'contractor_profiles'
        verbose_name = 'Contractor Profile'
        verbose_name_plural = 'Contractor Profiles'
    
    def __str__(self):
        return f'Contractor - {self.company_name or self.user.phone}'
    
    @property
    def phone(self):
        """Get phone number from related user."""
        return self.user.phone if self.user else None


class Site(BaseModel):
    """Construction site managed by contractor."""
    
    contractor = models.ForeignKey(
        ContractorProfile,
        on_delete=models.CASCADE,
        related_name='sites',
        help_text="Contractor who owns this site"
    )
    name = models.CharField(max_length=255, help_text="Site name/identifier")
    address = models.TextField(help_text="Full site address")
    lat = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Latitude for site location"
    )
    lng = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Longitude for site location"
    )
    phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Site contact phone number"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this site is currently active"
    )
    start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Project start date"
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Expected/actual project end date"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional site metadata (JSON)"
    )
    
    class Meta:
        db_table = 'contractor_sites'
        verbose_name = 'Construction Site'
        verbose_name_plural = 'Construction Sites'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['contractor', 'is_active'], name='site_contractor_active_idx'),
            models.Index(fields=['is_active', 'created_at'], name='site_active_created_idx'),
        ]
    
    def __str__(self):
        return f'{self.name} ({self.contractor.company_name or "Contractor"})'


class SiteAssignment(BaseModel):
    """Worker assignment to construction site."""
    
    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name='assignments',
        help_text="Site where worker is assigned"
    )
    worker = models.ForeignKey(
        'workers.WorkerProfile',
        on_delete=models.CASCADE,
        related_name='site_assignments',
        help_text="Worker assigned to site"
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='site_assignments_made',
        help_text="User who made the assignment"
    )
    assigned_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When worker was assigned"
    )
    role_on_site = models.CharField(
        max_length=100,
        blank=True,
        help_text="Worker's role on this site (e.g., Mason, Plumber)"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether assignment is currently active"
    )
    
    class Meta:
        db_table = 'site_assignments'
        verbose_name = 'Site Assignment'
        verbose_name_plural = 'Site Assignments'
        unique_together = [['site', 'worker']]
        ordering = ['-assigned_at']
        indexes = [
            models.Index(fields=['site', 'is_active'], name='assignment_site_active_idx'),
            models.Index(fields=['worker', 'is_active'], name='assignment_worker_active_idx'),
        ]
    
    def __str__(self):
        worker_name = self.worker.user.get_full_name() or self.worker.user.phone
        return f'{worker_name} at {self.site.name}'


class SiteAttendance(BaseModel):
    """Daily attendance record for worker at site."""
    
    STATUS_PRESENT = 'present'
    STATUS_ABSENT = 'absent'
    STATUS_HALF_DAY = 'half_day'
    STATUS_ON_LEAVE = 'on_leave'
    
    STATUS_CHOICES = [
        (STATUS_PRESENT, 'Present'),
        (STATUS_ABSENT, 'Absent'),
        (STATUS_HALF_DAY, 'Half Day'),
        (STATUS_ON_LEAVE, 'On Leave'),
    ]
    
    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name='attendance_records',
        help_text="Site where attendance is recorded"
    )
    worker = models.ForeignKey(
        'workers.WorkerProfile',
        on_delete=models.CASCADE,
        related_name='site_attendance',
        help_text="Worker for whom attendance is recorded"
    )
    attendance_date = models.DateField(
        db_index=True,
        help_text="Date of attendance"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ABSENT,
        help_text="Attendance status"
    )
    checkin_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Time when worker checked in"
    )
    checkout_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Time when worker checked out"
    )
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='attendance_marked',
        help_text="User/device that marked attendance"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about attendance"
    )
    
    class Meta:
        db_table = 'site_attendance'
        verbose_name = 'Site Attendance'
        verbose_name_plural = 'Site Attendance Records'
        unique_together = [['site', 'worker', 'attendance_date']]
        ordering = ['-attendance_date', 'site']
        indexes = [
            models.Index(fields=['site', 'attendance_date'], name='attendance_site_date_idx'),
            models.Index(fields=['worker', 'attendance_date'], name='attendance_worker_date_idx'),
            models.Index(fields=['attendance_date', 'status'], name='attendance_date_status_idx'),
        ]
    
    def __str__(self):
        worker_name = self.worker.user.get_full_name() or self.worker.user.phone
        return f'{worker_name} - {self.site.name} - {self.attendance_date} ({self.status})'
