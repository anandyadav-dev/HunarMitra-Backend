"""
Tests for Contractor Dashboard APIs.
"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from django.urls import reverse

from apps.contractors.models import ContractorProfile
from apps.attendance.models import AttendanceKiosk, AttendanceLog
from apps.jobs.models import Job
from apps.services.models import Service

User = get_user_model()


@pytest.mark.django_db
class TestContractorRegistration:
    """Test contractor registration API."""
    
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            phone="+919900001111",
            role="contractor"
        )
    
    def test_contractor_registration_success(self):
        """Test successful contractor profile creation."""
        url = reverse('contractor-list')
        self.client.force_authenticate(user=self.user)
        
        data = {
            'company_name': 'Test Construction Co.',
            'license_number': 'LIC123456',
            'gst_number': '29ABCDE1234F1Z5',
            'city': 'Bangalore',
            'state': 'Karnataka'
        }
        
        response = self.client.post(url, data)
        
        assert response.status_code == 201
        assert response.data['company_name'] == 'Test Construction Co.'
        assert response.data['phone'] == '+919900001111'
        assert ContractorProfile.objects.filter(user=self.user).exists()
    
    def test_contractor_duplicate_registration_fails(self):
        """Test that duplicate registration fails."""
        ContractorProfile.objects.create(
            user=self.user,
            company_name='Existing Co.'
        )
        
        url = reverse('contractor-list')
        self.client.force_authenticate(user=self.user)
        
        data = {'company_name': 'New Co.'}
        response = self.client.post(url, data)
        
        # Should fail due to unique constraint on user
        assert response.status_code == 400


@pytest.mark.django_db
class TestContractorDashboard:
    """Test contractor dashboard summary API."""
    
    def setup_method(self):
        self.client = APIClient()
        
        # Create contractor
        self.contractor_user = User.objects.create_user(
            phone="+919900002222",
            role="contractor"
        )
        self.contractor = ContractorProfile.objects.create(
            user=self.contractor_user,
            company_name="Dashboard Test Co."
        )
        
        # Create service for jobs
        self.service = Service.objects.create(
            name="Construction",
            title_en="Construction",
            is_active=True
        )
        
        # Create active sites (kiosks)
        self.kiosk1 = AttendanceKiosk.objects.create(
            contractor=self.contractor,
            device_uuid="KIOSK001",
            location_name="Site A",
            is_active=True
        )
        self.kiosk2 = AttendanceKiosk.objects.create(
            contractor=self.contractor,
            device_uuid="KIOSK002",
            location_name="Site B",
            is_active=True
        )
        
        # Create inactive kiosk (should not be counted)
        self.kiosk3 = AttendanceKiosk.objects.create(
            contractor=self.contractor,
            device_uuid="KIOSK003",
            location_name="Site C",
            is_active=False
        )
        
        # Create workers
        self.worker1 = User.objects.create_user(phone="+919900003333", role="worker")
        self.worker2 = User.objects.create_user(phone="+919900004444", role="worker")
        
        # Create attendance logs for today
        today = timezone.now()
        AttendanceLog.objects.create(worker=self.worker1, kiosk=self.kiosk1, check_in=today)
        AttendanceLog.objects.create(worker=self.worker2, kiosk=self.kiosk2, check_in=today)
        
        # Create jobs
        self.job_poster = User.objects.create_user(phone="+919900005555", role="customer")
        
        # Open job
        Job.objects.create(
            poster=self.job_poster,
            contractor=self.contractor,
            service=self.service,
            title="Job 1",
            description="Test job",
            status="open"
        )
        
        # Assigned job
        Job.objects.create(
            poster=self.job_poster,
            contractor=self.contractor,
            service=self.service,
            title="Job 2",
            description="Test job",
            status="assigned"
        )
        
        # Completed job (should not be counted)
        Job.objects.create(
            poster=self.job_poster,
            contractor=self.contractor,
            service=self.service,
            title="Job 3",
            description="Test job",
            status="completed"
        )
    
    def test_dashboard_returns_correct_metrics(self):
        """Test that dashboard API returns correct computed metrics."""
        url = reverse('contractor-dashboard', kwargs={'pk': self.contractor.id})
        self.client.force_authenticate(user=self.contractor_user)
        
        response = self.client.get(url)
        
        assert response.status_code == 200
        assert response.data['active_sites'] == 2  # kiosk1 and kiosk2 (kiosk3 is inactive)
        assert response.data['workers_present_today'] == 2  # worker1 and worker2
        assert response.data['pending_jobs'] == 2  # open and assigned jobs
    
    def test_dashboard_requires_authentication(self):
        """Test that dashboard requires authentication."""
        url = reverse('contractor-dashboard', kwargs={'pk': self.contractor.id})
        
        response = self.client.get(url)
        
        assert response.status_code == 401
    
    def test_dashboard_with_no_data(self):
        """Test dashboard with contractor having no sites/jobs."""
        # Create new contractor with no data
        new_user = User.objects.create_user(phone="+919900006666", role="contractor")
        new_contractor = ContractorProfile.objects.create(
            user=new_user,
            company_name="Empty Co."
        )
        
        url = reverse('contractor-dashboard', kwargs={'pk': new_contractor.id})
        self.client.force_authenticate(user=new_user)
        
        response = self.client.get(url)
        
        assert response.status_code == 200
        assert response.data['active_sites'] == 0
        assert response.data['workers_present_today'] == 0
        assert response.data['pending_jobs'] == 0
