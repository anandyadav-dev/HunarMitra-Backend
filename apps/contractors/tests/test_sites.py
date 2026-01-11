"""
Tests for Contractor Site Management.
"""
from datetime import timedelta
from django.utils import timezone
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.users.models import User
from apps.contractors.models import ContractorProfile, Site, SiteAssignment, SiteAttendance
from apps.workers.models import WorkerProfile


class SiteManagementTests(TestCase):
    """Test cases for site management APIs."""
    
    def setUp(self):
        """Set up test data."""
        # Create contractor user and profile
        self.contractor_user = User.objects.create_user(
            phone="+919876543210",
            role="contractor",
            first_name="Test",
            last_name="Contractor"
        )
        self.contractor_profile = ContractorProfile.objects.create(
            user=self.contractor_user,
            company_name="Test Construction Co.",
            is_active=True
        )
        
        # Create another contractor (for permissions testing)
        self.other_contractor = User.objects.create_user(
            phone="+919876543211",
            role="contractor"
        )
        self.other_contractor_profile = ContractorProfile.objects.create(
            user=self.other_contractor,
            company_name="Other Co."
        )
        
        # Create worker
        self.worker_user = User.objects.create_user(
            phone="+919876543212",
            role="worker",
            first_name="Test",
            last_name="Worker"
        )
        self.worker_profile = WorkerProfile.objects.create(
            user=self.worker_user,
            availability_status="available"
        )
        
        # Create test site
        self.site = Site.objects.create(
            contractor=self.contractor_profile,
            name="Test Site",
            address="Test Address, Lucknow",
            lat=26.8467,
            lng=80.9462,
            is_active=True
        )
        
        # API clients
        self.client = APIClient()
        self.contractor_client = APIClient()
        self.contractor_client.force_authenticate(user=self.contractor_user)
        
        self.other_contractor_client = APIClient()
        self.other_contractor_client.force_authenticate(user=self.other_contractor)
    
    def test_create_site(self):
        """Test creating a new site."""
        response = self.contractor_client.post('/api/v1/contractors/sites/', {
            'name': 'New Site',
            'address': 'New Address, Lucknow',
            'lat': 26.8500,
            'lng': 80.9500,
            'is_active': True
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Site')
        self.assertEqual(Site.objects.count(), 2)
    
    def test_list_sites(self):
        """Test listing contractor's sites."""
        response = self.contractor_client.get('/api/v1/contractors/sites/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test Site')
    
    def test_assign_worker_to_site(self):
        """Test assigning a worker to a site."""
        response = self.contractor_client.post(
            f'/api/v1/contractors/sites/{self.site.id}/assign/',
            {
                'worker_id': str(self.worker_profile.id),
                'role_on_site': 'Plumber'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            SiteAssignment.objects.filter(
                site=self.site,
                worker=self.worker_profile
            ).exists()
        )
    
    def test_list_assigned_workers(self):
        """Test listing workers assigned to a site."""
        # First assign a worker
        SiteAssignment.objects.create(
            site=self.site,
            worker=self.worker_profile,
            assigned_by=self.contractor_user,
            role_on_site="Mason",
            is_active=True
        )
        
        response = self.contractor_client.get(
            f'/api/v1/contractors/sites/{self.site.id}/workers/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['role_on_site'], 'Mason')
    
    def test_mark_attendance(self):
        """Test marking attendance for a worker."""
        # Assign worker first
        SiteAssignment.objects.create(
            site=self.site,
            worker=self.worker_profile,
            assigned_by=self.contractor_user,
            is_active=True
        )
        
        today = timezone.now().date()
        response = self.contractor_client.post(
            f'/api/v1/contractors/sites/{self.site.id}/attendance/',
            {
                'worker_id': str(self.worker_profile.id),
                'status': 'present',
                'date': str(today)
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            SiteAttendance.objects.filter(
                site=self.site,
                worker=self.worker_profile,
                attendance_date=today,
                status='present'
            ).exists()
        )
    
    def test_get_attendance(self):
        """Test retrieving attendance for a date."""
        today = timezone.now().date()
        
        SiteAttendance.objects.create(
            site=self.site,
            worker=self.worker_profile,
            attendance_date=today,
            status='present',
            marked_by=self.contractor_user
        )
        
        response = self.contractor_client.get(
            f'/api/v1/contractors/sites/{self.site.id}/attendance/',
            {'date': str(today)}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status'], 'present')
    
    def test_site_dashboard(self):
        """Test site dashboard metrics."""
        today = timezone.now().date()
        
        # Assign worker
        SiteAssignment.objects.create(
            site=self.site,
            worker=self.worker_profile,
            assigned_by=self.contractor_user,
            is_active=True
        )
        
        # Mark attendance
        SiteAttendance.objects.create(
            site=self.site,
            worker=self.worker_profile,
            attendance_date=today,
            status='present',
            checkin_time=timezone.now(),
            marked_by=self.contractor_user
        )
        
        response = self.contractor_client.get(
            f'/api/v1/contractors/sites/{self.site.id}/dashboard/',
            {'date': str(today)}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_assigned'], 1)
        self.assertEqual(response.data['present_count'], 1)
        self.assertEqual(response.data['absent_count'], 0)
        self.assertEqual(response.data['attendance_rate'], 100.0)
    
    def test_site_permissions(self):
        """Test that contractors can only access their own sites."""
        # Unauthenticated request
        response = self.client.get(f'/api/v1/contractors/sites/{self.site.id}/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Different contractor accessing site
        response = self.other_contractor_client.get(
            f'/api/v1/contractors/sites/{self.site.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_attendance_export_admin_action(self):
        """Test CSV export functionality (basic check)."""
        from apps.contractors.admin import SiteAttendanceAdmin
        
        today = timezone.now().date()
        
        attendance = SiteAttendance.objects.create(
            site=self.site,
            worker=self.worker_profile,
            attendance_date=today,
            status='present',
            marked_by=self.contractor_user
        )
        
        # This is a basic check that the method exists and returns CSV
        from django.http import HttpRequest
        from django.contrib.admin.sites import AdminSite
        
        admin = SiteAttendanceAdmin(SiteAttendance, AdminSite())
        request = HttpRequest()
        queryset = SiteAttendance.objects.all()
        
        response = admin.export_attendance_csv(request, queryset)
        
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])
