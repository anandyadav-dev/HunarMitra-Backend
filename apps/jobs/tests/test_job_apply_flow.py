"""
Tests for Job Application Flow.
"""
import pytest
from unittest.mock import patch
from django.contrib.auth import get_user_model
from apps.jobs.models import Job, JobApplication
from apps.services.models import Service
from apps.workers.models import WorkerProfile
from apps.notifications.models import Notification
from rest_framework.test import APIClient
from django.urls import reverse

User = get_user_model()

@pytest.mark.django_db
class TestJobApplicationFlow:
    def setup_method(self):
        self.client = APIClient()
        
        # Create users
        self.employer = User.objects.create_user(phone="+919000001111", role="employer")
        self.worker_user = User.objects.create_user(
            phone="+919000002222",
            role="worker",
            first_name="Ravi",
            last_name="Kumar"
        )
        self.worker_profile = WorkerProfile.objects.create(user=self.worker_user)
        
        # Create service
        self.service = Service.objects.create(name="Carpentry", slug="carpentry")
        
        # Create job
        self.job = Job.objects.create(
            poster=self.employer,
            service=self.service,
            title="Fix wooden door",
            description="Need carpenter to fix door",
            status="open",
            budget=1000.00
        )

    @patch('apps.realtime.publisher.get_redis_connection')
    def test_worker_applies_successfully(self, mock_redis):
        """Test that a worker can apply for a job."""
        self.client.force_authenticate(user=self.worker_user)
        
        url = reverse('job-apply', kwargs={'pk': self.job.id})
        response = self.client.post(url)
        
        assert response.status_code == 201
        assert response.data['status'] == 'applied'
        
        # Verify JobApplication created
        application = JobApplication.objects.get(job=self.job, worker=self.worker_profile)
        assert application.status == JobApplication.STATUS_APPLIED
        
        # Verify notification created for employer
        notification = Notification.objects.filter(user=self.employer, notification_type='job_application').first()
        assert notification is not None
        assert 'Ravi Kumar' in notification.message
        
        # Verify realtime event published
        assert mock_redis.return_value.publish.called

    @patch('apps.realtime.publisher.get_redis_connection')
    def test_duplicate_application_blocked(self, mock_redis):
        """Test that a worker cannot apply twice for the same job."""
        self.client.force_authenticate(user=self.worker_user)
        
        # First application
        JobApplication.objects.create(job=self.job, worker=self.worker_profile)
        
        # Second application attempt
        url = reverse('job-apply', kwargs={'pk': self.job.id})
        response = self.client.post(url)
        
        assert response.status_code == 400
        assert 'already applied' in response.data['error'].lower()

    @patch('apps.realtime.publisher.get_redis_connection')
    def test_accept_application_assigns_worker(self, mock_redis):
        """Test that accepting application assigns worker to job."""
        # Create application
        application = JobApplication.objects.create(
            job=self.job,
            worker=self.worker_profile,
            status=JobApplication.STATUS_APPLIED
        )
        
        self.client.force_authenticate(user=self.worker_user)
        
        url = reverse('job-accept-application', kwargs={'pk': self.job.id, 'application_id': application.id})
        response = self.client.post(url)
        
        assert response.status_code == 200
        assert response.data['status'] == 'accepted'
        
        # Verify application accepted
        application.refresh_from_db()
        assert application.status == JobApplication.STATUS_ACCEPTED
        
        # Verify worker assigned to job
        self.job.refresh_from_db()
        assert self.job.assigned_worker == self.worker_user
        assert self.job.status == 'assigned'
        
        # Verify notifications created
        employer_notif = Notification.objects.filter(user=self.employer, notification_type='application_accepted').first()
        worker_notif = Notification.objects.filter(user=self.worker_user, notification_type='job_assigned').first()
        assert employer_notif is not None
        assert worker_notif is not None

    @patch('apps.realtime.publisher.get_redis_connection')
    def test_decline_application_updates_status(self, mock_redis):
        """Test that declining application updates status correctly."""
        # Create application
        application = JobApplication.objects.create(
            job=self.job,
            worker=self.worker_profile,
            status=JobApplication.STATUS_APPLIED
        )
        
        self.client.force_authenticate(user=self.worker_user)
        
        url = reverse('job-decline-application', kwargs={'pk': self.job.id, 'application_id': application.id})
        response = self.client.post(url)
        
        assert response.status_code == 200
        assert response.data['status'] == 'declined'
        
        # Verify application declined
        application.refresh_from_db()
        assert application.status == JobApplication.STATUS_DECLINED
        
        # Verify job NOT assigned
        self.job.refresh_from_db()
        assert self.job.assigned_worker is None
        
        # Verify notification created for employer
        notification = Notification.objects.filter(user=self.employer, notification_type='application_declined').first()
        assert notification is not None

    def test_non_worker_cannot_apply(self):
        """Test that non-workers cannot apply for jobs."""
        self.client.force_authenticate(user=self.employer)
        
        url = reverse('job-apply', kwargs={'pk': self.job.id})
        response = self.client.post(url)
        
        assert response.status_code == 403
        assert 'worker' in response.data['error'].lower()

    def test_unauthorized_cannot_accept(self):
        """Test that unauthorized users cannot accept applications."""
        application = JobApplication.objects.create(
            job=self.job,
            worker=self.worker_profile
        )
        
        # Create another worker
        other_worker = User.objects.create_user(phone="+919000003333", role="worker")
        self.client.force_authenticate(user=other_worker)
        
        url = reverse('job-accept-application', kwargs={'pk': self.job.id, 'application_id': application.id})
        response = self.client.post(url)
        
        assert response.status_code == 403
