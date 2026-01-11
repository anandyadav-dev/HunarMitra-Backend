"""
Tests for Analytics Event API.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.urls import reverse

from apps.analytics.models import Event

User = get_user_model()


@pytest.mark.django_db
class TestAnalyticsEventAPI:
    """Test analytics event collection API."""
    
    def setup_method(self):
        self.client = APIClient()
        self.url = reverse('event-create')
        
        # Create test user
        self.user = User.objects.create_user(
            phone="+919900001111",
            role="worker"
        )
    
    def test_event_posted_without_auth(self):
        """Test that event can be posted without authentication."""
        data = {
            'name': 'screen_viewed',
            'payload': {
                'screen': 'home',
                'timestamp': '2026-01-03T09:30:00Z'
            }
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == 201
        assert response.data['name'] == 'screen_viewed'
        assert 'id' in response.data
        assert 'created_at' in response.data
        
        # Verify event was created with no user
        event = Event.objects.get(id=response.data['id'])
        assert event.user is None
        assert event.name == 'screen_viewed'
        assert event.payload == data['payload']
    
    def test_event_posted_with_auth(self):
        """Test that event can be posted with authentication and user is linked."""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'name': 'job_apply_clicked',
            'payload': {
                'job_id': 'uuid-123',
                'job_title': 'Plumber Needed'
            }
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == 201
        assert response.data['name'] == 'job_apply_clicked'
        
        # Verify event was created with user link
        event = Event.objects.get(id=response.data['id'])
        assert event.user == self.user
        assert event.name == 'job_apply_clicked'
        assert event.payload == data['payload']
    
    def test_payload_json_stored_correctly(self):
        """Test that complex JSON payload is stored correctly."""
        data = {
            'name': 'search_performed',
            'payload': {
                'query': 'plumber',
                'location': 'Delhi',
                'filters': {
                    'rating': 4,
                    'price_range': [100, 1000]
                },
                'results_count': 15
            }
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == 201
        
        # Verify payload stored correctly
        event = Event.objects.get(id=response.data['id'])
        assert event.payload['query'] == 'plumber'
        assert event.payload['filters']['rating'] == 4
        assert event.payload['results_count'] == 15
    
    def test_empty_event_name_rejected(self):
        """Test that empty event name is rejected."""
        data = {
            'name': '',
            'payload': {}
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == 400
        assert 'name' in response.data
    
    def test_whitespace_event_name_rejected(self):
        """Test that whitespace-only event name is rejected."""
        data = {
            'name': '   ',
            'payload': {}
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == 400
    
    def test_default_source_is_mobile(self):
        """Test that default source is 'mobile' if not specified."""
        data = {
            'name': 'button_clicked',
            'payload': {'button': 'submit'}
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == 201
        
        event = Event.objects.get(id=response.data['id'])
        assert event.source == 'mobile'
    
    def test_custom_source_accepted(self):
        """Test that custom source can be specified."""
        data = {
            'name': 'page_viewed',
            'payload': {},
            'source': 'web'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == 201
        
        event = Event.objects.get(id=response.data['id'])
        assert event.source == 'web'
    
    def test_missing_payload_defaults_to_empty_dict(self):
        """Test that missing payload defaults to empty dict."""
        data = {
            'name': 'simple_event'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == 201
        
        event = Event.objects.get(id=response.data['id'])
        assert event.payload == {}
    
    def test_admin_can_query_events(self):
        """Test that events can be queried from database."""
        # Create events
        Event.objects.create(
            name='event1',
            payload={'data': 'test1'}
        )
        Event.objects.create(
            name='event2',
            user=self.user,
            payload={'data': 'test2'}
        )
        
        # Query events
        events = Event.objects.all()
        assert events.count() == 2
        
        # Query by name
        event1 = Event.objects.filter(name='event1').first()
        assert event1 is not None
        assert event1.user is None
        
        # Query by user
        user_events = Event.objects.filter(user=self.user)
        assert user_events.count() == 1
        assert user_events.first().name == 'event2'
    
    def test_multiple_events_same_user(self):
        """Test that same user can create multiple events."""
        self.client.force_authenticate(user=self.user)
        
        # Create first event
        response1 = self.client.post(self.url, {'name': 'event1'}, format='json')
        assert response1.status_code == 201
        
        # Create second event
        response2 = self.client.post(self.url, {'name': 'event2'}, format='json')
        assert response2.status_code == 201
        
        # Verify both events exist
        user_events = Event.objects.filter(user=self.user)
        assert user_events.count() == 2
