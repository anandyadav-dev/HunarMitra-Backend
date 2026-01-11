"""
Views for CMS app.
"""
from django.utils import timezone
from rest_framework import generics, permissions
from drf_spectacular.utils import extend_schema

from apps.cms.models import Banner
from apps.cms.serializers import BannerSerializer


class BannerListView(generics.ListAPIView):
    """
    Public API endpoint for fetching promotional banners.
    
    Query params:
    - slot: Filter banners by slot (e.g., home_top, home_mid)
    
    Returns only active banners within their scheduled time window,
    ordered by priority (descending) then creation date (descending).
    """
    serializer_class = BannerSerializer
    permission_classes = [permissions.AllowAny]  # Public endpoint
    
    @extend_schema(
        parameters=[
            {
                'name': 'slot',
                'in': 'query',
                'description': 'Filter by banner slot (e.g., home_top)',
                'required': False,
                'schema': {'type': 'string'}
            }
        ],
        description="Get active promotional banners"
    )
    def get_queryset(self):
        """
        Return active banners within their scheduled time window.
        
        Filters:
        - active = True
        - starts_at <= now (or null)
        - ends_at >= now (or null)
        - Optional: slot filter
        
        Ordering:
        - priority DESC
        - created_at DESC
        """
        now = timezone.now()
        
        # Base queryset: active banners
        queryset = Banner.objects.filter(active=True)
        
        # Filter by schedule
        # Include banners where:
        # - starts_at is null OR starts_at <= now
        # - ends_at is null OR ends_at >= now
        queryset = queryset.filter(
            models.Q(starts_at__isnull=True) | models.Q(starts_at__lte=now)
        ).filter(
            models.Q(ends_at__isnull=True) | models.Q(ends_at__gte=now)
        )
        
        # Filter by slot if provided
        slot = self.request.query_params.get('slot')
        if slot:
            queryset = queryset.filter(slot=slot)
        
        # Order by priority (DESC) then created_at (DESC)
        queryset = queryset.order_by('-priority', '-created_at')
        
        return queryset


# Import Q for queryset filtering
from django.db import models
