"""
Tests for TTS stub API.
"""
import pytest
from rest_framework.test import APIClient
from django.urls import reverse


@pytest.mark.django_db
class TestTTSStub:
    """Test TTS stub endpoint."""
    
    def setup_method(self):
        self.client = APIClient()
    
    def test_tts_stub_english(self):
        """Test TTS stub with English language."""
        url = reverse('tts-stub')
        response = self.client.get(url, {'lang': 'en', 'text': 'Hello world'})
        
        assert response.status_code == 200
        assert 'url' in response.data
        assert response.data['lang'] == 'en'
        assert 'tts_stub_en.mp3' in response.data['url']
    
    def test_tts_stub_hindi(self):
        """Test TTS stub with Hindi language."""
        url = reverse('tts-stub')
        response = self.client.get(url, {'lang': 'hi', 'text': 'नमस्ते'})
        
        assert response.status_code == 200
        assert 'url' in response.data
        assert response.data['lang'] == 'hi'
        assert 'tts_stub_hi.mp3' in response.data['url']
    
    def test_tts_stub_default_language(self):
        """Test TTS stub defaults to English."""
        url = reverse('tts-stub')
        response = self.client.get(url, {'text': 'Test'})
        
        assert response.status_code == 200
        assert response.data['lang'] == 'en'
    
    def test_tts_stub_invalid_language(self):
        """Test error for invalid language."""
        url = reverse('tts-stub')
        response = self.client.get(url, {'lang': 'fr', 'text': 'Bonjour'})
        
        assert response.status_code == 400
        assert 'error' in response.data
    
    def test_tts_stub_url_format(self):
        """Test that returned URL ends with .mp3."""
        url = reverse('tts-stub')
        response = self.client.get(url, {'lang': 'en'})
        
        assert response.status_code == 200
        assert response.data['url'].endswith('.mp3')
    
    def test_tts_stub_no_auth_required(self):
        """Test that TTS stub is publicly accessible."""
        url = reverse('tts-stub')
        response = self.client.get(url, {'lang': 'hi'})
        
        # Should work without authentication
        assert response.status_code == 200
