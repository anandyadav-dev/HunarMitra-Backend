"""
Tests for Emergency app - emergency request system.
"""
from datetime import timedelta
from unittest import mock
from django.utils import timezone
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.users.models import User
from apps.workers.models import WorkerProfile
from apps.services.models import Service
from apps.emergency.models import EmergencyRequest, EmergencyDispatchLog


class EmergencyRequestTests(TestCase):
    """Test cases for emergency request system."""
    
    def setUp(self):
        """Set up test data."""
        # Create test service
        self.service = Service.objects.create(
            name="Emergency Plumbing",
            slug="emergency-plumbing",
            category="home_services"
        )
        
        # Create worker
        self.worker_user = User.objects.create_user(
            phone="+919876543210",
            role="worker"
        )
        self.worker = WorkerProfile.objects.create(
            user=self.worker_user,
            availability_status="available",
            is_available=True,
            latitude=26.8467,
            longitude=80.9462
        )
        self.worker.services.add(self.service)
        
        # Create another worker
        self.worker2_user = User.objects.create_user(
            phone="+919876543211",
            role="worker"
        )
        self.worker2 = WorkerProfile.objects.create(
            user=self.worker2_user,
            is_available=True,
            latitude=26.8500,
            longitude=80.9500
        )
        self.worker2.services.add(self.service)
        
        # API clients
        self.client = APIClient()
        self.worker_client = APIClient()
        self.worker_client.force_authenticate(user=self.worker_user)
    
    def test_create_emergency_request(self):
        """Test creating an emergency request."""
        response = self.client.post('/api/v1/emergency/requests/', {
            'contact_phone': '+919900000001',
            'location': {'lat': 26.8467, 'lng': 80.9462},
            'address': 'Test Address, Lucknow',
            'service_id': str(self.service.id),
            'urgency_level': 'high'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['status'], 'open')
    
    @mock.patch('apps.emergency.rate_limit.cache')
    def test_create_emergency_request_rate_limit(self, mock_cache):
        """Test rate limiting on emergency requests."""
        # Mock cache to simulate exceeded limit
        mock_cache.get.return_value = 2  # Exceeds limit of 1
        
        response = self.client.post('/api/v1/emergency/requests/', {
            'contact_phone': '+919900000001',
            'location': {'lat': 26.8467, 'lng': 80.9462},
            'address': 'Test Address, Lucknow',
            'urgency_level': 'high'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('Rate limit exceeded', response.data['detail'])
    
    @mock.patch('apps.emergency.tasks.process_emergency_dispatch.delay')
    def test_auto_assign_dispatch_flow_mocked(self, mock_dispatch):
        """Test auto-dispatch queuing (mocked)."""
        with self.settings(EMERGENCY_AUTO_ASSIGN=True):
            response = self.client.post('/api/v1/emergency/requests/', {
                'contact_phone': '+919900000001',
                'location': {'lat': 26.8467, 'lng': 80.9462},
                'address': 'Test Address, Lucknow',
                'urgency_level': 'high'
            }, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data['dispatch_status'], 'queued')
            
            # Verify Celery task was called
            mock_dispatch.assert_called_once()
    
    def test_worker_accept_assigns_emergency(self):
        """Test worker accepting emergency request."""
        # Create emergency
        emergency = EmergencyRequest.objects.create(
            contact_phone='+919900000001',
            location_lat=26.8467,
            location_lng=80.9462,
            address_text='Test Address',
            urgency_level='high',
            status=EmergencyRequest.STATUS_OPEN
        )
        
        # Create dispatch log (simulate notification)
        EmergencyDispatchLog.objects.create(
            emergency=emergency,
            worker=self.worker,
            status=EmergencyDispatchLog.STATUS_NOTIFIED
        )
        
        # Worker accepts
        response = self.worker_client.post(
            f'/api/v1/emergency/requests/{emergency.id}/accept/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'accepted')
        self.assertEqual(str(response.data['assigned_worker']), str(self.worker.id))
        
        # Verify dispatch log updated
        log = EmergencyDispatchLog.objects.get(emergency=emergency, worker=self.worker)
        self.assertEqual(log.status, EmergencyDispatchLog.STATUS_ACCEPTED)
        self.assertIsNotNone(log.response_time)
    
    def test_worker_decline_logs_response(self):
        """Test worker declining emergency request."""
        emergency = EmergencyRequest.objects.create(
            contact_phone='+919900000001',
            location_lat=26.8467,
            location_lng=80.9462,
            address_text='Test Address',
            urgency_level='high'
        )
        
        EmergencyDispatchLog.objects.create(
            emergency=emergency,
            worker=self.worker,
            status=EmergencyDispatchLog.STATUS_NOTIFIED
        )
        
        response = self.worker_client.post(
            f'/api/v1/emergency/requests/{emergency.id}/decline/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'declined')
        
        # Verify log updated
        log = EmergencyDispatchLog.objects.get(emergency=emergency, worker=self.worker)
        self.assertEqual(log.status, EmergencyDispatchLog.STATUS_DECLINED)
    
    def test_admin_can_list_and_update_status(self):
        """Test admin can list emergencies and update status."""
        admin_user = User.objects.create_superuser(
            phone='+919000000000',
            password='admin123'
        )
        admin_client = APIClient()
        admin_client.force_authenticate(user=admin_user)
        
        emergency = EmergencyRequest.objects.create(
            contact_phone='+919900000001',
            location_lat=26.8467,
            location_lng=80.9462,
            address_text='Test Address',
            status=EmergencyRequest.STATUS_OPEN
        )
        
        # List emergencies
        response = admin_client.get('/api/v1/emergency/requests/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Update status
        response = admin_client.patch(
            f'/api/v1/emergency/requests/{emergency.id}/status/',
            {'status': 'resolved', 'notes': 'Resolved by admin'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'resolved')
        
        emergency.refresh_from_db()
        self.assertEqual(emergency.status, 'resolved')
