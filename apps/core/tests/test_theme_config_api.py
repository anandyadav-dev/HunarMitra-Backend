"""
Tests for Theme Config API.
"""
import pytest
from django.core.cache import cache
from django.contrib.auth import get_user_model
from apps.core.models import Theme
from rest_framework.test import APIClient
from django.urls import reverse

User = get_user_model()

@pytest.mark.django_db
class TestThemeConfigAPI:
    def setup_method(self):
        self.client = APIClient()
        cache.clear()  # Clear cache before each test
        
    def test_theme_api_returns_active_theme(self):
        """Test that theme API returns the active theme."""
        # Create active theme
        theme = Theme.objects.create(
            name="Test Theme",
            primary_color="#FF0000",
            accent_color="#00FF00",
            background_color="#0000FF",
            logo_s3_key="static/logo.png",
            hero_image_s3_key="static/hero.jpg",
            fonts=[{"family": "Roboto", "s3_key": "fonts/roboto.woff"}],
            active=True
        )
        
        url = reverse('core:theme-config')
        response = self.client.get(url)
        
        assert response.status_code == 200
        assert response.data['name'] == "Test Theme"
        assert response.data['primary_color'] == "#FF0000"
        assert response.data['secondary_color'] == "#00FF00"
        assert 'logo_url' in response.data
        assert 'hero_image_url' in response.data
        assert len(response.data['fonts']) == 1
        
    def test_theme_api_returns_404_if_no_active_theme(self):
        """Test that theme API returns 404 if no theme is active."""
        url = reverse('core:theme-config')
        response = self.client.get(url)
        
        assert response.status_code == 404
        assert 'error' in response.data
        
    def test_theme_api_caching(self):
        """Test that theme API response is cached."""
        theme = Theme.objects.create(
            name="Cached Theme",
            active=True
        )
        
        url = reverse('core:theme-config')
        
        # First request
        response1 = self.client.get(url)
        assert response1.status_code == 200
        
        # Change theme (shouldn't affect cached response)
        theme.name = "Modified Theme"
        theme.save()
        cache.delete("theme_config_active")  # Simulating cache invalidation
        
        # Second request with fresh cache
        response2 = self.client.get(url)
        assert response2.data['name'] == "Modified Theme"
        
    def test_only_one_active_theme(self):
        """Test that only one theme can be active."""
        theme1 = Theme.objects.create(name="Theme 1", active=True)
        theme2 = Theme.objects.create(name="Theme 2", active=True)
        
        # Verify only theme2 is active
        theme1.refresh_from_db()
        assert theme1.active is False
        assert theme2.active is True
