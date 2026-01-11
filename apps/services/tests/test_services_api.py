"""
Tests for Services API.
"""
import pytest
from rest_framework.test import APIClient
from django.urls import reverse

from apps.services.models import Service


@pytest.mark.django_db
class TestServicesAPI:
    """Test services list and detail API."""
    
    def setup_method(self):
        self.client = APIClient()
        
        # Create test services
        self.service1 = Service.objects.create(
            name="Plumber",
            slug="plumber",
            title_en="Plumber",
            title_hi="प्लंबर",
            category="construction",
            description="Water supply work",
            icon_s3_key="services/icons/plumber.png",
            is_active=True,
            display_order=1
        )
        
        self.service2 = Service.objects.create(
            name="Electrician",
            slug="electrician",
            title_en="Electrician",
            title_hi="इलेक्ट्रीशियन",
            category="construction",
            description="Electrical work",
            icon_s3_key="services/icons/electrician.png",
            is_active=True,
            display_order=2
        )
        
        # Inactive service
        self.service3 = Service.objects.create(
            name="Inactive Service",
            slug="inactive",
            title_en="Inactive Service",
            title_hi="निष्क्रिय सेवा",
            is_active=False
        )
    
    def test_list_services_returns_200(self):
        """Test that GET /api/v1/services returns 200."""
        url = reverse('service-list')
        response = self.client.get(url)
        
        assert response.status_code == 200
    
    def test_list_services_returns_active_only(self):
        """Test that only active services are returned."""
        url = reverse('service-list')
        response = self.client.get(url)
        
        assert response.status_code == 200
        slugs = [s['slug'] for s in response.data]
        
        assert 'plumber' in slugs
        assert 'electrician' in slugs
        assert 'inactive' not in slugs
    
    def test_service_has_bilingual_titles(self):
        """Test that services include title_en and title_hi."""
        url = reverse('service-list')
        response = self.client.get(url)
        
        assert response.status_code == 200
        assert len(response.data) > 0
        
        service = response.data[0]
        assert 'title_en' in service
        assert 'title_hi' in service
    
    def test_service_has_icon_url(self):
        """Test that services include icon_url field."""
        url = reverse('service-list')
        response = self.client.get(url)
        
        assert response.status_code == 200
        assert len(response.data) > 0
        
        service = response.data[0]
        assert 'icon_url' in service
        
        # If icon_s3_key exists, icon_url should be a full URL
        if service['icon_url']:
            assert service['icon_url'].startswith('http')
            assert 'services/icons' in service['icon_url']
    
    def test_service_detail(self):
        """Test getting a single service by slug."""
        url = reverse('service-detail', kwargs={'slug': 'plumber'})
        response = self.client.get(url)
        
        assert response.status_code == 200
        assert response.data['slug'] == 'plumber'
        assert response.data['title_en'] == 'Plumber'
        assert response.data['title_hi'] == 'प्लंबर'
    
    def test_services_ordered_correctly(self):
        """Test that services are ordered by display_order."""
        url = reverse('service-list')
        response = self.client.get(url)
        
        assert response.status_code == 200
        slugs = [s['slug'] for s in response.data]
        
        # Plumber has display_order=1, Electrician has display_order=2
        assert slugs.index('plumber') < slugs.index('electrician')
    
    def test_service_category_present(self):
        """Test that category field is present."""
        url = reverse('service-list')
        response = self.client.get(url)
        
        assert response.status_code == 200
        service = response.data[0]
        assert 'category' in service
