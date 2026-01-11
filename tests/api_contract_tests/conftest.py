"""
Shared fixtures for API contract tests.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.workers.models import WorkerProfile
from apps.jobs.models import Job, JobCategory
from apps.core.models import WeekDay

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_worker(db):
    """Create a worker user and profile."""
    user = User.objects.create_user(
        phone="+919999911111",
        password="password",
        role="worker",
        first_name="Raju",
        last_name="Painter"
    )
    
    # Create required profile
    WorkerProfile.objects.create(
        user=user,
        skill="Painter",
        experience_years=5,
        price_per_hour=500.0,
        bio="Expert painter",
        is_available=True,
        lat=28.6139,
        lng=77.2090
    )
    return user


@pytest.fixture
def user_employer(db):
    """Create an employer user."""
    return User.objects.create_user(
        phone="+919999922222",
        password="password",
        role="employer",
        first_name="Vijay",
        last_name="Employer"
    )


@pytest.fixture
def job_category(db):
    return JobCategory.objects.create(
        name="Plumbing",
        icon="plumbing_icon"
    )


@pytest.fixture
def job(db, user_employer, job_category):
    return Job.objects.create(
        employer=user_employer,
        category=job_category,
        title="Fix Leak",
        description="Kitchen sink leak",
        budget=1500.0,
        location="Delhi",
        status="open"
    )
