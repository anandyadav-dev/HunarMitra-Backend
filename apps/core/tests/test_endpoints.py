"""
Tests for core app endpoints.
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_check(self):
        """Test that health check endpoint returns 200."""
        client = APIClient()
        url = reverse('core:health')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'ok'


@pytest.mark.django_db
class TestThemeEndpoint:
    """Tests for theme endpoint."""
    
    def test_theme_endpoint(self):
        """Test that theme endpoint returns valid configuration."""
        client = APIClient()
        url = reverse('core:theme')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'colors' in response.data
        assert 'logo_url' in response.data
        assert 'fonts' in response.data
        assert 'feature_flags' in response.data
        assert isinstance(response.data['feature_flags'], dict)
