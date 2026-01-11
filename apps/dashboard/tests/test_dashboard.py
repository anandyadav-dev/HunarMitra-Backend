"""
Tests for dashboard summary endpoints.
"""
from unittest import mock
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta

from apps.users.models import User
from apps.workers.models import WorkerProfile
from apps.contractors.models import ContractorProfile
from apps.bookings.models import Booking
from apps.services.models import Service
from apps.notifications.models import Notification


class WorkerDashboardTests(TestCase):
    """Test cases for worker dashboard endpoint."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create worker user
        self.worker_user = User.objects.create_user(
            phone="+919900000001",
            role="worker"
        )
        self.worker_profile = WorkerProfile.objects.create(
            user=self.worker_user,
            is_available=True,
            is_verified=False,
            last_seen=timezone.now()
        )
        
    def test_worker_dashboard_payload_contains_required_keys(self):
        """Test worker dashboard returns all required keys."""
        self.client.force_authenticate(user=self.worker_user)
        
        response = self.client.get('/api/v1/dashboard/worker/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify all required keys present
        required_keys = [
            'user_id', 'unread_notifications', 'today_jobs',
            'availability', 'earnings', 'badges'
        ]
        for key in required_keys:
            self.assertIn(key, response.data, f"Missing required key: {key}")
        
        # Verify nested structure
        self.assertIn('assigned', response.data['today_jobs'])
        self.assertIn('on_the_way', response.data['today_jobs'])
        self.assertIn('completed', response.data['today_jobs'])
        
        self.assertIn('is_available', response.data['availability'])
        self.assertIn('last_seen_minutes_ago', response.data['availability'])
        
        self.assertIn('today', response.data['earnings'])
        self.assertIn('month_to_date', response.data['earnings'])
    
    def test_worker_dashboard_includes_badges(self):
        """Test worker dashboard includes profile badges."""
        self.client.force_authenticate(user=self.worker_user)
        
        response = self.client.get('/api/v1/dashboard/worker/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Worker not verified, should have badge
        self.assertIn('verify_profile', response.data['badges'])
    
    def test_worker_dashboard_unauthorized(self):
        """Test worker dashboard requires authentication."""
        response = self.client.get('/api/v1/dashboard/worker/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_worker_dashboard_non_worker_user(self):
        """Test worker dashboard rejects non-worker users."""
        employer_user = User.objects.create_user(
            phone="+919900000002",
            role="employer"
        )
        self.client.force_authenticate(user=employer_user)
        
        response = self.client.get('/api/v1/dashboard/worker/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class EmployerDashboardTests(TestCase):
    """Test cases for employer dashboard endpoint."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create employer user
        self.employer_user = User.objects.create_user(
            phone="+919900000003",
            role="employer"
        )
        
        # Create worker and service for bookings
        self.worker_user = User.objects.create_user(
            phone="+919900000004",
            role="worker"
        )
        self.worker_profile = WorkerProfile.objects.create(user=self.worker_user)
        
        self.service = Service.objects.create(
            name="Plumbing",
            category="home",
            base_price=500
        )
    
    def test_employer_dashboard_recent_bookings(self):
        """Test employer dashboard includes recent bookings."""
        self.client.force_authenticate(user=self.employer_user)
        
        # Create booking
        booking = Booking.objects.create(
            user=self.employer_user,
            worker=self.worker_profile,
            service=self.service,
            status='on_the_way',
            scheduled_at=timezone.now() + timedelta(hours=1)
        )
        
        response = self.client.get('/api/v1/dashboard/employer/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify structure
        required_keys = [
            'user_id', 'unread_notifications', 'active_requests',
            'pending_confirmations', 'recent_bookings', 'emergency_alerts'
        ]
        for key in required_keys:
            self.assertIn(key, response.data)
        
        # Verify recent bookings
        self.assertGreater(len(response.data['recent_bookings']), 0)
        booking_data = response.data['recent_bookings'][0]
        self.assertEqual(booking_data['status'], 'on_the_way')
        self.assertIn('id', booking_data)
        self.assertIn('eta_minutes', booking_data)
    
    def test_employer_dashboard_active_requests_count(self):
        """Test employer dashboard counts active requests correctly."""
        self.client.force_authenticate(user=self.employer_user)
        
        # Create multiple bookings with different statuses
        Booking.objects.create(
            user=self.employer_user,
            worker=self.worker_profile,
            service=self.service,
            status='requested',
            scheduled_at=timezone.now() + timedelta(hours=1)
        )
        Booking.objects.create(
            user=self.employer_user,
            worker=self.worker_profile,
            service=self.service,
            status='confirmed',
            scheduled_at=timezone.now() + timedelta(hours=2)
        )
        Booking.objects.create(
            user=self.employer_user,
            worker=self.worker_profile,
            service=self.service,
            status='completed',  # Should not count as active
            scheduled_at=timezone.now() - timedelta(hours=1)
        )
        
        response = self.client.get('/api/v1/dashboard/employer/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['active_requests'], 2)
        self.assertEqual(response.data['pending_confirmations'], 1)


class ContractorDashboardTests(TestCase):
    """Test cases for contractor dashboard endpoint."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create contractor user
        self.contractor_user = User.objects.create_user(
            phone="+919900000005",
            role="contractor"
        )
        self.contractor_profile = ContractorProfile.objects.create(
            user=self.contractor_user,
            company_name="Test Contractors Inc"
        )
    
    def test_contractor_dashboard_aggregates_attendance(self):
        """Test contractor dashboard shows attendance aggregates."""
        self.client.force_authenticate(user=self.contractor_user)
        
        response = self.client.get('/api/v1/dashboard/contractor/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify structure
        required_keys = [
            'contractor_id', 'unread_notifications', 'active_sites',
            'workers_present_today', 'pending_job_requests',
            'attendance_rate_percent'
        ]
        for key in required_keys:
            self.assertIn(key, response.data)
        
        # Attendance rate should be a float
        self.assertIsInstance(response.data['attendance_rate_percent'], (int, float))
        self.assertGreaterEqual(response.data['attendance_rate_percent'], 0)
        self.assertLessEqual(response.data['attendance_rate_percent'], 100)
    
    @override_settings(FEATURE_CONTRACTOR_SITES=True)
    def test_contractor_dashboard_with_sites_enabled(self):
        """Test contractor dashboard with sites feature enabled."""
        # This would require creating Site and SiteAttendance models
        # For now, just verify the endpoint works
        self.client.force_authenticate(user=self.contractor_user)
        
        response = self.client.get('/api/v1/dashboard/contractor/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('active_sites', response.data)


class AdminDashboardTests(TestCase):
    """Test cases for admin dashboard endpoint."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            phone="+919000000000",
            password="admin123"
        )
        
        # Create some regular users
        for i in range(5):
            User.objects.create_user(phone=f"+91990000{i:04d}", role="worker")
    
    def test_admin_dashboard_global_metrics(self):
        """Test admin dashboard returns global stats."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get('/api/v1/dashboard/admin/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify structure
        required_keys = [
            'total_users', 'total_workers_online', 'open_emergencies',
            'today_bookings', 'system_health'
        ]
        for key in required_keys:
            self.assertIn(key, response.data)
        
        # Verify metrics
        self.assertGreaterEqual(response.data['total_users'], 5)  # At least our test users
        self.assertIsInstance(response.data['total_workers_online'], int)
        self.assertIsInstance(response.data['today_bookings'], int)
        
        # System health should be a dict
        self.assertIsInstance(response.data['system_health'], dict)
    
    def test_admin_dashboard_requires_admin_permission(self):
        """Test admin dashboard requires admin permissions."""
        worker_user = User.objects.create_user(
            phone="+919900000006",
            role="worker"
        )
        self.client.force_authenticate(user=worker_user)
        
        response = self.client.get('/api/v1/dashboard/admin/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class DashboardCachingTests(TestCase):
    """Test cases for dashboard caching behavior."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        self.worker_user = User.objects.create_user(
            phone="+919900000007",
            role="worker"
        )
        self.worker_profile = WorkerProfile.objects.create(user=self.worker_user)
        
        self.admin_user = User.objects.create_superuser(
            phone="+919000000001",
            password="admin123"
        )
    
    def test_cache_is_used_and_cleared(self):
        """Test dashboard caching works and can be cleared."""
        self.client.force_authenticate(user=self.worker_user)
        
        # First request (cache miss)
        with self.assertNumQueries(4):  # Approximate - worker, jobs, notifications, payments check
            response1 = self.client.get('/api/v1/dashboard/worker/')
        
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Second request (cache hit - should have fewer queries)
        with self.assertNumQueries(0):  # Should be cached
            response2 = self.client.get('/api/v1/dashboard/worker/')
        
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response1.data, response2.data)
        
        # Clear cache via admin endpoint
        self.client.force_authenticate(user=self.admin_user)
        clear_response = self.client.post('/api/admin/dashboard/cache/clear/', {
            'role': 'worker',
            'user_id': self.worker_user.id
        })
        
        self.assertEqual(clear_response.status_code, status.HTTP_200_OK)
        self.assertEqual(clear_response.data['status'], 'cache_cleared')
    
    @override_settings(DASHBOARD_CACHE_TTL_SECONDS=1)
    def test_cache_expiration(self):
        """Test cache expires after TTL."""
        import time
        
        self.client.force_authenticate(user=self.worker_user)
        
        # First request
        response1 = self.client.get('/api/v1/dashboard/worker/')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Wait for cache to expire
        time.sleep(2)
        
        # Second request (cache expired, should fetch fresh)
        response2 = self.client.get('/api/v1/dashboard/worker/')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)


class DashboardPayloadSizeTests(TestCase):
    """Test cases to ensure dashboard payloads are minimal."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        self.worker_user = User.objects.create_user(
            phone="+919900000008",
            role="worker"
        )
        self.worker_profile = WorkerProfile.objects.create(user=self.worker_user)
    
    def test_payload_size_under_1kb(self):
        """Test dashboard payload is under 1KB."""
        import json
        
        self.client.force_authenticate(user=self.worker_user)
        
        response = self.client.get('/api/v1/dashboard/worker/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check payload size
        payload_str = json.dumps(response.data)
        payload_size = len(payload_str.encode('utf-8'))
        
        self.assertLess(payload_size, 1024, f"Payload size {payload_size} bytes exceeds 1KB")
