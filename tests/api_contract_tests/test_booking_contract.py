"""
Contract tests for Booking Lifecycle.
Frontend Requirement:
- Create booking -> status "requested"
- Status updates reflect immediately
"""
import pytest
from django.urls import reverse
from apps.bookings.models import Booking

@pytest.mark.django_db
def test_booking_lifecycle_contract(api_client, user_employer, user_worker):
    """
    Contract: Booking creation and status flow.
    """
    api_client.force_authenticate(user=user_employer)
    
    # 1. Create Booking
    url_create = reverse('booking-list')
    payload = {
        'worker_id': user_worker.id,
        'job_description': 'Paint wall',
        'scheduled_time': '2026-02-01T10:00:00Z',
        'address': {'text': '123 Main St'},
        'lat': 28.6,
        'lng': 77.2
    }
    
    response = api_client.post(url_create, payload, format='json')
    assert response.status_code == 201
    data = response.data
    
    # --- CREATE CONTRACT ---
    booking_id = data['id']
    assert data['status'] == 'requested'
    assert str(data['employer']) == str(user_employer.id)
    assert str(data['worker']) == str(user_worker.id)
    
    # 2. Lifecycle Updates
    # Worker confirms
    booking = Booking.objects.get(id=booking_id)
    # Simulate status transitions usually done via specific endpoints or PATCH
    
    url_detail = reverse('booking-detail', kwargs={'pk': booking_id})
    
    # Confirm
    api_client.force_authenticate(user=user_worker)
    patch_response = api_client.patch(url_detail, {'status': 'confirmed'})
    assert patch_response.status_code == 200
    assert patch_response.data['status'] == 'confirmed'
    
    # On the way
    patch_response = api_client.patch(url_detail, {'status': 'on_the_way'})
    assert patch_response.status_code == 200
    assert patch_response.data['status'] == 'on_the_way'
    
    # Arrived
    patch_response = api_client.patch(url_detail, {'status': 'arrived'})
    assert patch_response.status_code == 200
    assert patch_response.data['status'] == 'arrived'
    
    # In Progress
    patch_response = api_client.patch(url_detail, {'status': 'in_progress'})
    assert patch_response.status_code == 200
    assert patch_response.data['status'] == 'in_progress'

    # Completed
    patch_response = api_client.patch(url_detail, {'status': 'completed'})
    assert patch_response.status_code == 200
    assert patch_response.data['status'] == 'completed'
