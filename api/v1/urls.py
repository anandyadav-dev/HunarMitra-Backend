"""
API v1 URL configuration.
"""

from django.urls import path, include

urlpatterns = [
    # Auth endpoints
    path('auth/', include('apps.users.urls')),
    
    # Core endpoints
    path('', include('apps.core.urls')),
    
    # Services
    path('services/', include('apps.services.urls')),
    
    # Jobs (placeholder)
    # path('jobs/', include('apps.jobs.urls')),
    
    # Workers (placeholder)
    # path('workers/', include('apps.workers.urls')),
]
