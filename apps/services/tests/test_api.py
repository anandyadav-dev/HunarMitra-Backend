"""
Tests for services app.
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.services.models import Service


@pytest.mark.django_db
class TestServicesAPI:
    """Tests for services list API."""
    
    @pytest.fixture
    def sample_services(self):
        """Create sample services for testing."""
        services = [
            Service.objects.create(name='Plumbing', description='Pipe fitting', is_active=True),
            Service.objects.create(name='Electrical', description='Wiring', is_active=True),
            Service.objects.create(name='Carpentry', description='Woodwork', is_active=False),
        ]
        return services
    
    def test_services_list(self, sample_services):
        """Test that services list endpoint returns only active services."""
        client = APIClient()
        url = reverse('services:service-list')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2  # Only active services
        
        service_names = [s['name'] for s in response.data]
        assert 'Plumbing' in service_names
        assert 'Electrical' in service_names
        assert 'Carpentry' not in service_names  # Inactive
    
    def test_service_detail(self, sample_services):
        """Test service detail endpoint."""
        client = APIClient()
        service = sample_services[0]
        url = reverse('services:service-detail', kwargs={'slug': service.slug})
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == service.name
        assert response.data['slug'] == service.slug
