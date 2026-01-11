"""
Contract tests for Worker API.
Frontend Requirement:
- User must see worker details incl. price, location, rating.
"""
import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_worker_detail_contract(api_client, user_worker):
    """
    Contract: GET /api/v1/workers/{id}/
    Must return: id, name, skill, price info, location
    """
    # Authenticate (optional depending on permissions, but good practice)
    api_client.force_authenticate(user=user_worker)
    
    url = reverse('worker-detail', kwargs={'pk': user_worker.id})
    response = api_client.get(url)
    
    assert response.status_code == 200
    data = response.data
    
    # --- CONTRACT CHECK ---
    
    # 1. ID Check
    assert str(data['id']) == str(user_worker.id)
    
    # 2. Basic Info
    assert 'first_name' in data
    assert 'last_name' in data
    assert data['role'] == 'worker'
    
    # 3. Profile Flattening (Frontend expects these at top level or clearly nested)
    # Based on current implementation, verify structure
    assert 'worker_profile' in data
    profile = data['worker_profile']
    
    # 4. Critical Profile Fields
    assert 'skill' in profile
    assert profile['skill'] == "Painter"
    
    # 5. Price Contract
    assert 'price_per_hour' in profile
    assert float(profile['price_per_hour']) == 500.0
    
    # 6. Location Contract (Critical for Map)
    assert 'lat' in profile
    assert 'lng' in profile
    assert float(profile['lat']) == 28.6139
    
    # 7. Availability
    assert 'is_available' in profile
    assert profile['is_available'] is True
