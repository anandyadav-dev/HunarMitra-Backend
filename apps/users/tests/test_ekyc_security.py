"""
Security tests for eKYC implementation.

CRITICAL TESTS:
- Ensures only last 4 digits are stored
- Validates encryption at rest
- Tests that API never returns full Aadhaar
- Ensures validation prevents full Aadhaar storage
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.urls import reverse

from core.crypto import encrypt_value, decrypt_value

User = get_user_model()


@pytest.mark.django_db
class TestEKYCEncryption:
    """Test encryption/decryption of Aadhaar last-4."""
    
    def test_encrypt_decrypt_value(self):
        """Test that values can be encrypted and decrypted correctly."""
        original = "1234"
        encrypted = encrypt_value(original)
        
        # Verify it's encrypted (binary)
        assert isinstance(encrypted, bytes)
        assert encrypted != original.encode()
        
        # Verify decryption
        decrypted = decrypt_value(encrypted)
        assert decrypted == original
    
    def test_encrypted_value_not_plaintext(self):
        """Test that encrypted value is not readable plaintext."""
        last4 = "5678"
        encrypted = encrypt_value(last4)
        
        # Encrypted value should not contain the plaintext
        assert b"5678" not in encrypted
        assert "5678" not in encrypted.decode('utf-8', errors='ignore')


@pytest.mark.django_db
class TestEKYCAPI:
    """Test eKYC API endpoints for security compliance."""
    
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            phone="+919876543210",
            role="worker"
        )
    
    def test_upload_only_accepts_4_digits(self):
        """Test that API only accepts exactly 4 digits."""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('auth:ekyc-upload', kwargs={'user_id': self.user.id})
        
        # Test exactly 4 digits - should succeed
        response = self.client.post(url, {"aadhaar_last4": "1234"})
        assert response.status_code == 200
        
        # Test more than 4 digits - should fail
        response = self.client.post(url, {"aadhaar_last4": "12345"})
        assert response.status_code == 400
        
        # Test less than 4 digits - should fail
        response = self.client.post(url, {"aadhaar_last4": "123"})
        assert response.status_code == 400
        
        # Test non-digits - should fail
        response = self.client.post(url, {"aadhaar_last4": "abcd"})
        assert response.status_code == 400
    
    def test_upload_stores_encrypted_value(self):
        """Test that uploaded value is stored encrypted, not plaintext."""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('auth:ekyc-upload', kwargs={'user_id': self.user.id})
        response = self.client.post(url, {"aadhaar_last4": "9876"})
        
        assert response.status_code == 200
        
        # Refresh user from DB
        self.user.refresh_from_db()
        
        # Verify field is not None
        assert self.user.aadhaar_last4_encrypted is not None
        
        # Verify it's binary (encrypted)
        assert isinstance(self.user.aadhaar_last4_encrypted, (bytes, memoryview))
        
        # Verify plaintext "9876" is not in the encrypted value
        encrypted_bytes = bytes(self.user.aadhaar_last4_encrypted)
        assert b"9876" not in encrypted_bytes
    
    def test_upload_sets_ekyc_status(self):
        """Test that upload sets eKYC status to ocr_scanned."""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('auth:ekyc-upload', kwargs={'user_id': self.user.id})
        response = self.client.post(url, {"aadhaar_last4": "4321"})
        
        assert response.status_code == 200
        assert response.data['ekyc_status'] == 'ocr_scanned'
        
        self.user.refresh_from_db()
        assert self.user.ekyc_status == 'ocr_scanned'
    
    def test_api_returns_masked_format(self):
        """Test that API never returns full/unmasked Aadhaar."""
        self.client.force_authenticate(user=self.user)
        
        # Upload
        upload_url = reverse('auth:ekyc-upload', kwargs={'user_id': self.user.id})
        response = self.client.post(upload_url, {"aadhaar_last4": "7890"})
        
        assert response.status_code == 200
        assert response.data['aadhaar_masked'] == "XXXX-7890"
        
        # Get status
        status_url = reverse('auth:ekyc-status', kwargs={'user_id': self.user.id})
        response = self.client.get(status_url)
        
        assert response.status_code == 200
        assert response.data['aadhaar_masked'] == "XXXX-7890"
        
        # Verify response never contains bare digits
        response_str = str(response.data)
        assert "7890" in response_str  # OK in masked format
        assert response_str.count("7890") == 1  # Only once (in masked format)
    
    def test_permission_check_own_ekyc_only(self):
        """Test that users can only access their own eKYC data."""
        other_user = User.objects.create_user(
            phone="+919000000001",
            role="worker"
        )
        
        self.client.force_authenticate(user=other_user)
        
        # Try to upload for different user
        url = reverse('auth:ekyc-upload', kwargs={'user_id': self.user.id})
        response = self.client.post(url, {"aadhaar_last4": "1111"})
        
        assert response.status_code == 403
    
    def test_masked_property_returns_correct_format(self):
        """Test that User.aadhaar_last4_masked property returns correct format."""
        # Set encrypted value
        encrypted = encrypt_value("2468")
        self.user.aadhaar_last4_encrypted = encrypted
        self.user.save()
        
        # Check masked property
        assert self.user.aadhaar_last4_masked == "XXXX-2468"
    
    def test_no_aadhaar_returns_none(self):
        """Test that masked property returns None if no Aadhaar set."""
        assert self.user.aadhaar_last4_encrypted is None
        assert self.user.aadhaar_last4_masked is None


@pytest.mark.django_db
class TestEKYCValidation:
    """Test validation prevents security violations."""
    
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            phone="+919111111111",
            role="worker"
        )
    
    def test_rejects_full_aadhaar_number(self):
        """Test that system rejects if someone tries to send full Aadhaar."""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('auth:ekyc-upload', kwargs={'user_id': self.user.id})
        
        # Try to send 12 digits (full Aadhaar)
        response = self.client.post(url, {"aadhaar_last4": "123456789012"})
        
        assert response.status_code == 400
        assert 'error' in response.data or 'aadhaar_last4' in response.data
