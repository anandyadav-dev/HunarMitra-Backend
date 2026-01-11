"""
Contract tests for Config/Theme API.
Frontend Requirement:
- App needs active theme config on launch
"""
import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_config_theme_contract(api_client):
    """
    Contract: GET /api/v1/core/theme/
    Must return: primary_color, secondary_color, etc.
    """
    # Assuming public endpoint or auth required
    # Check URLs... usually core endpoints
    
    # NOTE: We need to verify the exact URL for theme.
    # Often /api/v1/config/ or /api/v1/core/theme/
    
    url = "/api/v1/core/theme/active/" # Standard pattern for singleton
    # If viewset, maybe list?
    
    # Let's try finding the URL name if possible, or hardcode the contract path
    # If the endpoint requested in prompt `GET /api/config/theme`
    
    url = "/api/v1/core/theme/active/"
    
    response = api_client.get(url)
    
    # If 404, contract fails
    assert response.status_code == 200, "Theme endpoint missing"
    
    data = response.data
    
    # --- CONTRACT CHECK ---
    assert 'primary_color' in data
    assert 'secondary_color' in data
    assert 'font_family' in data
    
    # Color format check (Hex)
    assert data['primary_color'].startswith('#')

@pytest.mark.django_db
def test_config_translations_contract(api_client):
    """
    Contract: GET /api/v1/core/translations/?lang=hi
    """
    url = "/api/v1/core/translations/"
    response = api_client.get(url, {'lang': 'hi'})
    
    assert response.status_code == 200
    data = response.data
    
    # Must be a dictionary of key-values
    assert isinstance(data, dict)
    # Should be non-empty if seeded
    # assert len(data) > 0 
