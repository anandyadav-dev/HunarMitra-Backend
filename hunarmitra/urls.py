"""
URL configuration for HunarMitra project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

admin_url = getattr(settings, 'ADMIN_URL', 'admin/')

urlpatterns = [
    path(admin_url, admin.site.urls),
    
    # API v1
    # Authentication endpoints (OTP, login, etc.)
    path('api/v1/auth/', include('apps.users.urls')),  # CRITICAL: Auth endpoints
    
    path('api/v1/services/', include('apps.services.urls')),
    path('api/v1/', include('apps.bookings.urls')),
    path('api/v1/', include('apps.jobs.urls')),
    path('api/v1/payments/', include('apps.payments.urls')),
    path('api/v1/', include('apps.contractors.urls')),
    path('api/v1/', include('apps.attendance.urls')),
    path('api/v1/media/', include('apps.media.urls')),
    path('api/v1/tracking/', include('apps.tracking.urls')),
    path('api/v1/tts/', include('apps.tts.urls')),
    path('api/v1/workers/', include('apps.workers.urls')),
    path('api/v1/', include('apps.help.urls')),
    path('api/v1/cms/', include('apps.cms.urls')),
    path('api/v1/flags/', include('apps.flags.urls')),
    path('api/v1/', include('apps.notifications.urls')),
    path('api/v1/emergency/', include('apps.emergency.urls')),
    path('api/v1/dashboard/', include('apps.dashboard.urls')),
    path('api/admin/dashboard/', include('apps.dashboard.urls')),
    path('api/v1/analytics/', include('apps.analytics.urls')),
    path('api/admin/analytics/', include(('apps.analytics.urls', 'analytics'), namespace='admin-analytics')),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
