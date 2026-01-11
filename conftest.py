"""
Pytest configuration and fixtures.
"""

import pytest
from rest_framework.test import APIClient

@pytest.fixture
def api_client():
    """Fixture for DRF APIClient."""
    return APIClient()
