"""
Views for Services app.
"""

from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema

from .models import Service
from .serializers import ServiceSerializer


@extend_schema(tags=['Services'])
class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing and retrieving services.
    
    Only active services are returned.
    """
    queryset = Service.objects.filter(is_active=True)
    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'
