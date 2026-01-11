"""
Tests for Kiosk Attendance APIs.
"""
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.test import override_settings
from rest_framework.test import APIClient
from django.urls import reverse

from apps.attendance.models import Attendance, AttendanceKiosk

User = get_user_model()


@pytest.mark.django_db
class TestKioskAttendance:
    """Test kiosk attendance marking API."""
    
    def setup_method(self):
        self.client = APIClient()
        
        # Create worker
        self.worker = User.objects.create_user(
            phone="+919900001111",
            role="worker"
        )
        
        # Create kiosk
        self.kiosk = AttendanceKiosk.objects.create(
            device_uuid="KIOSK_001",
            location_name="Test Site A",
            is_active=True
        )
    
    @override_settings(FEATURE_BIOMETRIC_STUB=True)
    def test_attendance_creation_when_flag_enabled(self):
        """Test attendance is created when feature flag is enabled."""
        url = reverse('attendance-kiosk')
        
        data = {
            'worker_id': str(self.worker.id),
            'device_id': 'KIOSK_001',
            'kiosk_id': str(self.kiosk.id)
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert response.data['worker'] == str(self.worker.id)
        assert response.data['method'] == 'stub'
        assert response.data['device_id'] == 'KIOSK_001'
        assert Attendance.objects.filter(worker=self.worker).exists()
    
    @override_settings(FEATURE_BIOMETRIC_STUB=False)
    def test_attendance_rejected_when_flag_disabled(self):
        """Test attendance is rejected when feature flag is disabled."""
        url = reverse('attendance-kiosk')
        
        data = {
            'worker_id': str(self.worker.id),
            'device_id': 'KIOSK_001'
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == 403
        assert 'Biometric stub is not enabled' in response.data['detail']
        assert not Attendance.objects.filter(worker=self.worker).exists()
    
    @override_settings(FEATURE_BIOMETRIC_STUB=True)
    def test_duplicate_attendance_same_day_updates(self):
        """Test that marking attendance twice on same day updates, doesn't duplicate."""
        url = reverse('attendance-kiosk')
        
        data = {
            'worker_id': str(self.worker.id),
            'device_id': 'KIOSK_001',
            'kiosk_id': str(self.kiosk.id)
        }
        
        # First attendance
        response1 = self.client.post(url, data, format='json')
        assert response1.status_code == 201
        
        # Second attendance same day
        data['device_id'] = 'KIOSK_002'
        response2 = self.client.post(url, data, format='json')
        assert response2.status_code == 200  # Updated, not created
        
        # Should only have one attendance record for today
        today = timezone.now().date()
        count = Attendance.objects.filter(
            worker=self.worker,
            date=today
        ).count()
        assert count == 1
        
        # Device ID should be updated
        attendance = Attendance.objects.get(worker=self.worker, date=today)
        assert attendance.device_id == 'KIOSK_002'
    
    @override_settings(FEATURE_BIOMETRIC_STUB=True)
    def test_attendance_without_kiosk(self):
        """Test attendance can be marked without kiosk (optional)."""
        url = reverse('attendance-kiosk')
        
        data = {
            'worker_id': str(self.worker.id),
            'device_id': 'MOBILE_APP'
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert response.data['kiosk'] is None
        assert response.data['device_id'] == 'MOBILE_APP'
    
    @override_settings(FEATURE_BIOMETRIC_STUB=True)
    def test_attendance_invalid_worker(self):
        """Test attendance fails with invalid worker ID."""
        url = reverse('attendance-kiosk')
        
        data = {
            'worker_id': '00000000-0000-0000-0000-000000000000',
            'device_id': 'KIOSK_001'
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == 404
        assert 'Worker not found' in response.data['detail']


@pytest.mark.django_db
class TestSiteAttendance:
    """Test site-wise attendance query API."""
    
    def setup_method(self):
        self.client = APIClient()
        
        # Create auth user
        self.auth_user = User.objects.create_user(
            phone="+919900009999",
            role="contractor"
        )
        
        # Create kiosk
        self.kiosk = AttendanceKiosk.objects.create(
            device_uuid="KIOSK_TEST",
            location_name="Test Site",
            is_active=True
        )
        
        # Create workers
        self.worker1 = User.objects.create_user(phone="+919900001111", role="worker")
        self.worker2 = User.objects.create_user(phone="+919900002222", role="worker")
        self.worker3 = User.objects.create_user(phone="+919900003333", role="worker")
        
        # Create attendance for today
        today = timezone.now().date()
        Attendance.objects.create(
            worker=self.worker1,
            kiosk=self.kiosk,
            date=today,
            method='stub'
        )
        Attendance.objects.create(
            worker=self.worker2,
            kiosk=self.kiosk,
            date=today,
            method='stub'
        )
        
        # Create attendance for yesterday
        from datetime import timedelta
        yesterday = today - timedelta(days=1)
        Attendance.objects.create(
            worker=self.worker3,
            kiosk=self.kiosk,
            date=yesterday,
            method='stub'
        )
    
    def test_site_attendance_query_today(self):
        """Test querying attendance for a site returns today's workers."""
        url = reverse('attendance-site', kwargs={'kiosk_id': self.kiosk.id})
        self.client.force_authenticate(user=self.auth_user)
        
        response = self.client.get(url)
        
        assert response.status_code == 200
        assert len(response.data) == 2  # Only today's attendance
        worker_ids = [a['worker'] for a in response.data]
        assert str(self.worker1.id) in worker_ids
        assert str(self.worker2.id) in worker_ids
        assert str(self.worker3.id) not in worker_ids  # Yesterday's worker
    
    def test_site_attendance_query_specific_date(self):
        """Test querying attendance for a specific date."""
        from datetime import timedelta
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        url = reverse('attendance-site', kwargs={'kiosk_id': self.kiosk.id})
        self.client.force_authenticate(user=self.auth_user)
        
        response = self.client.get(url, {'date': yesterday.strftime('%Y-%m-%d')})
        
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['worker'] == str(self.worker3.id)
    
    def test_site_attendance_requires_authentication(self):
        """Test that site attendance query requires authentication."""
        url = reverse('attendance-site', kwargs={'kiosk_id': self.kiosk.id})
        
        response = self.client.get(url)
        
        assert response.status_code == 401
    
    def test_site_attendance_invalid_date_format(self):
        """Test that invalid date format returns empty results."""
        url = reverse('attendance-site', kwargs={'kiosk_id': self.kiosk.id})
        self.client.force_authenticate(user=self.auth_user)
        
        response = self.client.get(url, {'date': 'invalid-date'})
        
        assert response.status_code == 200
        assert len(response.data) == 0  # Empty queryset for invalid date
