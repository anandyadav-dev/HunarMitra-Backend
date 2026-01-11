"""
API Views for Realtime Tracking.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from apps.bookings.models import Booking
from apps.realtime import publish_event
import logging

logger = logging.getLogger(__name__)

class TrackingView(APIView):
    """
    Endpoint for workers to push live location updates.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, booking_id):
        # 1. Validate permissions
        # Only assigned worker or admin/contractor should push updates?
        # For now, simplistic: Is authenticated.
        
        booking = get_object_or_404(Booking, id=booking_id)
        
        # Ideally check if request.user == booking.worker.user
        
        lat = request.data.get('lat')
        lng = request.data.get('lng')
        timestamp = request.data.get('timestamp')
        
        if lat is None or lng is None:
             return Response({"error": "lat and lng required"}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Persist? (Optional - updating booking lat/lng snapshot)
        booking.lat = lat
        booking.lng = lng
        booking.save(update_fields=['lat', 'lng'])

        # 3. Publish to Redis
        payload = {
            "type": "location_update",
            "booking_id": str(booking.id),
            "lat": lat,
            "lng": lng,
            "timestamp": timestamp,
            "worker_id": str(booking.worker.id) if booking.worker else None
        }
        
        success = publish_event(f"booking_{booking.id}", payload)
        
        return Response({"success": success})
