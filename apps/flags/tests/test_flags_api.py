"""
Tests for Feature Flags API.
"""
import pytest
from django.core.cache import cache
from rest_framework.test import APIClient
from django.urls import reverse

from apps.flags.models import FeatureFlag
from apps.flags.signals import CACHE_KEY


@pytest.mark.django_db
class TestFeatureFlagsAPI:
    """Test feature flags API and caching."""
    
    def setup_method(self):
        self.client = APIClient()
        self.url = reverse('feature-flags')
        
        # Clear cache before each test
        cache.delete(CACHE_KEY)
        
        # Create test flags
        FeatureFlag.objects.create(key='FEATURE_A', enabled=True)
        FeatureFlag.objects.create(key='FEATURE_B', enabled=False)
    
    def test_api_returns_key_value_map(self):
        """Test API returns simple key-value JSON object."""
        response = self.client.get(self.url)
        
        assert response.status_code == 200
        assert isinstance(response.data, dict)
        assert response.data['FEATURE_A'] is True
        assert response.data['FEATURE_B'] is False
    
    def test_response_is_cached(self):
        """Test that response is cached."""
        # First request (DB hit)
        with self.assertNumQueries(1):
            self.client.get(self.url)
            
        # Verify cache is set
        assert cache.get(CACHE_KEY) is not None
        
        # Second request (Cache hit - 0 DB queries)
        with self.assertNumQueries(0):
            self.client.get(self.url)
            
    def test_admin_update_invalidates_cache(self):
        """Test that updating a flag clears the cache."""
        # Populate cache
        self.client.get(self.url)
        assert cache.get(CACHE_KEY) is not None
        
        # Update flag via ORM (triggers signal)
        flag = FeatureFlag.objects.get(key='FEATURE_A')
        flag.enabled = False
        flag.save()
        
        # Verify cache is cleared
        assert cache.get(CACHE_KEY) is None
        
        # Verify API returns updated value
        response = self.client.get(self.url)
        assert response.data['FEATURE_A'] is False
        
    def test_admin_delete_invalidates_cache(self):
        """Test that deleting a flag clears the cache."""
        # Populate cache
        self.client.get(self.url)
        assert cache.get(CACHE_KEY) is not None
        
        # Delete flag
        FeatureFlag.objects.get(key='FEATURE_A').delete()
        
        # Verify cache is cleared
        assert cache.get(CACHE_KEY) is None
        
        # Verify API reflects deletion
        response = self.client.get(self.url)
        assert 'FEATURE_A' not in response.data
