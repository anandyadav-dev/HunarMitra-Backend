"""
Tests for Realtime Integration.
"""
import pytest
from unittest.mock import patch
from django.contrib.auth import get_user_model
from apps.bookings.models import Booking
from apps.services.models import Service
from rest_framework.test import APIClient
from django.urls import reverse

User = get_user_model()

@pytest.mark.django_db
class TestRealtimeIntegration:
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(phone="+919999000099", role="employer")
        self.service = Service.objects.create(name="Cleaning", slug="cleaning")
        self.booking = Booking.objects.create(
            user=self.user, 
            service=self.service, 
            status=Booking.STATUS_REQUESTED,
            address="Test"
        )

    @patch('apps.realtime.publisher.get_redis_connection')
    def test_booking_status_publishes_event(self, mock_redis):
        """Test that updating status triggers Redis publish."""
        self.client.force_authenticate(user=self.user)
        
        # Setup mock
        mock_conn = mock_redis.return_value
        
        # Verify transition
        url = reverse('booking-status', kwargs={'pk': self.booking.id})
        data = {"status": "cancelled"} # Owner can cancel
        
        response = self.client.patch(url, data)
        assert response.status_code == 200
        
        # Assert publish called
        assert mock_conn.publish.called
        args = mock_conn.publish.call_args[0]
        channel = args[0]
        assert channel == f"booking_{self.booking.id}"
        assert "booking_status" in args[1]
        assert "cancelled" in args[1]

    @patch('apps.realtime.publisher.get_redis_connection')
    def test_tracking_endpoint_publishes_event(self, mock_redis):
        """Test tracking API publishes location event."""
        self.client.force_authenticate(user=self.user)
        mock_conn = mock_redis.return_value
        
        url = reverse('tracking-update', kwargs={'booking_id': self.booking.id})
        data = {"lat": 12.34, "lng": 56.78, "timestamp": "2026-01-01T10:00:00Z"}
        
        response = self.client.post(url, data)
        assert response.status_code == 200
        
        assert mock_conn.publish.called
        args = mock_conn.publish.call_args[0]
        assert channel == f"booking_{self.booking.id}"
        assert "location_update" in args[1]
