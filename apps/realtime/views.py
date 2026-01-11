"""
API Views for realtime tracking endpoints.
"""
import logging
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.bookings.models import Booking
from apps.notifications.models import TimelineEvent
from .serializers import TrackingUpdateSerializer
from .utils import publish_event

logger = logging.getLogger(__name__)


class BookingTrackingView(APIView):
    """
    POST /api/tracking/{booking_id}/
    
    Update worker location for a booking and publish realtime event.
    
    Rate limit: 1 request per 2 seconds (configured in settings)
    """
    
    permission_classes = [IsAuthenticated]
    throttle_scope = 'tracking'
    
    def post(self, request, booking_id):
        """
        Update booking location.
        
        Request body:
        {
            "lat": 28.6139,
            "lng": 77.2090,
            "timestamp": "2026-01-03T10:51:00Z"  // optional
        }
        """
        # Validate input
        serializer = TrackingUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get booking
        booking = get_object_or_404(Booking, id=booking_id)
        
        # Verify authorization (worker or admin)
        if not self.is_authorized(request.user, booking):
            return Response(
                {'error': 'Only assigned worker or admin can update location'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Extract validated data
        lat = serializer.validated_data['lat']
        lng = serializer.validated_data['lng']
        timestamp = serializer.validated_data.get('timestamp') or timezone.now()
        
        # Update booking location (store latest location)
        booking.last_location = {'lat': lat, 'lng': lng}
        booking.last_location_time = timestamp
        booking.save(update_fields=['last_location', 'last_location_time', 'updated_at'])
        
        # Create timeline event
        try:
            TimelineEvent.objects.create(
                booking=booking,
                event_type=TimelineEvent.EVENT_TYPE_CUSTOM,
                actor_display=f"{request.user.get_full_name() or request.user.phone}",
                related_user=request.user,
                payload={
                    'event': 'location_update',
                    'lat': lat,
                    'lng': lng,
                    'timestamp': timestamp.isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Failed to create timeline event: {e}")
        
        # Publish realtime event to WebSocket subscribers
        try:
            publish_event(
                f'booking_{booking_id}',
                {
                    'type': 'location_update',
                    'booking_id': str(booking_id),
                    'lat': lat,
                    'lng': lng,
                    'timestamp': timestamp.isoformat(),
                    'actor': request.user.get_full_name() or request.user.phone
                }
            )
        except Exception as e:
            logger.error(f"Failed to publish location event: {e}")
        
        return Response({
            'status': 'success',
            'message': 'Location updated',
            'booking_id': str(booking_id),
            'location': {
                'lat': lat,
                'lng': lng,
                'timestamp': timestamp.isoformat()
            }
        }, status=status.HTTP_200_OK)
    
    def is_authorized(self, user, booking):
        """
        Check if user is authorized to update location for this booking.
        
        Authorized users:
        - Assigned worker
        - Admin/staff
        """
        # Admin/staff always authorized
        if user.is_staff or user.is_superuser:
            return True
        
        # Check if user is assigned worker
        if booking.worker and booking.worker.user_id == user.id:
            return True
        
        # TODO: Check device token auth for kiosk devices
        
        return False
