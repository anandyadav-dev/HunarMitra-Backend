"""
Views for Help & FAQ APIs.
"""
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.help.models import HelpPage, FAQ
from apps.help.serializers import HelpPageSerializer, FAQSerializer


@extend_schema(
    tags=['Help & FAQ'],
    parameters=[
        OpenApiParameter(
            name='lang',
            type=str,
            enum=['en', 'hi'],
            description='Filter by language (optional)'
        )
    ]
)
class HelpPageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only API for Help Pages.
    
    Supports optional language filtering via ?lang=en|hi query parameter.
    Returns only active help pages, ordered by display order.
    """
    serializer_class = HelpPageSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    
    def get_queryset(self):
        """Filter by language if specified, and only return active pages."""
        queryset = HelpPage.objects.filter(is_active=True)
        
        lang = self.request.query_params.get('lang', None)
        if lang in ['en', 'hi']:
            queryset = queryset.filter(lang=lang)
        
        return queryset.order_by('order', 'title')


@extend_schema(
    tags=['Help & FAQ'],
    parameters=[
        OpenApiParameter(
            name='lang',
            type=str,
            enum=['en', 'hi'],
            description='Filter by language (optional)'
        )
    ]
)
class FAQViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only API for FAQs.
    
    Supports optional language filtering via ?lang=en|hi query parameter.
    Returns only active FAQs, ordered by display order.
    """
    serializer_class = FAQSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        """Filter by language if specified, and only return active FAQs."""
        queryset = FAQ.objects.filter(is_active=True)
        
        lang = self.request.query_params.get('lang', None)
        if lang in ['en', 'hi']:
            queryset = queryset.filter(lang=lang)
        
        return queryset.order_by('order', 'question')
