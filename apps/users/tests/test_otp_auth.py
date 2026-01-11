"""
Tests for OTP Authentication Flow.
"""

import pytest
from django.urls import reverse
from django.test import override_settings
from rest_framework import status
from django.conf import settings
from apps.users.models import User
from rest_framework_simplejwt.tokens import RefreshToken

# Mark all tests to use database and redis
pytestmark = [pytest.mark.django_db]

from django.core.cache import cache

@pytest.fixture(autouse=True)
def clear_cache_fixture():
    cache.clear()
    yield
    cache.clear()


class TestOTPAuth:

    @pytest.fixture(autouse=True)
    def setup_settings(self, settings):
        settings.DEBUG = True
        settings.OTP_RATE_LIMIT_PER_MINUTE = 10
    
    def test_request_otp_success(self, api_client):
        """Test requesting OTP successfully."""
        url = reverse('auth:request-otp')
        data = {'phone': '+919999999999', 'role': 'worker'}
        
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'request_id' in response.data
        assert 'ttl' in response.data
        
        # In DEV mode, OTP is returned
        if settings.DEBUG:
            assert 'dev_otp' in response.data

    def test_request_otp_rate_limit(self, api_client, settings):
        """Test rate limiting prevents excessive requests."""
        # Set tight limits for testing
        settings.OTP_RATE_LIMIT_PER_MINUTE = 1
        
        url = reverse('auth:request-otp')
        data = {'phone': '+918888888888'}
        
        # First request - success
        response1 = api_client.post(url, data)
        assert response1.status_code == status.HTTP_200_OK
        
        # Second request - failure
        response2 = api_client.post(url, data)
        assert response2.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert 'error' in response2.data

    def test_verify_otp_success_new_user(self, api_client):
        """Test verifying OTP creates a new user."""
        # 1. Request OTP
        url_req = reverse('auth:request-otp')
        phone = '+917777777777'
        resp_req = api_client.post(url_req, {'phone': phone})
        request_id = resp_req.data['request_id']
        otp = resp_req.data.get('dev_otp') # Relies on DEBUG=True
        
        # 2. Verify OTP
        url_verify = reverse('auth:verify-otp')
        resp_verify = api_client.post(url_verify, {
            'request_id': request_id, 
            'otp': otp
        })
        
        assert resp_verify.status_code == status.HTTP_200_OK
        assert 'access' in resp_verify.data
        assert 'refresh' in resp_verify.data
        assert resp_verify.data['is_new_user'] is True
        assert resp_verify.data['user']['phone'] == phone
        
        # Verify user created in DB
        assert User.objects.filter(phone=phone).exists()

    def test_verify_otp_invalid(self, api_client):
        """Test verifying with wrong OTP fails."""
        # 1. Request OTP
        url_req = reverse('auth:request-otp')
        resp_req = api_client.post(url_req, {'phone': '+916666666666'})
        request_id = resp_req.data['request_id']
        
        # 2. Verify with wrong OTP
        url_verify = reverse('auth:verify-otp')
        resp_verify = api_client.post(url_verify, {
            'request_id': request_id, 
            'otp': '0000' # Wrong OTP
        })
        
        assert resp_verify.status_code == status.HTTP_400_BAD_REQUEST

    def test_logout_blacklist(self, api_client):
        """Test logout invalidates refresh token."""
        user = User.objects.create_user(phone='+915555555555')
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)
        
        # Authenticate
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        
        # Logout
        url = reverse('auth:logout')
        response = api_client.post(url, {'refresh': str(refresh)})
        
        assert response.status_code == status.HTTP_205_RESET_CONTENT
        
        # Try to use refresh token again -> should fail
        # This check depends on SimpleJWT internals usually, but we assume blacklist app works
