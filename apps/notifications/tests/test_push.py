"""
Tests for push notification system - Device registration and FCM delivery.
"""
from unittest import mock
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.users.models import User
from apps.notifications.models import Device, Notification, OutgoingPush
from apps.notifications.tasks import send_push_batch, enqueue_push_for_notification


class DeviceRegistrationTests(TestCase):
    """Test cases for device registration."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(phone="+919900000001", role="worker")
        
    def test_register_device_creates_new_device(self):
        """Test device registration creates a new device."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/api/notifications/devices/register/', {
            'registration_token': 'test-fcm-token-123',
            'platform': 'android',
            'metadata': {'model': 'Pixel 5', 'os_version': '12'}
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['platform'], 'android')
        self.assertEqual(response.data['user'], self.user.id)
        
        # Verify database
        device = Device.objects.get(registration_token='test-fcm-token-123')
        self.assertEqual(device.user, self.user)
        self.assertTrue(device.is_active)
    
    def test_register_device_upsert_behavior(self):
        """Test registering same token updates existing device."""
        self.client.force_authenticate(user=self.user)
        
        # First registration
        response1 = self.client.post('/api/notifications/devices/register/', {
            'registration_token': 'test-token',
            'platform': 'android'
        })
        device_id = response1.data['id']
        
        # Second registration with same token
        response2 = self.client.post('/api/notifications/devices/register/', {
            'registration_token': 'test-token',
            'platform': 'ios',  # Changed platform
            'metadata': {'new': 'data'}
        })
        
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data['id'], device_id)  # Same device
        self.assertEqual(response2.data['platform'], 'ios')  # Updated
        
        # Verify only one device exists
        self.assertEqual(Device.objects.filter(registration_token='test-token').count(), 1)
    
    def test_unregister_device_deactivates(self):
        """Test device unregistration marks device as inactive."""
        self.client.force_authenticate(user=self.user)
        
        # Register device
        device = Device.objects.create(
            user=self.user,
            platform='android',
            registration_token='test-token',
            is_active=True
        )
        
        # Unregister
        response = self.client.post('/api/notifications/devices/unregister/', {
            'registration_token': 'test-token'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'unregistered')
        
        # Verify deactivated
        device.refresh_from_db()
        self.assertFalse(device.is_active)
    
    def test_list_user_devices(self):
        """Test listing user's registered devices."""
        self.client.force_authenticate(user=self.user)
        
        # Create devices
        Device.objects.create(user=self.user, platform='android', registration_token='token1', is_active=True)
        Device.objects.create(user=self.user, platform='ios', registration_token='token2', is_active=True)
        
        # Other user's device
        other_user = User.objects.create_user(phone="+919900000002")
        Device.objects.create(user=other_user, platform='android', registration_token='token3', is_active=True)
        
        response = self.client.get('/api/notifications/devices/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Only user's devices


class PushEnqueueTests(TestCase):
    """Test cases for push notification enqueueing."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(phone="+919900000001")
        self.device = Device.objects.create(
            user=self.user,
            platform='android',
            registration_token='test-token',
            is_active=True
        )
    
    @override_settings(FCM_ENABLED=True)
    @mock.patch('apps.notifications.tasks.send_push_batch.delay')
    def test_notification_creation_enqueues_push(self, mock_delay):
        """Test creating notification with channel='push' enqueues OutgoingPush."""
        notification = Notification.objects.create(
            user=self.user,
            title='Test Push',
            message='Test message',
            channel=Notification.CHANNEL_PUSH
        )
        
        # Verify OutgoingPush created
        push = OutgoingPush.objects.filter(notification=notification).first()
        self.assertIsNotNone(push)
        self.assertEqual(push.device, self.device)
        self.assertEqual(push.status, OutgoingPush.STATUS_QUEUED)
        self.assertEqual(push.payload['title'], 'Test Push')
        
        # Verify Celery task called
        mock_delay.assert_called_once()
        call_args = mock_delay.call_args[0][0]
        self.assertIn(push.id, call_args)
    
    @override_settings(FCM_ENABLED=False)
    @mock.patch('apps.notifications.tasks.send_push_batch.delay')
    def test_fcm_disabled_skips_enqueue(self, mock_delay):
        """Test FCM_ENABLED=false skips push enqueueing."""
        notification = Notification.objects.create(
            user=self.user,
            title='Test',
            message='Message',
            channel=Notification.CHANNEL_PUSH
        )
        
        # Verify no OutgoingPush created
        self.assertEqual(OutgoingPush.objects.filter(notification=notification).count(), 0)
        mock_delay.assert_not_called()
    
    @override_settings(FCM_ENABLED=True)
    def test_in_app_channel_does_not_enqueue_push(self):
        """Test channel='in_app' does not create push."""
        notification = Notification.objects.create(
            user=self.user,
            title='Test',
            message='Message',
            channel=Notification.CHANNEL_IN_APP
        )
        
        self.assertEqual(OutgoingPush.objects.filter(notification=notification).count(), 0)


class FCMDeliveryTests(TestCase):
    """Test cases for FCM push delivery task."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(phone="+919900000001")
        self.device = Device.objects.create(
            user=self.user,
            platform='android',
            registration_token='test-token',
            is_active=True
        )
        self.notification = Notification.objects.create(
            user=self.user,
            title='Test',
            message='Message'
        )
        self.push = OutgoingPush.objects.create(
            notification=self.notification,
            device=self.device,
            payload={'title': 'Test', 'message': 'Message', 'data': {}},
            status=OutgoingPush.STATUS_QUEUED
        )
    
    @override_settings(FCM_ENABLED=True, FCM_SERVER_KEY='test-key')
    @mock.patch('apps.notifications.tasks.requests.post')
    def test_send_push_batch_success(self, mock_post):
        """Test successful FCM delivery marks push as sent."""
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'success': 1, 'failure': 0}
        mock_post.return_value.content = b'{}'
        
        result = send_push_batch([self.push.id])
        
        self.assertEqual(result['sent'], 1)
        self.assertEqual(result['failed'], 0)
        
        self.push.refresh_from_db()
        self.assertEqual(self.push.status, OutgoingPush.STATUS_SENT)
        self.assertEqual(self.push.attempts, 1)
        self.assertIsNotNone(self.push.last_attempt_at)
    
    @override_settings(FCM_ENABLED=True, FCM_SERVER_KEY='test-key')
    @mock.patch('apps.notifications.tasks.requests.post')
    def test_invalid_token_deactivates_device(self, mock_post):
        """Test 400/invalid token response deactivates device."""
        mock_post.return_value.status_code = 400
        mock_post.return_value.json.return_value = {'error': 'InvalidRegistration'}
        mock_post.return_value.content = b'{}'
        
        send_push_batch([self.push.id])
        
        self.push.refresh_from_db()
        self.assertEqual(self.push.status, OutgoingPush.STATUS_FAILED)
        
        self.device.refresh_from_db()
        self.assertFalse(self.device.is_active)
    
    @override_settings(FCM_ENABLED=True, FCM_SERVER_KEY='test-key', FCM_MAX_RETRIES=2)
    @mock.patch('apps.notifications.tasks.send_push_batch.retry')
    @mock.patch('apps.notifications.tasks.requests.post')
    def test_transient_failure_retries(self, mock_post, mock_retry):
        """Test 5xx error triggers retry."""
        mock_post.return_value.status_code = 503
        mock_post.return_value.json.return_value = {}
        mock_post.return_value.content = b'{}'
        mock_retry.side_effect = Exception("Retry triggered")
        
        with self.assertRaises(Exception):
            send_push_batch([self.push.id])
        
        self.push.refresh_from_db()
        self.assertEqual(self.push.attempts, 1)
        mock_retry.assert_called_once()
    
    @override_settings(FCM_ENABLED=False)
    def test_fcm_disabled_skips_send(self):
        """Test FCM_ENABLED=false skips actual sending."""
        result = send_push_batch([self.push.id])
        
        self.assertEqual(result['status'], 'skipped')
        self.assertEqual(result['reason'], 'FCM_ENABLED=False')
        
        self.push.refresh_from_db()
        self.assertEqual(self.push.status, OutgoingPush.STATUS_QUEUED)  # Unchanged
    
    @override_settings(FCM_ENABLED=True, FCM_SERVER_KEY='test-key')
    def test_inactive_device_skipped(self):
        """Test push to inactive device is skipped."""
        self.device.is_active = False
        self.device.save()
        
        result = send_push_batch([self.push.id])
        
        self.assertEqual(result['skipped'], 1)
        self.push.refresh_from_db()
        self.assertEqual(self.push.status, OutgoingPush.STATUS_FAILED)


class AdminActionsTests(TestCase):
    """Test admin actions for device and push management."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(phone="+919900000001")
        self.admin_user = User.objects.create_superuser(phone="+919000000000", password='admin123')
        
    def test_requeue_failed_pushes(self):
        """Test admin can requeue failed pushes."""
        device = Device.objects.create(user=self.user, platform='android', registration_token='token', is_active=True)
        notification = Notification.objects.create(user=self.user, title='Test', message='Msg')
        
        # Create failed push
        push = OutgoingPush.objects.create(
            notification=notification,
            device=device,
            payload={},
            status=OutgoingPush.STATUS_FAILED,
            attempts=3
        )
        
        # Simulate admin requeue (would normally be done via admin interface)
        with mock.patch('apps.notifications.tasks.send_push_batch.delay') as mock_delay:
            OutgoingPush.objects.filter(id=push.id).update(
                status=OutgoingPush.STATUS_QUEUED,
                attempts=0
            )
            send_push_batch.delay([push.id])
            
            mock_delay.assert_called_once_with([push.id])
        
        push.refresh_from_db()
        self.assertEqual(push.status, OutgoingPush.STATUS_QUEUED)
        self.assertEqual(push.attempts, 0)
