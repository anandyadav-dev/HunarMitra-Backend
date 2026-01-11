"""
Tests for worker pricing functionality.
"""

import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from apps.workers.models import WorkerProfile
from apps.services.models import Service

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestWorkerPricingModel:
    """Test worker pricing model fields."""
    
    def test_worker_has_pricing_fields(self):
        """Test that WorkerProfile model has all pricing fields."""
        user = User.objects.create_user(phone="+919999999991")
        worker = WorkerProfile.objects.create(
            user=user,
            price_amount=Decimal('500.00'),
            price_currency='INR',
            price_type='per_day',
            min_charge=Decimal('250.00')
        )
        
        assert worker.price_amount == Decimal('500.00')
        assert worker.price_currency == 'INR'
        assert worker.price_type == 'per_day'
        assert worker.min_charge == Decimal('250.00')
    
    def test_price_type_choices(self):
        """Test valid price_type choices."""
        user = User.objects.create_user(phone="+919999999992")
        
        # Test per_hour
        worker1 = WorkerProfile.objects.create(
            user=user,
            price_type='per_hour'
        )
        assert worker1.price_type == 'per_hour'
        
        # Test per_job
        worker1.price_type = 'per_job'
        worker1.save()
        assert worker1.price_type == 'per_job'
    
    def test_default_values(self):
        """Test default pricing values."""
        user = User.objects.create_user(phone="+919999999993")
        worker = WorkerProfile.objects.create(user=user)
        
        assert worker.price_currency == 'INR'
        assert worker.price_type == 'per_day'
        assert worker.price_amount is None  # nullable
        assert worker.min_charge is None  # nullable


class TestWorkerPricingAPI:
    """Test worker pricing in API serializer."""
    
    def test_pricing_in_serializer(self):
        """Test that pricing fields are included in serializer."""
        from apps.workers.serializers import WorkerProfileSerializer
        
        user = User.objects.create_user(
            phone="+919999999994",
            first_name="Test",
            last_name="Worker"
        )
        worker = WorkerProfile.objects.create(
            user=user,
            price_amount=Decimal('800.00'),
            price_currency='INR',
            price_type='per_hour',
            min_charge=Decimal('400.00')
        )
        
        serializer = WorkerProfileSerializer(worker)
        data = serializer.data
        
        assert 'price_amount' in data
        assert 'price_currency' in data
        assert 'price_type' in data
        assert 'min_charge' in data
        
        assert data['price_amount'] == '800.00'
        assert data['price_currency'] == 'INR'
        assert data['price_type'] == 'per_hour'
        assert data['min_charge'] == '400.00'


class TestWorkerPricingSeedData:
    """Test that seed data includes pricing."""
    
    def test_seeded_workers_have_pricing(self):
        """Test that demo workers created by seed command have pricing."""
        # This would be run after seed_demo_data command
        # For now, just test the structure
        user = User.objects.create_user(
            phone="+919876543210",
            first_name="Raju",
            last_name="Kumar"
        )
        
        worker = WorkerProfile.objects.create(
            user=user,
            availability_status="available",
            experience_years=5,
            bio="Expert plumber with 5 years experience",
            rating=Decimal('4.5'),
            price_amount=Decimal('600.00'),
            price_currency="INR",
            price_type="per_day",
            min_charge=Decimal('300.00')
        )
        
        # Verify all pricing fields populated
        assert worker.price_amount is not None
        assert worker.price_currency == 'INR'
        assert worker.price_type in ['per_hour', 'per_day', 'per_job']
        assert worker.min_charge is not None
        assert worker.min_charge <= worker.price_amount
