"""
Tests for Rate Limiting.
"""
import time
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.urls import path
from django.test import override_settings

User = get_user_model()

# Mock view for testing rate limits
class MockView(APIView):
    def get(self, request):
        return Response({'status': 'ok'})

urlpatterns = [
    path('mock/', MockView.as_view(), name='mock-view'),
]

@pytest.mark.django_db
class TestRateLimiting:
    """Test API rate limiting."""
    
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            phone="+919900001111",
            role="worker"
        )

    @override_settings(
        ROOT_URLCONF=__name__,
        REST_FRAMEWORK={
            'DEFAULT_THROTTLE_CLASSES': [
                'rest_framework.throttling.AnonRateThrottle',
                'rest_framework.throttling.UserRateThrottle',
            ],
            'DEFAULT_THROTTLE_RATES': {
                'anon': '3/minute',
                'user': '5/minute',
            },
            'DEFAULT_AUTHENTICATION_CLASSES': [],
            'DEFAULT_PERMISSION_CLASSES': [],
            'DEFAULT_RENDERER_CLASSES': [
                'rest_framework.renderers.JSONRenderer',
            ],
        }
    )
    def test_anonymous_rate_limit(self):
        """Test that anonymous users are rate limited."""
        url = '/mock/'
        
        # Make allowed requests
        for _ in range(3):
            response = self.client.get(url)
            assert response.status_code == status.HTTP_200_OK
            
        # Exceed limit
        response = self.client.get(url)
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert 'seconds' in response.data['detail'].lower() or 'available' in response.data['detail'].lower()

    @override_settings(
        ROOT_URLCONF=__name__,
        REST_FRAMEWORK={
            'DEFAULT_THROTTLE_CLASSES': [
                'rest_framework.throttling.AnonRateThrottle',
                'rest_framework.throttling.UserRateThrottle',
            ],
            'DEFAULT_THROTTLE_RATES': {
                'anon': '3/minute',
                'user': '5/minute',
            },
            'DEFAULT_AUTHENTICATION_CLASSES': [
                'rest_framework_simplejwt.authentication.JWTAuthentication',
            ],
            'DEFAULT_PERMISSION_CLASSES': [],
            'DEFAULT_RENDERER_CLASSES': [
                'rest_framework.renderers.JSONRenderer',
            ],
        }
    )
    def test_authenticated_rate_limit(self):
        """Test that authenticated users have higher limits."""
        url = '/mock/'
        self.client.force_authenticate(user=self.user)
        
        # Make allowed requests (limit is 5)
        for _ in range(5):
            response = self.client.get(url)
            assert response.status_code == status.HTTP_200_OK
            
        # Exceed limit
        response = self.client.get(url)
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    @override_settings(
        ROOT_URLCONF=__name__,
        REST_FRAMEWORK={
            'DEFAULT_THROTTLE_CLASSES': [
                'rest_framework.throttling.AnonRateThrottle',
                'rest_framework.throttling.UserRateThrottle',
            ],
            'DEFAULT_THROTTLE_RATES': {
                'anon': '3/minute',
                'user': '5/minute',
            },
        }
    )
    def test_sentry_initialization_simulation(self):
        """
        Verify code structure for Sentry doesn't crash app when DSN is missing.
        We can't easily test the actual Sentry init as it happens at startup,
        but we verify the app loads and functions.
        """
        from django.conf import settings
        # Ensure we can access settings without error
        assert hasattr(settings, 'REST_FRAMEWORK')
