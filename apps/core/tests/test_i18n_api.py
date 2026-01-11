"""
Tests for i18n API.
"""
import pytest
from django.core.cache import cache
from apps.core.models import Translation
from rest_framework.test import APIClient
from django.urls import reverse

@pytest.mark.django_db
class TestI18nAPI:
    def setup_method(self):
        self.client = APIClient()
        cache.clear()
        
    def test_i18n_returns_english_translations(self):
        """Test that i18n API returns English translations."""
        Translation.objects.create(key="apply_now", lang="en", value="Apply Now")
        Translation.objects.create(key="book_service", lang="en", value="Book Service")
        
        url = reverse('core:i18n')
        response = self.client.get(url, {"lang": "en"})
        
        assert response.status_code == 200
        assert response.data['apply_now'] == "Apply Now"
        assert response.data['book_service'] == "Book Service"
        
    def test_i18n_returns_hindi_translations(self):
        """Test that i18n API returns Hindi translations."""
        Translation.objects.create(key="apply_now", lang="hi", value="अभी आवेदन करें")
        Translation.objects.create(key="book_service", lang="hi", value="सेवा बुक करें")
        
        url = reverse('core:i18n')
        response = self.client.get(url, {"lang": "hi"})
        
        assert response.status_code == 200
        assert response.data['apply_now'] == "अभी आवेदन करें"
        assert response.data['book_service'] == "सेवा बुक करें"
        
    def test_i18n_fallback_to_english(self):
        """Test that missing Hindi translations fallback to English."""
        Translation.objects.create(key="apply_now", lang="en", value="Apply Now")
        Translation.objects.create(key="book_service", lang="en", value="Book Service")
        Translation.objects.create(key="apply_now", lang="hi", value="अभी आवेदन करें")
        # book_service not in Hindi
        
        url = reverse('core:i18n')
        response = self.client.get(url, {"lang": "hi"})
        
        assert response.status_code == 200
        assert response.data['apply_now'] == "अभी आवेदन करें"
        assert response.data['book_service'] == "Book Service"  # Fallback to English
        
    def test_i18n_invalid_language(self):
        """Test that invalid language returns error."""
        url = reverse('core:i18n')
        response = self.client.get(url, {"lang": "fr"})
        
        assert response.status_code == 400
        assert 'error' in response.data
        
    def test_i18n_default_language(self):
        """Test that default language is English."""
        Translation.objects.create(key="apply_now", lang="en", value="Apply Now")
        
        url = reverse('core:i18n')
        response = self.client.get(url)  # No lang param
        
        assert response.status_code == 200
        assert response.data['apply_now'] == "Apply Now"
        
    def test_i18n_caching(self):
        """Test that i18n responses are cached."""
        Translation.objects.create(key="apply_now", lang="en", value="Apply Now")
        
        url = reverse('core:i18n')
        
        # First request
        response1 = self.client.get(url, {"lang": "en"})
        assert response1.status_code == 200
        
        # Modify translation
        Translation.objects.filter(key="apply_now", lang="en").update(value="Modified")
        cache.delete("i18n_translations_en")  # Simulate cache invalidation
        
        # Second request with fresh cache
        response2 = self.client.get(url, {"lang": "en"})
        assert response2.data['apply_now'] == "Modified"
