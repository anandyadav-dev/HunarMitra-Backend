"""
Views for Core app - Health check and theme endpoints.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView  # Added for AppConfigView
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.core.serializers import AppConfigSerializer # Added for AppConfigView


@extend_schema(
    responses={200: OpenApiResponse(description='Health check successful')},
    tags=['Core']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint.
    
    Returns the health status of the API.
    """
    return Response({'status': 'ok'}, status=status.HTTP_200_OK)


@extend_schema(
    responses={200: OpenApiResponse(description='Theme configuration')},
    tags=['Core']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def theme(request):
    """
    Get app theme configuration.
    
    Returns theme colors, branding, and feature flags for the frontend.
    """
    theme_config = {
        'colors': {
            'primary': '#FF6B35',
            'secondary': '#004E89',
            'accent': '#F77F00',
            'success': '#06D6A0',
            'warning': '#FFD23F',
            'error': '#EF476F',
            'background': '#FFFFFF',
            'surface': '#F8F9FA',
            'text_primary': '#212529',
            'text_secondary': '#6C757D',
        },
        'logo_url': 'https://minio.local/static/logo.png',
        'fonts': ['Roboto', 'Open Sans', 'Lato'],
        'feature_flags': {
            'enable_attendance': True,
            'enable_payments': False,
            'enable_job_matching': True,
            'enable_notifications': True,
            'enable_chat': False,
        },
        'app_version': '1.0.0',
        'min_supported_version': '1.0.0',
    }
    
    return Response(theme_config, status=status.HTTP_200_OK)


@extend_schema(
    summary="Get Application Configuration",
    description="Returns complete app configuration including theme, categories, banners, and feature flags. Response is cached for 5 minutes.",
    responses={200: OpenApiResponse(description='Application configuration')}, # Placeholder, assuming AppConfigSerializer is not imported yet
)
class AppConfigView(APIView):
    """
    Application configuration endpoint.
    Returns theme, categories (services), banners, and feature flags.
    Response is cached using Redis.
    """

    permission_classes = []  # Public endpoint

    def get(self, request):
        """Get complete app configuration."""
        from django.core.cache import cache

        from apps.core.models import Banner, Theme
        from apps.core.serializers import AppConfigSerializer
        from apps.services.models import Service

        # Try to get cached response
        cache_key = "app_config_response"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        # Get active theme or use defaults
        theme = Theme.objects.filter(active=True).first()

        # Default theme for fallback
        default_theme_data = {
            "name": "Default",
            "primary_color": "#2563EB",
            "accent_color": "#F59E0B",
            "background_color": "#F9FAFB",
            "logo_s3_key": "static/logo.png",
            "fonts": [{"family": "Inter", "s3_key": "static/fonts/default.woff"}],
        }

        # Get active categories (services)
        categories = Service.objects.filter(is_active=True).order_by("display_order")

        # Get active banners
        banners = Banner.objects.filter(active=True)

        # App metadata
        app_metadata = {
            "name": "HunarMitra",
            "version": "1.0.0",
            "supported_locales": ["en", "hi", "mr"],
            "support_phone": "+91-1800-XXX-XXXX",
        }

        # Feature flags
        features = {
            "attendance_kiosk": True,
            "ekyc": False,
            "auto_assign_emergency": True,
            "enable_notifications": True,
            "enable_dark_mode": True,
        }

        # Meta information
        cache_ttl = 300  # 5 minutes
        meta = {
            "config_version": "1.0",
            "cache_ttl_seconds": cache_ttl,
        }

        # Build response data
        from apps.core.serializers import BannerSerializer, CategorySerializer, ThemeSerializer

        response_data = {
            "app": app_metadata,
            "theme": (
                ThemeSerializer(theme).data
                if theme
                else ThemeSerializer(type("Theme", (object,), default_theme_data)()).data
            ),
            "categories": CategorySerializer(categories, many=True).data,
            "banners": BannerSerializer(banners, many=True).data,
            "features": features,
            "meta": meta,
        }

        # Cache the response
        cache.set(cache_key, response_data, cache_ttl)

        return Response(response_data)


@extend_schema(
    summary="Get Theme Configuration",
    description="Returns active theme with colors, logo, hero image, and fonts. Response is cached.",
    responses={200: OpenApiResponse(description='Theme configuration')},
    tags=['Config']
)
class ThemeConfigView(APIView):
    """
    Theme configuration endpoint for frontend UI.
    Returns active theme with MinIO asset URLs.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get active theme configuration."""
        from django.core.cache import cache
        from django.conf import settings
        from apps.core.models import Theme
        
        # Try cache first
        cache_key = "theme_config_active"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        # Get active theme
        theme = Theme.objects.filter(active=True).first()
        
        if not theme:
            return Response(
                {"error": "No active theme configured"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Build MinIO URLs
        minio_endpoint = getattr(settings, 'AWS_S3_ENDPOINT_URL', 'http://localhost:9000')
        bucket = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'hunarmitra')
        
        def build_url(s3_key):
            if not s3_key:
                return None
            return f"{minio_endpoint}/{bucket}/{s3_key}"
        
        # Build response
        theme_data = {
            "name": theme.name,
            "primary_color": theme.primary_color,
            "secondary_color": theme.accent_color,  # Map accent to secondary
            "background_color": theme.background_color,
            "logo_url": build_url(theme.logo_s3_key),
            "hero_image_url": build_url(theme.hero_image_s3_key),
            "fonts": [
                {
                    "family": font.get("family"),
                    "url": build_url(font.get("s3_key"))
                }
                for font in theme.fonts
            ] if theme.fonts else []
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, theme_data, 300)
        
        return Response(theme_data)


@extend_schema(
    summary="Get Translations (i18n)",
    description="Returns translation strings for specified language with fallback to English.",
    responses={200: OpenApiResponse(description='Translation key-value pairs')},
    tags=['Config']
)
class I18nView(APIView):
    """
    Internationalization endpoint.
    Returns translations for specified language.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get translations for specified language."""
        from django.core.cache import cache
        from apps.core.models import Translation
        
        lang = request.query_params.get('lang', 'en')
        
        # Validate language
        if lang not in ['en', 'hi']:
            return Response(
                {"error": "Invalid language. Supported: en, hi"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Try cache first
        cache_key = f"i18n_translations_{lang}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        # Get translations for requested language
        translations = Translation.objects.filter(lang=lang)
        trans_dict = {t.key: t.value for t in translations}
        
        # If requesting Hindi, add English fallback for missing keys
        if lang == 'hi':
            en_translations = Translation.objects.filter(lang='en')
            for t in en_translations:
                if t.key not in trans_dict:
                    trans_dict[t.key] = t.value  # Fallback to English
        
        # Cache for 10 minutes
        cache.set(cache_key, trans_dict, 600)
        
        return Response(trans_dict)
