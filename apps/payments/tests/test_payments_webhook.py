"""
Tests for Payment Webhook.
"""
import pytest
from decimal import Decimal
from unittest.mock import patch
from django.contrib.auth import get_user_model
from apps.payments.models import Payment, Payout
from apps.bookings.models import Booking
from apps.services.models import Service
from apps.workers.models import WorkerProfile
from rest_framework.test import APIClient
from django.urls import reverse

User = get_user_model()

@pytest.mark.django_db
class TestPaymentWebhook:
    def setup_method(self):
        self.client = APIClient()
        
        # Create users
        self.employer = User.objects.create_user(phone="+919100001111", role="employer")
        self.worker_user = User.objects.create_user(phone="+919100002222", role="worker")
        self.worker_profile = WorkerProfile.objects.create(user=self.worker_user)
        
        # Create service
        self.service = Service.objects.create(name="Cleaning", slug="cleaning")
        
        # Create booking
        self.booking = Booking.objects.create(
            user=self.employer,
            service=self.service,
            address="Test Address",
            worker=self.worker_profile,
            status=Booking.STATUS_CONFIRMED
        )

    def test_payment_creation(self):
        """Test that payment can be created via API."""
        self.client.force_authenticate(user=self.employer)
        
        url = reverse('payment-create')
        data = {
            "booking_id": str(self.booking.id),
            "amount": "1000.00",
            "gateway": "manual"
        }
        
        response = self.client.post(url, data)
        
        assert response.status_code == 201
        assert 'payment_id' in response.data
        assert response.data['status'] == 'created'
        
        # Verify payment in DB
        payment = Payment.objects.get(id=response.data['payment_id'])
        assert payment.booking == self.booking
        assert payment.amount == Decimal('1000.00')
        assert payment.status == Payment.STATUS_CREATED

    def test_webhook_updates_payment_status(self):
        """Test that webhook updates payment status."""
        # Create payment
        payment = Payment.objects.create(
            booking=self.booking,
            amount=Decimal('1000.00'),
            gateway='manual',
            status=Payment.STATUS_CREATED
        )
        
        url = reverse('payment-webhook')
        data = {
            "payment_id": str(payment.id),
            "status": "completed",
            "gateway_reference": "mock_ref_12345"
        }
        
        response = self.client.post(url, data)
        
        assert response.status_code == 200
        
        # Verify payment updated
        payment.refresh_from_db()
        assert payment.status == 'completed'
        assert payment.gateway_reference == 'mock_ref_12345'

    def test_webhook_creates_payout_on_completion(self):
        """Test that webhook creates payout when payment completed."""
        # Create payment
        payment = Payment.objects.create(
            booking=self.booking,
            amount=Decimal('1000.00'),
            gateway='manual',
            status=Payment.STATUS_CREATED
        )
        
        url = reverse('payment-webhook')
        data = {
            "payment_id": str(payment.id),
            "status": "completed"
        }
        
        response = self.client.post(url, data)
        
        assert response.status_code == 200
        
        # Verify payout created
        payout = Payout.objects.filter(payment=payment).first()
        assert payout is not None
        assert payout.worker == self.worker_profile
        assert payout.amount == Decimal('800.00')  # 80% of 1000
        assert payout.status == Payout.STATUS_PENDING

    def test_webhook_idempotency(self):
        """Test that duplicate webhooks don't break data."""
        payment = Payment.objects.create(
            booking=self.booking,
            amount=Decimal('1000.00'),
            gateway='manual',
            status=Payment.STATUS_CREATED
        )
        
        url = reverse('payment-webhook')
        data = {
            "payment_id": str(payment.id),
            "status": "completed"
        }
        
        # First webhook
        response1 = self.client.post(url, data)
        assert response1.status_code == 200
        
        # Second identical webhook
        response2 = self.client.post(url, data)
        assert response2.status_code == 200
        
        # Verify only one payout created
        payout_count = Payout.objects.filter(payment=payment).count()
        assert payout_count == 1

    def test_non_owner_cannot_create_payment(self):
        """Test that non-booking-owner cannot create payment."""
        other_user = User.objects.create_user(phone="+919100003333", role="employer")
        self.client.force_authenticate(user=other_user)
        
        url = reverse('payment-create')
        data = {
            "booking_id": str(self.booking.id),
            "amount": "1000.00"
        }
        
        response = self.client.post(url, data)
        assert response.status_code == 403
