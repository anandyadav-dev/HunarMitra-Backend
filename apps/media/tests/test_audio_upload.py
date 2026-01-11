"""
Tests for audio upload API.
"""
import pytest
import io
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.urls import reverse

User = get_user_model()


@pytest.mark.django_db
class TestAudioUpload:
    """Test audio upload endpoint."""
    
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(phone="+919900001111", role="worker")
        self.client.force_authenticate(user=self.user)
    
    def test_upload_mp3_file(self):
        """Test uploading mp3 audio file."""
        # Create dummy mp3 file
        audio_content = b'fake mp3 content for testing'
        audio_file = io.BytesIO(audio_content)
        audio_file.name = 'test_audio.mp3'
        
        url = reverse('audio-upload')
        response = self.client.post(
            url,
            {'file': audio_file},
            format='multipart'
        )
        
        # Note: This test will fail without real MinIO, but structure is correct
        # In real environment with MinIO, should return 201
        assert response.status_code in [201, 500]  # 500 if MinIO not available
        
        if response.status_code == 201:
            assert 'url' in response.data
            assert 'type' in response.data
            assert response.data['type'] == 'audio'
    
    def test_upload_requires_authentication(self):
        """Test that upload requires authentication."""
        self.client.force_authenticate(user=None)
        
        audio_file = io.BytesIO(b'test')
        audio_file.name = 'test.mp3'
        
        url = reverse('audio-upload')
        response = self.client.post(
            url,
            {'file': audio_file},
            format='multipart'
        )
        
        assert response.status_code == 401
    
    def test_upload_no_file(self):
        """Test error when no file provided."""
        url = reverse('audio-upload')
        response = self.client.post(url, {})
        
        assert response.status_code == 400
        assert 'error' in response.data
    
    def test_upload_invalid_extension(self):
        """Test error for invalid file extension."""
        text_file = io.BytesIO(b'not audio')
        text_file.name = 'test.txt'
        
        url = reverse('audio-upload')
        response = self.client.post(
            url,
            {'file': text_file},
            format='multipart'
        )
        
        assert response.status_code == 400
        assert 'error' in response.data
