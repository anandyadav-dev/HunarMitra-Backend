"""
Views for Feature Flags app.
"""
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from apps.flags.models import FeatureFlag
from apps.flags.signals import CACHE_KEY

class FeatureFlagListView(APIView):
    """
    Public Endpoint to returning all feature flags as a key-value map.
    
    Response format:
    {
        "FEATURE_CSR": false,
        "FEATURE_EKYC": true
    }
    
    This endpoint is cached for 5 minutes (TTL=300).
    Cache is automatically invalidated on any admin change.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # Try to get from cache first
        flags_map = cache.get(CACHE_KEY)
        
        if flags_map is None:
            # Cache miss - query DB
            flags = FeatureFlag.objects.all().values('key', 'enabled')
            
            # Transform to key-value map
            flags_map = {item['key']: item['enabled'] for item in flags}
            
            # Set cache (5 minutes)
            cache.set(CACHE_KEY, flags_map, timeout=300)
        
        return Response(flags_map)
