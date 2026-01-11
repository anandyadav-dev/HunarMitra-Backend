"""
Tests for Pagination and Filters across APIs.
"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.urls import reverse

from apps.workers.models import WorkerProfile
from apps.jobs.models import Job
from apps.services.models import Service

User = get_user_model()


@pytest.mark.django_db
class TestWorkerListPagination:
    """Test pagination for worker list API."""
    
    def setup_method(self):
        self.client = APIClient()
        
        # Create service
        self.service = Service.objects.create(
            name="Plumber",
            title_en="Plumber",
            is_active=True
        )
        
        # Create 25 workers for pagination testing
        self.workers = []
        for i in range(25):
            user = User.objects.create_user(
                phone=f"+9199000{i:05d}",
                role="worker"
            )
            worker = WorkerProfile.objects.create(
                user=user,
                price_amount=Decimal(100 + (i * 50)),
                rating=Decimal(3 + (i % 3)),
                availability_status='available' if i % 2 == 0 else 'unavailable'
            )
            worker.services.add(self.service)
            self.workers.append(worker)
    
    def test_default_pagination(self):
        """Test default pagination (page=1, per_page=20)."""
        url = reverse('worker-list')
        
        response = self.client.get(url)
        
        assert response.status_code == 200
        assert 'count' in response.data
        assert 'next_page' in response.data
        assert 'prev_page' in response.data
        assert 'results' in response.data
        assert response.data['count'] == 25
        assert len(response.data['results']) == 20
        assert response.data['next_page'] == 2
        assert response.data['prev_page'] is None
    
    def test_custom_page_size(self):
        """Test custom per_page parameter."""
        url = reverse('worker-list')
        
        response = self.client.get(url, {'per_page': 10})
        
        assert response.status_code == 200
        assert len(response.data['results']) == 10
        assert response.data['next_page'] == 2
    
    def test_second_page(self):
        """Test fetching second page."""
        url = reverse('worker-list')
        
        response = self.client.get(url, {'page': 2})
        
        assert response.status_code == 200
        assert len(response.data['results']) == 5  # Remaining 5 workers
        assert response.data['prev_page'] == 1
        assert response.data['next_page'] is None


@pytest.mark.django_db
class TestWorkerFilters:
    """Test filtering for worker list API."""
    
    def setup_method(self):
        self.client = APIClient()
        
        # Create services
        self.plumber_service = Service.objects.create(
            name="Plumber",
            title_en="Plumber",
            is_active=True
        )
        self.electrician_service = Service.objects.create(
            name="Electrician",
            title_en="Electrician",
            is_active=True
        )
        
        # Create workers with different attributes
        user1 = User.objects.create_user(phone="+919900001111", role="worker")
        self.worker1 = WorkerProfile.objects.create(
            user=user1,
            price_amount=Decimal(100),
            rating=Decimal(4.5),
            availability_status='available'
        )
        self.worker1.services.add(self.plumber_service)
        
        user2 = User.objects.create_user(phone="+919900002222", role="worker")
        self.worker2 = WorkerProfile.objects.create(
            user=user2,
            price_amount=Decimal(500),
            rating=Decimal(3.0),
            availability_status='unavailable'
        )
        self.worker2.services.add(self.electrician_service)
        
        user3 = User.objects.create_user(phone="+919900003333", role="worker")
        self.worker3 = WorkerProfile.objects.create(
            user=user3,
            price_amount=Decimal(300),
            rating=Decimal(5.0),
            availability_status='available'
        )
        self.worker3.services.add(self.plumber_service)
    
    def test_filter_by_skill(self):
        """Test filtering workers by skill."""
        url = reverse('worker-list')
        
        response = self.client.get(url, {'skill': 'Plumber'})
        
        assert response.status_code == 200
        assert response.data['count'] == 2  # worker1 and worker3
    
    def test_filter_by_min_price(self):
        """Test filtering workers by minimum price."""
        url = reverse('worker-list')
        
        response = self.client.get(url, {'min_price': 200})
        
        assert response.status_code == 200
        assert response.data['count'] == 2  # worker2 and worker3
    
    def test_filter_by_max_price(self):
        """Test filtering workers by maximum price."""
        url = reverse('worker-list')
        
        response = self.client.get(url, {'max_price': 400})
        
        assert response.status_code == 200
        assert response.data['count'] == 2  # worker1 and worker3
    
    def test_filter_by_price_range(self):
        """Test filtering workers by price range."""
        url = reverse('worker-list')
        
        response = self.client.get(url, {'min_price': 200, 'max_price': 400})
        
        assert response.status_code == 200
        assert response.data['count'] == 1  # Only worker3
    
    def test_filter_by_rating(self):
        """Test filtering workers by minimum rating."""
        url = reverse('worker-list')
        
        response = self.client.get(url, {'rating': 4})
        
        assert response.status_code == 200
        assert response.data['count'] == 2  # worker1 (4.5) and worker3 (5.0)
    
    def test_filter_by_available_now(self):
        """Test filtering workers by availability."""
        url = reverse('worker-list')
        
        response = self.client.get(url, {'available_now': 'true'})
        
        assert response.status_code == 200
        assert response.data['count'] == 2  # worker1 and worker3
    
    def test_combined_filters(self):
        """Test combining multiple filters."""
        url = reverse('worker-list')
        
        response = self.client.get(url, {
            'skill': 'Plumber',
            'available_now': 'true',
            'rating': 4
        })
        
        assert response.status_code == 200
        assert response.data['count'] == 2  # worker1 and worker3


@pytest.mark.django_db
class TestWorkerSorting:
    """Test sorting for worker list API."""
    
    def setup_method(self):
        self.client = APIClient()
        
        # Create workers with different prices and ratings
        user1 = User.objects.create_user(phone="+919900001111", role="worker")
        self.worker1 = WorkerProfile.objects.create(
            user=user1,
            price_amount=Decimal(300),
            rating=Decimal(4.0)
        )
        
        user2 = User.objects.create_user(phone="+919900002222", role="worker")
        self.worker2 = WorkerProfile.objects.create(
            user=user2,
            price_amount=Decimal(100),
            rating=Decimal(5.0)
        )
        
        user3 = User.objects.create_user(phone="+919900003333", role="worker")
        self.worker3 = WorkerProfile.objects.create(
            user=user3,
            price_amount=Decimal(500),
            rating=Decimal(3.0)
        )
    
    def test_sort_by_price(self):
        """Test sorting workers by price (ascending)."""
        url = reverse('worker-list')
        
        response = self.client.get(url, {'sort': 'price'})
        
        assert response.status_code == 200
        prices = [Decimal(w['price_amount']) for w in response.data['results']]
        assert prices == [Decimal(100), Decimal(300), Decimal(500)]
    
    def test_sort_by_rating(self):
        """Test sorting workers by rating (descending)."""
        url = reverse('worker-list')
        
        response = self.client.get(url, {'sort': 'rating'})
        
        assert response.status_code == 200
        ratings = [Decimal(w['rating']) for w in response.data['results']]
        assert ratings == [Decimal(5.0), Decimal(4.0), Decimal(3.0)]


@pytest.mark.django_db
class TestJobListPagination:
    """Test pagination for job list API."""
    
    def setup_method(self):
        self.client = APIClient()
        
        # Create service and user
        self.service = Service.objects.create(
            name="Construction",
            title_en="Construction",
            is_active=True
        )
        self.poster = User.objects.create_user(
            phone="+919900001111",
            role="customer"
        )
        
        # Create 25 jobs
        for i in range(25):
            Job.objects.create(
                poster=self.poster,
                service=self.service,
                title=f"Job {i}",
                description="Test job",
                budget=Decimal(1000 + (i * 100)),
                status='open' if i % 2 == 0 else 'completed'
            )
    
    def test_default_pagination(self):
        """Test default pagination for jobs."""
        url = reverse('job-list')
        
        response = self.client.get(url)
        
        assert response.status_code == 200
        assert response.data['count'] == 25
        assert len(response.data['results']) == 20


@pytest.mark.django_db
class TestJobFilters:
    """Test filtering for job list API."""
    
    def setup_method(self):
        self.client = APIClient()
        
        # Create services
        self.service1 = Service.objects.create(
            name="Plumbing",
            title_en="Plumbing",
            is_active=True
        )
        self.service2 = Service.objects.create(
            name="Electrical",
            title_en="Electrical",
            is_active=True
        )
        
        # Create poster
        self.poster = User.objects.create_user(
            phone="+919900001111",
            role="customer"
        )
        
        # Create jobs with different attributes
        self.job1 = Job.objects.create(
            poster=self.poster,
            service=self.service1,
            title="Job 1",
            description="Test",
            budget=Decimal(1000),
            status='open'
        )
        
        self.job2 = Job.objects.create(
            poster=self.poster,
            service=self.service2,
            title="Job 2",
            description="Test",
            budget=Decimal(5000),
            status='completed'
        )
        
        self.job3 = Job.objects.create(
            poster=self.poster,
            service=self.service1,
            title="Job 3",
            description="Test",
            budget=Decimal(3000),
            status='open'
        )
    
    def test_filter_by_status(self):
        """Test filtering jobs by status."""
        url = reverse('job-list')
        
        response = self.client.get(url, {'status': 'open'})
        
        assert response.status_code == 200
        assert response.data['count'] == 2  # job1 and job3
    
    def test_filter_by_min_price(self):
        """Test filtering jobs by minimum price."""
        url = reverse('job-list')
        
        response = self.client.get(url, {'min_price': 2000})
        
        assert response.status_code == 200
        assert response.data['count'] == 2  # job2 and job3
    
    def test_filter_by_service(self):
        """Test filtering jobs by service."""
        url = reverse('job-list')
        
        response = self.client.get(url, {'service_id': str(self.service1.id)})
        
        assert response.status_code == 200
        assert response.data['count'] == 2  # job1 and job3
    
    def test_sort_by_price(self):
        """Test sorting jobs by price."""
        url = reverse('job-list')
        
        response = self.client.get(url, {'sort': 'price'})
        
        assert response.status_code == 200
        budgets = [Decimal(j['budget']) for j in response.data['results']]
        assert budgets == [Decimal(1000), Decimal(3000), Decimal(5000)]
