"""
Tests for Booking State Machine and logic.
"""
import pytest
from django.contrib.auth import get_user_model
from apps.bookings.models import Booking
from apps.services.models import Service
from apps.workers.models import WorkerProfile
from rest_framework.test import APIClient
from django.urls import reverse

User = get_user_model()

@pytest.mark.django_db
class TestBookingStateMachine:
    def setup_method(self):
        self.client = APIClient()
        
        # Setup users
        self.employer = User.objects.create_user(phone="+919999000001", role="employer")
        self.contractor = User.objects.create_user(phone="+919999000002", role="contractor")
        self.worker_user = User.objects.create_user(phone="+919999000003", role="worker")
        
        # Setup worker profile
        self.worker_profile = WorkerProfile.objects.create(user=self.worker_user)
        
        # Setup service
        self.service = Service.objects.create(name="Plumbing", slug="plumbing")
        
    def test_create_booking_initial_state(self):
        """Test that new booking starts in 'requested' state."""
        booking = Booking.objects.create(
            user=self.employer,
            service=self.service,
            address="Test Address"
        )
        assert booking.status == Booking.STATUS_REQUESTED

    def test_transition_logic_requested_to_confirmed(self):
        """Test requested -> confirmed transition logic."""
        booking = Booking.objects.create(
            user=self.employer,
            service=self.service,
            address="Test Address",
            status=Booking.STATUS_REQUESTED
        )
        
        # Contractor should be able to confirm
        assert booking.can_transition_to(Booking.STATUS_CONFIRMED, self.contractor) is True
        
        # Random worker should NOT be able to confirm
        assert booking.can_transition_to(Booking.STATUS_CONFIRMED, self.worker_user) is False

    def test_transition_confirmed_to_on_the_way(self):
        """Test confirmed -> on_the_way."""
        booking = Booking.objects.create(
            user=self.employer,
            service=self.service,
            address="Test Address",
            status=Booking.STATUS_CONFIRMED,
            worker=self.worker_profile
        )
        
        # Assigned worker can start
        assert booking.can_transition_to(Booking.STATUS_ON_THE_WAY, self.worker_user) is True
        
        # Contractor can also start (override)
        assert booking.can_transition_to(Booking.STATUS_ON_THE_WAY, self.contractor) is True

    def test_cancel_flow(self):
        """Test cancellation permissions."""
        booking = Booking.objects.create(
            user=self.employer,
            service=self.service,
            address="Test Address",
            status=Booking.STATUS_REQUESTED
        )
        
        # Owner can cancel
        assert booking.can_transition_to(Booking.STATUS_CANCELLED, self.employer) is True
        
        # Contractor can cancel
        assert booking.can_transition_to(Booking.STATUS_CANCELLED, self.contractor) is True

    def test_complete_flow(self):
        booking = Booking.objects.create(
            user=self.employer,
            service=self.service,
            address="Test Address",
            status=Booking.STATUS_ARRIVED,
            worker=self.worker_profile
        )
        # Assigned Worker can complete
        assert booking.can_transition_to(Booking.STATUS_COMPLETED, self.worker_user) is True

@pytest.mark.django_db
class TestBookingAPI:
    def setup_method(self):
        self.client = APIClient()
        self.employer = User.objects.create_user(phone="+918888000001", role="employer")
        self.service = Service.objects.create(name="Electrician", slug="electrician")
        self.url = reverse('booking-list')
        
    def test_create_booking_api(self):
        self.client.force_authenticate(user=self.employer)
        data = {
            "service": self.service.id,
            "address": "123 Test Lane",
            "notes": "Urgent"
        }
        response = self.client.post(self.url, data)
        assert response.status_code == 201
        assert response.data['status'] == 'requested'
        assert response.data['address'] == "123 Test Lane"
