"""
Tests for app configuration endpoint.
"""

import pytest
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.models import Banner, Theme
from apps.core.utils import get_s3_public_url
from apps.services.models import Service


@pytest.mark.django_db
class TestAppConfigEndpoint:
    """Tests for /api/v1/app-config/ endpoint."""

    def setup_method(self):
        """Setup for each test method."""
        cache.clear()

    def test_app_config_returns_200(self):
        """Test that app config endpoint returns 200."""
        client = APIClient()
        url = reverse("core:app-config")
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_app_config_structure(self):
        """Test that app config returns expected JSON structure."""
        client = APIClient()
        url = reverse("core:app-config")
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK

        data = response.data

        # Check top-level keys
        assert "app" in data
        assert "theme" in data
        assert "categories" in data
        assert "banners" in data
        assert "features" in data
        assert "meta" in data

        # Check app metadata
        assert "name" in data["app"]
        assert "version" in data["app"]
        assert "supported_locales" in data["app"]
        assert isinstance(data["app"]["supported_locales"], list)

        # Check theme
        assert "primary_color" in data["theme"]
        assert "accent_color" in data["theme"]
        assert "background_color" in data["theme"]
        assert "logo_url" in data["theme"]
        assert "fonts" in data["theme"]

        # Check categories is a list
        assert isinstance(data["categories"], list)

        # Check banners is a list
        assert isinstance(data["banners"], list)

        # Check features is a dict
        assert isinstance(data["features"], dict)

        # Check meta
        assert "config_version" in data["meta"]
        assert "cache_ttl_seconds" in data["meta"]

    def test_app_config_with_active_theme(self):
        """Test that active theme is returned when present."""
        # Create an active theme
        theme = Theme.objects.create(
            name="Test Theme",
            primary_color="#FF0000",
            accent_color="#00FF00",
            background_color="#0000FF",
            logo_s3_key="test/logo.png",
            active=True,
        )

        client = APIClient()
        url = reverse("core:app-config")
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["theme"]["name"] == "Test Theme"
        assert response.data["theme"]["primary_color"] == "#FF0000"

    def test_app_config_with_services(self):
        """Test that active services are returned as categories."""
        # Create test services
        Service.objects.create(
            name="Plumbing", slug="plumbing", is_active=True, display_order=1
        )
        Service.objects.create(
            name="Electrical", slug="electrical", is_active=True, display_order=2
        )
        Service.objects.create(
            name="Inactive", slug="inactive", is_active=False, display_order=3
        )

        client = APIClient()
        url = reverse("core:app-config")
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        categories = response.data["categories"]

        # Should only return active services
        assert len(categories) == 2
        category_names = [c["name"] for c in categories]
        assert "Plumbing" in category_names
        assert "Electrical" in category_names
        assert "Inactive" not in category_names

    def test_app_config_with_banners(self):
        """Test that active banners are returned."""
        # Create test banners
        Banner.objects.create(
            title="Banner 1",
            subtitle="Test subtitle",
            image_s3_key="banners/test1.png",
            action={"type": "url", "value": "https://example.com"},
            display_order=1,
            active=True,
        )
        Banner.objects.create(
            title="Banner 2",
            subtitle="Test subtitle 2",
            image_s3_key="banners/test2.png",
            action={"type": "route", "value": "/services"},
            display_order=2,
            active=True,
        )
        Banner.objects.create(
            title="Inactive Banner",
            image_s3_key="banners/inactive.png",
            action={},
            display_order=3,
            active=False,
        )

        client = APIClient()
        url = reverse("core:app-config")
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        banners = response.data["banners"]

        # Should only return active banners
        assert len(banners) == 2
        banner_titles = [b["title"] for b in banners]
        assert "Banner 1" in banner_titles
        assert "Banner 2" in banner_titles
        assert "Inactive Banner" not in banner_titles

    def test_app_config_cache(self):
        """Test that response is cached."""
        client = APIClient()
        url = reverse("core:app-config")
        
        # Create initial theme
        theme = Theme.objects.create(
            name="Initial Theme",
            primary_color="#123456",
            active=True
        )

        # First request populates cache
        response1 = client.get(url)
        assert response1.status_code == status.HTTP_200_OK
        assert response1.data["theme"]["name"] == "Initial Theme"

        # Update theme bypassing signals (using queryset update) so cache is NOT invalidated
        Theme.objects.filter(id=theme.id).update(name="Updated Theme Name")

        # Second request should return cached data (Old Name)
        response2 = client.get(url)
        assert response2.status_code == status.HTTP_200_OK
        assert response2.data["theme"]["name"] == "Initial Theme"

        # Clear cache and try again
        cache.clear()
        
        # Third request should see the update
        response3 = client.get(url)
        assert response3.status_code == status.HTTP_200_OK
        assert response3.data["theme"]["name"] == "Updated Theme Name"

    def test_app_config_fallback_when_no_theme(self):
        """Test that default theme is returned when no active theme exists."""
        # Ensure no active themes
        Theme.objects.all().delete()

        client = APIClient()
        url = reverse("core:app-config")
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "theme" in response.data
        assert response.data["theme"]["name"] == "Default"


@pytest.mark.django_db
class TestS3URLResolution:
    """Tests for S3 URL resolution utility."""

    def test_get_s3_public_url(self):
        """Test S3 key to URL conversion."""
        s3_key = "static/logo.png"
        url = get_s3_public_url(s3_key)

        assert url is not None
        assert s3_key in url
        assert url.startswith("http")

    def test_get_s3_public_url_with_leading_slash(self):
        """Test S3 URL resolution removes leading slash."""
        s3_key = "/static/logo.png"
        url = get_s3_public_url(s3_key)

        assert url is not None
        assert "//static" not in url  # Should not have double slashes

    def test_get_s3_public_url_with_empty_key(self):
        """Test S3 URL resolution with empty key."""
        url = get_s3_public_url("")

        assert url is None

    def test_get_s3_public_url_with_none(self):
        """Test S3 URL resolution with None."""
        url = get_s3_public_url(None)

        assert url is None
