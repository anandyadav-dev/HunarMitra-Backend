"""
Tests for Banners API.
"""
import pytest
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from django.urls import reverse

from apps.cms.models import Banner


@pytest.mark.django_db
class TestBannersAPI:
    """Test promotional banners API."""
    
    def setup_method(self):
        self.client = APIClient()
        self.url = reverse('banner-list')
        
        # Get current time
        self.now = timezone.now()
    
    def test_only_active_banners_returned(self):
        """Test that only active banners are returned."""
        # Create active banner
        active_banner = Banner.objects.create(
            title='Active Banner',
            image_url='https://example.com/active.jpg',
            slot='home_top',
            priority=10,
            active=True
        )
        
        # Create inactive banner
        Banner.objects.create(
            title='Inactive Banner',
            image_url='https://example.com/inactive.jpg',
            slot='home_top',
            priority=20,
            active=False
        )
        
        response = self.client.get(self.url)
        
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['title'] == 'Active Banner'
    
    def test_expired_banners_excluded(self):
        """Test that expired banners are not returned."""
        # Create current banner
        current_banner = Banner.objects.create(
            title='Current Banner',
            image_url='https://example.com/current.jpg',
            slot='home_top',
            priority=10,
            active=True,
            starts_at=self.now - timedelta(days=5),
            ends_at=self.now + timedelta(days=5)
        )
        
        # Create expired banner
        Banner.objects.create(
            title='Expired Banner',
            image_url='https://example.com/expired.jpg',
            slot='home_top',
            priority=20,
            active=True,
            starts_at=self.now - timedelta(days=10),
            ends_at=self.now - timedelta(days=1)  # Ended yesterday
        )
        
        response = self.client.get(self.url)
        
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['title'] == 'Current Banner'
    
    def test_future_banners_excluded(self):
        """Test that future banners (not yet started) are not returned."""
        # Create current banner
        Banner.objects.create(
            title='Current Banner',
            image_url='https://example.com/current.jpg',
            slot='home_top',
            priority=10,
            active=True
        )
        
        # Create future banner
        Banner.objects.create(
            title='Future Banner',
            image_url='https://example.com/future.jpg',
            slot='home_top',
            priority=20,
            active=True,
            starts_at=self.now + timedelta(days=1)  # Starts tomorrow
        )
        
        response = self.client.get(self.url)
        
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['title'] == 'Current Banner'
    
    def test_slot_filtering(self):
        """Test filtering banners by slot."""
        # Create home_top banner
        Banner.objects.create(
            title='Home Top Banner',
            image_url='https://example.com/home-top.jpg',
            slot='home_top',
            priority=10,
            active=True
        )
        
        # Create home_mid banner
        Banner.objects.create(
            title='Home Mid Banner',
            image_url='https://example.com/home-mid.jpg',
            slot='home_mid',
            priority=10,
            active=True
        )
        
        # Filter by home_top
        response = self.client.get(self.url, {'slot': 'home_top'})
        
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['title'] == 'Home Top Banner'
        assert response.data[0]['slot'] == 'home_top'
    
    def test_priority_ordering(self):
        """Test that banners are ordered by priority (descending)."""
        # Create banners with different priorities
        Banner.objects.create(
            title='Low Priority',
            image_url='https://example.com/low.jpg',
            slot='home_top',
            priority=10,
            active=True
        )
        
        Banner.objects.create(
            title='High Priority',
            image_url='https://example.com/high.jpg',
            slot='home_top',
            priority=100,
            active=True
        )
        
        Banner.objects.create(
            title='Medium Priority',
            image_url='https://example.com/medium.jpg',
            slot='home_top',
            priority=50,
            active=True
        )
        
        response = self.client.get(self.url)
        
        assert response.status_code == 200
        assert len(response.data) == 3
        assert response.data[0]['title'] == 'High Priority'
        assert response.data[1]['title'] == 'Medium Priority'
        assert response.data[2]['title'] == 'Low Priority'
    
    def test_null_dates_always_visible(self):
        """Test that banners with null start/end dates are always visible."""
        # Create banner with no date constraints
        Banner.objects.create(
            title='Always Visible',
            image_url='https://example.com/always.jpg',
            slot='home_top',
            priority=10,
            active=True,
            starts_at=None,
            ends_at=None
        )
        
        response = self.client.get(self.url)
        
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['title'] == 'Always Visible'
    
    def test_public_endpoint_no_auth_required(self):
        """Test that banners API is public (no auth required)."""
        Banner.objects.create(
            title='Public Banner',
            image_url='https://example.com/public.jpg',
            slot='home_top',
            active=True
        )
        
        # Call without authentication
        response = self.client.get(self.url)
        
        assert response.status_code == 200
        assert len(response.data) == 1
    
    def test_response_structure(self):
        """Test that response has correct structure."""
        Banner.objects.create(
            title='Test Banner',
            image_url='https://example.com/test.jpg',
            link='https://example.com/link',
            slot='home_top',
            priority=50,
            active=True
        )
        
        response = self.client.get(self.url)
        
        assert response.status_code == 200
        assert len(response.data) == 1
        
        banner = response.data[0]
        assert 'id' in banner
        assert 'title' in banner
        assert 'image_url' in banner
        assert 'link' in banner
        assert 'slot' in banner
        assert 'priority' in banner
        
        # Verify values
        assert banner['title'] == 'Test Banner'
        assert banner['image_url'] == 'https://example.com/test.jpg'
        assert banner['link'] == 'https://example.com/link'
        assert banner['slot'] == 'home_top'
        assert banner['priority'] == 50
