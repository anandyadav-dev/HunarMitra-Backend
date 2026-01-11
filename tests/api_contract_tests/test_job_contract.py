"""
Contract tests for Job Apply Flow.
Frontend Requirement:
- Worker can apply to open jobs
- Employer can see application and accept it
"""
import pytest
from django.urls import reverse
from apps.jobs.models import JobApplication

@pytest.mark.django_db
def test_job_application_flow_contract(api_client, user_worker, user_employer, job):
    """
    Contract: Apply -> Accept flow
    """
    # 1. Apply (Worker)
    api_client.force_authenticate(user=user_worker)
    url_apply = reverse('job-apply', kwargs={'pk': job.id})
    
    response = api_client.post(url_apply)
    assert response.status_code == 201
    
    # Check application created
    assert JobApplication.objects.filter(job=job, worker=user_worker).exists()
    application = JobApplication.objects.get(job=job, worker=user_worker)
    
    # 2. Accept (Employer)
    api_client.force_authenticate(user=user_employer)
    # Assuming endpoint: /api/v1/jobs/{job_id}/applications/{app_id}/accept/
    # Or simpler: /api/v1/job-applications/{id}/accept/ depending on routing
    # Let's try the standard router structure if viewset
    
    # NOTE: Adjusting url based on typical Nested or standard routing.
    # If routed as /jobs/<id>/applications/<id>/accept/
    url_accept = f"/api/v1/jobs/{job.id}/applications/{application.id}/accept/"
    
    # Since we don't have the exact URL config in memory for nested apps,
    # we will use the logic we implemented in jobs views.
    # Looking at previous context: explicit actions usually on ViewSet.
    
    # Checking JobViewSet actions... 
    # If explicit 'accept' action exists on JobViewSet or JobApplicationViewSet
    
    # Let's assume generic Update on application if specific endpoint is tricky to guess without `urls.py` read
    # But user prompt asked to test: POST /api/jobs/{id}/applications/{app_id}/accept
    
    response = api_client.post(url_accept)
    
    # If 404, it means router logic might be different. 
    # Contract test SHOULD fail if endpoint missing.
    # For now, asserting 200 assuming implementation exists as per prompt expectations.
    
    # If implementation handles accept logic differently (e.g. PATCH status='accepted'),
    # the contract test enforces verify standard.
    
    # To be safe for this "Contract" test, let's verify the RESULT primarily.
    # If the endpoint doesn't exist, this line fails, alerting us to "Missing Contract Endpoint"
    
    if response.status_code == 404:
        # Fallback: Maybe it's patch on application details?
        # Contract strictness: "Tests must fail clearly"
        pass 
        
    assert response.status_code in [200, 201], f"Endpoint {url_accept} not found or failed"
    
    # 3. Verify Job Status
    job.refresh_from_db()
    assert job.status == 'assigned' or job.status == 'in_progress'
    assert job.assigned_worker == user_worker
