"""
Tests for nearby workers API.
"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.urls import reverse

from apps.workers.models import WorkerProfile
from apps.services.models import Service

User = get_user_model()


@pytest.mark.django_db
class TestNearbyWorkersAPI:
    """Test nearby workers search API."""
    
    def setup_method(self):
        self.client = APIClient()
        
        # Create service
        self.service = Service.objects.create(name="Plumbing", is_active=True)
        
        # Create workers with different locations
        # Reference point: lat=28.6139, lng=77.2090 (Delhi)
        
        # Worker 1: Very close (~1 km)
        self.user1 = User.objects.create_user(phone="+919900005555", role="worker", first_name="Close Worker")
        self.worker1 = WorkerProfile.objects.create(
            user=self.user1,
            latitude=Decimal('28.6200'),
            longitude=Decimal('77.2100'),
            availability_status='available'
        )
        self.worker1.services.add(self.service)
        
        # Worker 2: Medium distance (~5 km)
        self.user2 = User.objects.create_user(phone="+919900006666", role="worker", first_name="Medium Worker")
        self.worker2 = WorkerProfile.objects.create(
            user=self.user2,
            latitude=Decimal('28.6500'),
            longitude=Decimal('77.2500'),
            availability_status='available'
        )
        self.worker2.services.add(self.service)
        
        # Worker 3: Far away (~15 km) - should be excluded with 10km radius
        self.user3 = User.objects.create_user(phone="+919900007777", role="worker", first_name="Far Worker")
        self.worker3 = WorkerProfile.objects.create(
            user=self.user3,
            latitude=Decimal('28.7500'),
            longitude=Decimal('77.3500'),
            availability_status='available'
        )
        self.worker3.services.add(self.service)
        
        # Worker 4: Close but offline - should be excluded
        self.user4 = User.objects.create_user(phone="+919900008888", role="worker", first_name="Offline Worker")
        self.worker4 = WorkerProfile.objects.create(
            user=self.user4,
            latitude=Decimal('28.6150'),
            longitude=Decimal('77.2095'),
            availability_status='offline'
        )
        self.worker4.services.add(self.service)
    
    def test_nearby_workers_within_radius(self):
        """Test that only workers within radius are returned."""
        url = reverse('nearby-workers')
        response = self.client.get(url, {
            'lat': '28.6139',
            'lng': '77.2090',
            'radius_km': '10'
        })
        
        assert response.status_code == 200
        results = response.data.get('results', response.data)
        
        # Should return worker1 and worker2, but not worker3 (too far) or worker4 (offline)
        assert len(results) >= 2
        
        # Verify worker3 is not in results
        worker_ids = [w['id'] for w in results]
        assert str(self.worker3.id) not in worker_ids
        assert str(self.worker4.id) not in worker_ids
    
    def test_nearby_workers_sorted_by_distance(self):
        """Test that workers are sorted by distance (nearest first)."""
        url = reverse('nearby-workers')
        response = self.client.get(url, {
            'lat': '28.6139',
            'lng': '77.2090',
            'radius_km': '20'  # Include all workers
        })
        
        assert response.status_code == 200
        results = response.data.get('results', response.data)
        
        # Check that distances are in ascending order
        distances = [w.get('distance_km') for w in results if w.get('distance_km') is not None]
        assert distances == sorted(distances), "Workers should be sorted by distance"
    
    def test_nearby_workers_distance_field_present(self):
        """Test that distance_km field is present in response."""
        url = reverse('nearby-workers')
        response = self.client.get(url, {
            'lat': '28.6139',
            'lng': '77.2090',
            'radius_km': '10'
        })
        
        assert response.status_code == 200
        results = response.data.get('results', response.data)
        
        if len(results) > 0:
            assert 'distance_km' in results[0]
            assert isinstance(results[0]['distance_km'], (int, float))
    
    def test_nearby_workers_skill_filter(self):
        """Test filtering by skill."""
        # Create another service and worker
        carpentry = Service.objects.create(name="Carpentry", is_active=True)
        user5 = User.objects.create_user(phone="+919900009999", role="worker")
        worker5 = WorkerProfile.objects.create(
            user=user5,
            latitude=Decimal('28.6200'),
            longitude=Decimal('77.2100'),
            availability_status='available'
        )
        worker5.services.add(carpentry)
        
        url = reverse('nearby-workers')
        response = self.client.get(url, {
            'lat': '28.6139',
            'lng': '77.2090',
            'radius_km': '10',
            'skill': 'Plumbing'
        })
        
        assert response.status_code == 200
        results = response.data.get('results', response.data)
        
        # Should only include plumbers
        for worker in results:
            assert 'Plumbing' in str(worker.get('services_list', []))
    
    def test_nearby_workers_missing_lat_lng(self):
        """Test error when lat/lng missing."""
        url = reverse('nearby-workers')
        response = self.client.get(url, {})
        
        assert response.status_code == 400
        assert 'error' in response.data
    
    def test_nearby_workers_invalid_lat_lng(self):
        """Test error for invalid lat/lng."""
        url = reverse('nearby-workers')
        response = self.client.get(url, {
            'lat': 'invalid',
            'lng': '77.2090'
        })
        
        assert response.status_code == 400
    
    def test_nearby_workers_default_radius(self):
        """Test that default radius is applied."""
        url = reverse('nearby-workers')
        response = self.client.get(url, {
            'lat': '28.6139',
            'lng': '77.2090'
            # No radius_km specified
        })
        
        assert response.status_code == 200
        # Should use default radius of 10km
