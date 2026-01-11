"""
Booking model with state machine.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.core.models import BaseModel


class Booking(BaseModel):
    """
    Represents a service booking between an employer (user) and a worker.
    """
    
    # Status constants
    STATUS_REQUESTED = 'requested'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_ON_THE_WAY = 'on_the_way'
    STATUS_ARRIVED = 'arrived'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_PAYMENT_PENDING = 'payment_pending'

    STATUS_CHOICES = [
        (STATUS_REQUESTED, 'Requested'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_ON_THE_WAY, 'On The Way'),
        (STATUS_ARRIVED, 'Arrived'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_PAYMENT_PENDING, 'Payment Pending'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='bookings',
        on_delete=models.CASCADE,
        help_text="Employer who booked the service"
    )
    
    worker = models.ForeignKey(
        'workers.WorkerProfile',
        related_name='bookings',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Assigned worker"
    )
    
    service = models.ForeignKey(
        'services.Service',
        on_delete=models.PROTECT,
        related_name='bookings'
    )
    
    address = models.CharField(max_length=512)
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    preferred_time = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    
    estimated_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default=STATUS_REQUESTED,
        db_index=True
    )
    
    eta_minutes = models.IntegerField(null=True, blank=True, help_text="Estimated arrival time in minutes")
    tracking_url = models.URLField(null=True, blank=True, help_text="Live location tracking URL")

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"{self.service.name} - {self.status} ({self.id})"

    def can_transition_to(self, target_status, user):
        """
        Check if transition to target status is valid for the given user.
        
        Transitions:
        - requested -> confirmed (Contractor/Admin/Owner)
        - confirmed -> on_the_way (Worker/Contractor/Admin)
        - on_the_way -> arrived (Worker)
        - arrived -> completed (Worker/Contractor/Admin)
        - confirmed -> payment_pending (Contractor/Admin)
        - any -> cancelled (Owner/Contractor/Admin)
        """
        if self.status == target_status:
             return True # Idempotent

        if self.status == self.STATUS_COMPLETED:
            return False # Final state
            
        if self.status == self.STATUS_CANCELLED:
            return False # Final state

        is_admin = user.is_staff or user.is_superuser
        is_owner = user.id == self.user_id
        is_contractor = getattr(user, 'role', '') == 'contractor'
        # Assuming worker is linked to user via profile
        is_assigned_worker = False
        if self.worker and hasattr(self.worker, 'user'):
            is_assigned_worker = self.worker.user_id == user.id

        # Cancel Logic (Any non-final state -> Cancelled)
        if target_status == self.STATUS_CANCELLED:
             return is_owner or is_contractor or is_admin

        # Status specific checks
        if self.status == self.STATUS_REQUESTED:
            if target_status == self.STATUS_CONFIRMED:
                return is_contractor or is_admin or is_owner # Simplification: Owner can confirm?? Requirements say "booking owner (employer)" - treating this as valid per instruction though strict read usually implies contractor. Sticking to instructions.

        if self.status == self.STATUS_CONFIRMED:
            if target_status == self.STATUS_ON_THE_WAY:
                return is_assigned_worker or is_contractor or is_admin
            if target_status == self.STATUS_PAYMENT_PENDING:
                 return is_contractor or is_admin

        if self.status == self.STATUS_ON_THE_WAY:
             if target_status == self.STATUS_ARRIVED:
                 return is_assigned_worker # Strictly worker usually?

        if self.status == self.STATUS_ARRIVED:
             if target_status == self.STATUS_COMPLETED:
                  return is_assigned_worker or is_contractor or is_admin

        if self.status == self.STATUS_PAYMENT_PENDING:
             if target_status == self.STATUS_COMPLETED:
                  return is_contractor or is_admin # Payment Confirmed

        return False

    def transition_to(self, target_status):
        """
        Execute transition. Caller must check permission first.
        """
        self.status = target_status
        self.save()
        # Hooks for audit/notifications would go here
