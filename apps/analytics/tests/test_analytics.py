"""
Comprehensive tests for analytics event ingestion and reporting.
"""
from django.test import TestCase, override_settings
from django.utils import timezone
from django.core.management import call_command
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta
import json

from apps.users.models import User
from apps.analytics.models import Event, EventAggregateDaily


class EventIngestionTests(TestCase):
    """Test cases for event ingestion API."""
    
    def setUp(self):
        """Set up test client and users."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            phone="+919900000001",
            role="worker"
        )
    
    def test_event_ingestion_single_authenticated(self):
        """Test single event ingestion with authenticated user."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/api/v1/analytics/events/', {
            'event_type': 'page_view',
            'source': 'android',
            'payload': {'page': 'dashboard'}
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('event_id', response.data)
        
        # Verify event created
        event = Event.objects.get(id=response.data['event_id'])
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.event_type, 'page_view')
        self.assertEqual(event.source, 'android')
        self.assertEqual(event.payload, {'page': 'dashboard'})
    
    def test_event_ingestion_single_anonymous(self):
        """Test single event ingestion without authentication."""
        response = self.client.post('/api/v1/analytics/events/', {
            'event_type': 'page_view',
            'anonymous_id': 'anon-123',
            'source': 'web'
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        event = Event.objects.get(id=response.data['event_id'])
        self.assertIsNone(event.user)
        self.assertEqual(event.anonymous_id, 'anon-123')
    
    def test_event_ingestion_bulk(self):
        """Test bulk event ingestion."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/api/v1/analytics/events/', {
            'events': [
                {'event_type': 'page_view', 'payload': {'page': '1'}},
                {'event_type': 'booking_created', 'payload': {'booking_id': '123'}},
                {'event_type': 'job_apply', 'payload': {'job_id': '456'}}
            ]
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['events_created'], 3)
        self.assertEqual(len(response.data['event_ids']), 3)
        
        # Verify all events created
        self.assertEqual(Event.objects.filter(user=self.user).count(), 3)
    
    def test_event_payload_size_limit(self):
        """Test payload size limit enforcement."""
        large_payload = {'data': 'x' * 3000}  # Exceeds 2KB limit
        
        response = self.client.post('/api/v1/analytics/events/', {
            'event_type': 'test',
            'payload': large_payload
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Payload size', str(response.data))
    
    @override_settings(ANALYTICS_ENABLED=False)
    def test_analytics_disabled_returns_204(self):
        """Test that analytics returns 204 when disabled."""
        response = self.client.post('/api/v1/analytics/events/', {
            'event_type': 'page_view'
        })
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Event.objects.count(), 0)
    
    def test_event_captures_ip_and_user_agent(self):
        """Test that events capture IP address and user agent."""
        response = self.client.post(
            '/api/v1/analytics/events/',
            {'event_type': 'page_view'},
            HTTP_USER_AGENT='TestBrowser/1.0',
            HTTP_X_FORWARDED_FOR='192.168.1.1'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        event = Event.objects.get(id=response.data['event_id'])
        self.assertEqual(event.ip_address, '192.168.1.1')
        self.assertEqual(event.user_agent, 'TestBrowser/1.0')


class DailyAggregationTests(TestCase):
    """Test cases for daily aggregation command."""
    
    def setUp(self):
        """Create test events."""
        self.user1 = User.objects.create_user(phone="+919900000001")
        self.user2 = User.objects.create_user(phone="+919900000002")
        
        # Create events for specific date
        self.target_date = timezone.now().date() - timedelta(days=1)
        target_datetime = timezone.make_aware(
            timezone.datetime.combine(self.target_date, timezone.datetime.min.time())
        )
        
        Event.objects.create(
            user=self.user1,
            event_type='page_view',
            source='android',
            created_at=target_datetime
        )
        Event.objects.create(
            user=self.user2,
            event_type='page_view',
            source='android',
            created_at=target_datetime
        )
        Event.objects.create(
            user=self.user1,
            event_type='booking_created',
            source='web',
            created_at=target_datetime
        )
    
    def test_daily_aggregation_command_creates_aggregates(self):
        """Test that aggregation command creates daily aggregates."""
        # Run aggregation
        call_command('analytics_aggregate_daily', date=str(self.target_date))
        
        # Verify aggregates created
        aggregates = EventAggregateDaily.objects.filter(date=self.target_date)
        self.assertGreater(aggregates.count(), 0)
        
        # Check page_view aggregate
        page_view_agg = aggregates.get(event_type='page_view', source='android')
        self.assertEqual(page_view_agg.count, 2)
        self.assertEqual(page_view_agg.unique_users, 2)
        
        # Check booking_created aggregate
        booking_agg = aggregates.get(event_type='booking_created', source='web')
        self.assertEqual(booking_agg.count, 1)
        self.assertEqual(booking_agg.unique_users, 1)
    
    def test_aggregation_is_idempotent(self):
        """Test that running aggregation twice doesn't duplicate."""
        # Run twice
        call_command('analytics_aggregate_daily', date=str(self.target_date))
        call_command('analytics_aggregate_daily', date=str(self.target_date))
        
        # Should still have same number of aggregates
        aggregates = EventAggregateDaily.objects.filter(date=self.target_date)
        
        # Should have 2 aggregates (page_view+android, booking_created+web)
        self.assertEqual(aggregates.count(), 2)


class AdminReportsTests(TestCase):
    """Test cases for admin report endpoints."""
    
    def setUp(self):
        """Set up admin user and test events."""
        self.admin = User.objects.create_superuser(
            phone="+919000000000",
            password="admin123"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)
        
        # Create test events
        self.today = timezone.now().date()
        today_datetime = timezone.make_aware(
            timezone.datetime.combine(self.today, timezone.datetime.min.time())
        )
        
        user = User.objects.create_user(phone="+919900000001")
        
        Event.objects.create(
            user=user,
            event_type='page_view',
            source='android',
            created_at=today_datetime
        )
        Event.objects.create(
            anonymous_id='anon-123',
            event_type='page_view',
            source='web',
            created_at=today_datetime
        )
        Event.objects.create(
            user=user,
            event_type='booking_created',
            source='android',
            created_at=today_datetime
        )
    
    def test_daily_summary_returns_expected_counts(self):
        """Test daily summary endpoint returns correct counts."""
        response = self.client.get(
            f'/api/admin/analytics/daily-summary/?date={self.today}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_events'], 3)
        self.assertEqual(response.data['unique_users'], 1)
        self.assertEqual(response.data['unique_anonymous'], 1)
        self.assertEqual(response.data['events_by_type']['page_view'], 2)
        self.assertEqual(response.data['events_by_type']['booking_created'], 1)
    
    def test_active_users_endpoint(self):
        """Test active users endpoint."""
        response = self.client.get(
            f'/api/admin/analytics/active-users/?date={self.today}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['daily_active_users'], 1)
        self.assertEqual(response.data['unique_anonymous'], 1)
        self.assertEqual(response.data['total_active'], 2)
    
    def test_csv_export_format(self):
        """Test CSV export returns correctly formatted data."""
        response = self.client.get(
            f'/api/admin/analytics/export/?date={self.today}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])
        
        # Check CSV content
        content = b''.join(response.streaming_content).decode('utf-8')
        lines = content.strip().split('\n')
        
        # Should have header + 3 data rows
        self.assertGreaterEqual(len(lines), 4)
        self.assertIn('event_type', lines[0])
    
    def test_reports_require_admin_permission(self):
        """Test that report endpoints require admin permissions."""
        # Create regular user
        user = User.objects.create_user(phone="+919900000002")
        self.client.force_authenticate(user=user)
        
        response = self.client.get('/api/admin/analytics/daily-summary/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class RetentionPurgeTests(TestCase):
    """Test cases for retention purge command."""
    
    def setUp(self):
        """Create old and recent events."""
        # Old events (100 days ago)
        old_date = timezone.now() - timedelta(days=100)
        Event.objects.create(
            event_type='page_view',
            created_at=old_date
        )
        Event.objects.create(
            event_type='booking_created',
            created_at=old_date
        )
        
        # Recent events
        Event.objects.create(event_type='page_view')
        Event.objects.create(event_type='job_apply')
    
    @override_settings(ANALYTICS_RETENTION_DAYS=90)
    def test_retention_purge_command_deletes_old_events(self):
        """Test that purge command deletes events older than retention period."""
        # Should have 4 events initially
        self.assertEqual(Event.objects.count(), 4)
        
        # Run purge
        call_command('analytics_purge_older_than')
        
        # Should have 2 events remaining (recent ones)
        self.assertEqual(Event.objects.count(), 2)
        self.assertFalse(
            Event.objects.filter(
                created_at__lt=timezone.now() - timedelta(days=90)
            ).exists()
        )
    
    def test_dry_run_does_not_delete(self):
        """Test that dry run doesn't actually delete events."""
        initial_count = Event.objects.count()
        
        # Run with --dry-run
        call_command('analytics_purge_older_than', dry_run=True)
        
        # Count should be unchanged
        self.assertEqual(Event.objects.count(), initial_count)


class EventModelTests(TestCase):
    """Test cases for Event model."""
    
    def test_event_string_representation(self):
        """Test __str__ method."""
        event = Event.objects.create(
            event_type='page_view',
            anonymous_id='anon-123'
        )
        
        self.assertIn('page_view', str(event))
        self.assertIn('anon-123', str(event))
    
    def test_event_with_user(self):
        """Test event creation with user."""
        user = User.objects.create_user(phone="+919900000001")
        event = Event.objects.create(
            user=user,
            event_type='booking_created'
        )
        
        self.assertEqual(event.user, user)
        self.assertIn(str(user.id), str(event))
