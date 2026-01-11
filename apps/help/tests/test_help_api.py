"""
Tests for Help & FAQ APIs.
"""
import pytest
from rest_framework.test import APIClient
from django.urls import reverse

from apps.help.models import HelpPage, FAQ


@pytest.mark.django_db
class TestHelpAPI:
    """Test Help Pages API."""
    
    def setup_method(self):
        self.client = APIClient()
        
        # Create test help pages
        self.help_en = HelpPage.objects.create(
            slug='getting-started',
            title='Getting Started',
            content_html='<p>Welcome</p>',
            lang='en',
            is_active=True,
            order=1
        )
        
        self.help_hi = HelpPage.objects.create(
            slug='shuruat',
            title='शुरुआत',
            content_html='<p>स्वागत</p>',
            lang='hi',
            is_active=True,
            order=2
        )
        
        # Inactive help page
        self.help_inactive = HelpPage.objects.create(
            slug='inactive',
            title='Inactive Page',
            content_html='<p>Hidden</p>',
            lang='en',
            is_active=False
        )
    
    def test_list_help_pages(self):
        """Test GET /api/v1/help returns help pages."""
        url = reverse('help-list')
        response = self.client.get(url)
        
        assert response.status_code == 200
        assert len(response.data) >= 2
    
    def test_help_filter_by_language(self):
        """Test filtering help pages by language."""
        url = reverse('help-list')
        
        # Filter English
        response = self.client.get(url, {'lang': 'en'})
        assert response.status_code == 200
        for page in response.data:
            assert page['lang'] == 'en'
        
        # Filter Hindi
        response = self.client.get(url, {'lang': 'hi'})
        assert response.status_code == 200
        for page in response.data:
            assert page['lang'] == 'hi'
    
    def test_inactive_help_excluded(self):
        """Test that inactive help pages are not returned."""
        url = reverse('help-list')
        response = self.client.get(url)
        
        assert response.status_code == 200
        slugs = [p['slug'] for p in response.data]
        assert 'inactive' not in slugs
    
    def test_help_ordering(self):
        """Test that help pages are ordered correctly."""
        url = reverse('help-list')
        response = self.client.get(url)
        
        assert response.status_code == 200
        # Check that lower order numbers come first
        if len(response.data) >= 2:
            assert response.data[0]['order'] <= response.data[1]['order']
    
    def test_help_detail(self):
        """Test getting a single help page by slug."""
        url = reverse('help-detail', kwargs={'slug': 'getting-started'})
        response = self.client.get(url)
        
        assert response.status_code == 200
        assert response.data['slug'] == 'getting-started'
        assert response.data['title'] == 'Getting Started'


@pytest.mark.django_db
class TestFAQAPI:
    """Test FAQ API."""
    
    def setup_method(self):
        self.client = APIClient()
        
        # Create test FAQs
        self.faq_en = FAQ.objects.create(
            question='How to use?',
            answer='Follow these steps...',
            lang='en',
            is_active=True,
            order=1
        )
        
        self.faq_hi = FAQ.objects.create(
            question='कैसे उपयोग करें?',
            answer='ये चरण फॉलो करें...',
            lang='hi',
            is_active=True,
            order=2
        )
        
        # Inactive FAQ
        self.faq_inactive = FAQ.objects.create(
            question='Inactive question?',
            answer='Inactive answer',
            lang='en',
            is_active=False
        )
    
    def test_list_faqs(self):
        """Test GET /api/v1/faqs returns FAQs."""
        url = reverse('faq-list')
        response = self.client.get(url)
        
        assert response.status_code == 200
        assert len(response.data) >= 2
    
    def test_faq_filter_by_language(self):
        """Test filtering FAQs by language."""
        url = reverse('faq-list')
        
        # Filter English
        response = self.client.get(url, {'lang': 'en'})
        assert response.status_code == 200
        for faq in response.data:
            assert faq['lang'] == 'en'
        
        # Filter Hindi
        response = self.client.get(url, {'lang': 'hi'})
        assert response.status_code == 200
        for faq in response.data:
            assert faq['lang'] == 'hi'
    
    def test_inactive_faq_excluded(self):
        """Test that inactive FAQs are not returned."""
        url = reverse('faq-list')
        response = self.client.get(url)
        
        assert response.status_code == 200
        questions = [f['question'] for f in response.data]
        assert 'Inactive question?' not in questions
    
    def test_faq_ordering(self):
        """Test that FAQs are ordered correctly."""
        url = reverse('faq-list')
        response = self.client.get(url)
        
        assert response.status_code == 200
        # Check that lower order numbers come first
        if len(response.data) >= 2:
            assert response.data[0]['order'] <= response.data[1]['order']
    
    def test_faq_has_required_fields(self):
        """Test that FAQs have all required fields."""
        url = reverse('faq-list')
        response = self.client.get(url)
        
        assert response.status_code == 200
        if len(response.data) > 0:
            faq = response.data[0]
            assert 'question' in faq
            assert 'answer' in faq
            assert 'lang' in faq
            assert 'order' in faq
