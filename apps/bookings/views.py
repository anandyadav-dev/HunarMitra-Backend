"""
API Views for Booking Management.
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import Booking
from .serializers import (
    BookingCreateSerializer,
    BookingDetailSerializer,
    BookingStatusSerializer,
    BookingAssignSerializer
)
from apps.workers.models import WorkerProfile

class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for creating, retrieving, and managing bookings.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Booking.objects.all()
        
        # User sees their bookings, Workers see their assigned bookings, Contractors see... ?
        # For now simplifying: Owners and Assigned Workers
        
        qs = Booking.objects.filter(
            Q(user=user) | Q(worker__user=user)
        )
        return qs.distinct()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return BookingCreateSerializer
        return BookingDetailSerializer

    def perform_create(self, serializer):
        from django.conf import settings
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Get payment_method from request data
        payment_method = self.request.data.get('payment_method', 'cash')
        payment_note = None
        
        # Fallback logic if online payments disabled
        if payment_method == 'online' and not settings.ENABLE_PAYMENTS:
            # Auto-convert to cash with note
            payment_method = 'cash'
            payment_note = 'Online payments disabled - auto-converted to cash'
            logger.warning(
                f"Booking creation: Online payment requested but ENABLE_PAYMENTS=false, "
                f"fallback to cash. User: {self.request.user.id}"
            )
        
        # Save booking with payment details
        booking = serializer.save(
            user=self.request.user,
            payment_method=payment_method,
            payment_status='n/a' if payment_method == 'cash' else 'pending',
            payment_note=payment_note
        )
        
        # TODO: If payment_method == 'online' and ENABLE_PAYMENTS, create payment order
        # This would be implemented when payment gateway integration is added

    @action(detail=True, methods=['patch'])
    def status(self, request, pk=None):
        """
        Transition booking status.
        Uses can_transition_to logic from model.
        """
        from apps.realtime import publish_event
        
        booking = self.get_object()
        serializer = BookingStatusSerializer(data=request.data)
        
        if serializer.is_valid():
            target_status = serializer.validated_data['status']
            eta = serializer.validated_data.get('eta_minutes')
            
            # Check transition permission
            if not booking.can_transition_to(target_status, request.user):
                return Response(
                    {"error": f"Transition from {booking.status} to {target_status} not allowed for this user."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Perform transition
            booking.transition_to(target_status)
            
            # Update supplementary fields if provided
            if eta is not None:
                booking.eta_minutes = eta
                booking.save(update_fields=['eta_minutes'])
            
            # Realtime Publish
            publish_event(
                f"booking_{booking.id}",
                {
                    "type": "booking_status",
                    "id": str(booking.id),
                    "status": booking.status,
                    "eta_minutes": booking.eta_minutes,
                    "worker_id": str(booking.worker.id) if booking.worker else None,
                    "updated_at": booking.updated_at.isoformat()
                }
            )
            
            return Response(BookingDetailSerializer(booking).data)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """
        Assign a worker to the booking. 
        Only allowed for Contractors/Admins (permissions pending strictly implementation).
        """
        from apps.realtime import publish_event

        booking = self.get_object()
        
        # Simple permission check for now: Is staff or contractor
        is_authorized = request.user.is_staff or getattr(request.user, 'role', '') == 'contractor'
        if not is_authorized:
             return Response(
                {"error": "Only contractors or admins can assign workers."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        serializer = BookingAssignSerializer(data=request.data)
        if serializer.is_valid():
            worker_id = serializer.validated_data['worker_id']
            worker = get_object_or_404(WorkerProfile, id=worker_id)
            
            booking.worker = worker
            # Auto-confirm if requested?
            if booking.status == Booking.STATUS_REQUESTED:
                booking.status = Booking.STATUS_CONFIRMED
                
            booking.save()
            
            # Realtime Publish
            publish_event(
                f"booking_{booking.id}",
                {
                    "type": "booking_assigned",
                    "id": str(booking.id),
                    "status": booking.status,
                    "worker_id": str(worker.id),
                    "worker_name": worker.user.get_full_name(),
                    "updated_at": booking.updated_at.isoformat()
                }
            )

            return Response(BookingDetailSerializer(booking).data)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
