"""
Tests for cash-first payment system.
"""
import pytest
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status as http_status

from apps.bookings.models import Booking
from apps.payments.models import Payment
from apps.users.models import User
from apps.workers.models import WorkerProfile
from apps.services.models import Service, ServiceCategory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def employer_user(db):
    return User.objects.create_user(
        phone="+919999900001",
        password="password",
        role="employer",
        first_name="Test",
        last_name="Employer"
    )


@pytest.fixture
def worker_user(db):
    user = User.objects.create_user(
        phone="+919999900002",
        password="password",
        role="worker",
        first_name="Test",
        last_name="Worker"
    )
    WorkerProfile.objects.create(
        user=user,
        skill="Plumber",
        experience_years=5,
        price_per_hour=500.0
    )
    return user


@pytest.fixture
def service(db):
    category = ServiceCategory.objects.create(name="Plumbing")
    return Service.objects.create(
        name="Tap Repair",
        category=category,
        base_price=300.0
    )


@pytest.mark.django_db
class TestCashPaymentBooking:
    """Test booking with cash payment method."""
    
    def test_create_booking_cash_default(self, api_client, employer_user, service):
        """Test that bookings default to cash when payment_method not specified."""
        api_client.force_authenticate(user=employer_user)
        
        url = reverse('booking-list')
        data = {
            'service': service.id,
            'address': '123 Main St',
            'lat': 28.6,
            'lng': 77.2
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == http_status.HTTP_201_CREATED
        assert response.data['payment_method'] == 'cash'
        assert response.data['status'] == 'requested'
        
        # Verify booking in DB
        booking = Booking.objects.get(id=response.data['id'])
        assert booking.payment_method == 'cash'
        assert booking.payment_status == 'n/a'
        
        # Verify no Payment record created
        assert Payment.objects.filter(booking=booking).count() == 0
    
    def test_create_booking_cash_explicit(self, api_client, employer_user, service):
        """Test creating booking with explicit cash payment method."""
        api_client.force_authenticate(user=employer_user)
        
        url = reverse('booking-list')
        data = {
            'service': service.id,
            'address': '123 Main St',
            'payment_method': 'cash'
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == http_status.HTTP_201_CREATED
        assert response.data['payment_method'] == 'cash'
        
        booking = Booking.objects.get(id=response.data['id'])
        assert booking.payment_status == 'n/a'
        assert booking.payment_note is None or booking.payment_note == ''


@pytest.mark.django_db
class TestOnlinePaymentWhenDisabled:
    """Test online payment handling when ENABLE_PAYMENTS=false."""
    
    @override_settings(ENABLE_PAYMENTS=False)
    def test_online_payment_fallback_to_cash(self, api_client, employer_user, service):
        """Test that online payment request falls back to cash when disabled."""
        api_client.force_authenticate(user=employer_user)
        
        url = reverse('booking-list')
        data = {
            'service': service.id,
            'address': '123 Main St',
            'payment_method': 'online'  # Request online payment
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == http_status.HTTP_201_CREATED
        # Should fallback to cash
        assert response.data['payment_method'] == 'cash'
        
        booking = Booking.objects.get(id=response.data['id'])
        assert booking.payment_method == 'cash'
        assert booking.payment_status == 'n/a'
        assert 'auto-converted' in booking.payment_note.lower()
        
        # Verify no Payment order created
        assert Payment.objects.filter(booking=booking).count() == 0


@pytest.mark.django_db
class TestOnlinePaymentWhenEnabled:
    """Test online payment handling when ENABLE_PAYMENTS=true."""
    
    @override_settings(ENABLE_PAYMENTS=True)
    def test_online_payment_accepted(self, api_client, employer_user, service):
        """Test that online payment is accepted when enabled."""
        api_client.force_authenticate(user=employer_user)
        
        url = reverse('booking-list')
        data = {
            'service': service.id,
            'address': '123 Main St',
            'payment_method': 'online'
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == http_status.HTTP_201_CREATED
        assert response.data['payment_method'] == 'online'
        
        booking = Booking.objects.get(id=response.data['id'])
        assert booking.payment_method == 'online'
        assert booking.payment_status == 'pending'
        
        # Note: Payment order creation would be tested separately
        # when payment gateway integration is implemented


@pytest.mark.django_db
class TestPaymentEndpointsGated:
    """Test that payment endpoints respect ENABLE_PAYMENTS flag."""
    
    @override_settings(ENABLE_PAYMENTS=False)
    def test_payment_creation_disabled(self, api_client, employer_user, service):
        """Test payment order creation returns 503 when disabled."""
        # First create a booking
        api_client.force_authenticate(user=employer_user)
        booking = Booking.objects.create(
            user=employer_user,
            service=service,
            address='Test',
            status='requested',
            payment_method='cash'
        )
        
        # Try to create payment
        url = reverse('payment-create')
        data = {
            'booking_id': str(booking.id),
            'amount': 500.0
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == http_status.HTTP_503_SERVICE_UNAVAILABLE
        assert 'disabled' in response.data['detail'].lower()
        assert Payment.objects.count() == 0
    
    @override_settings(ENABLE_PAYMENTS=False)
    def test_payment_webhook_noop_when_disabled(self, api_client):
        """Test webhook returns 200 but doesn't process when disabled."""
        url = reverse('payment-webhook')
        data = {
            'payment_id': 'some-id',
            'status': 'completed',
            'gateway_reference': 'ref123'
        }
        
        response = api_client.post(url, data)
        
        # Should acknowledge but not process
        assert response.status_code == http_status.HTTP_200_OK
        assert 'acknowledged' in response.data['message'].lower()
    
    @override_settings(ENABLE_PAYMENTS=True)
    def test_payment_creation_enabled(self, api_client, employer_user, service):
        """Test payment order creation works when enabled."""
        api_client.force_authenticate(user=employer_user)
        
        booking = Booking.objects.create(
            user=employer_user,
            service=service,
            address='Test',
            status='requested',
            payment_method='online',
            payment_status='pending'
        )
        
        url = reverse('payment-create')
        data = {
            'booking_id': str(booking.id),
            'amount': 500.0
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == http_status.HTTP_201_CREATED
        assert 'payment_id' in response.data
        assert Payment.objects.count() == 1
