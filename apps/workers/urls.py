"""
URL configuration for Workers app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.workers.views import WorkerViewSet, NearbyWorkersView, WorkerListView
from apps.workers.views_availability import (
    ToggleAvailabilityView,
    UpdateLocationView,
    NearbyWorkersView as NearbySearchView
)

# Create router for ViewSet
router = DefaultRouter()
router.register(r'', WorkerViewSet, basename='worker')

urlpatterns = [
    # ViewSet routes (list, create, retrieve, update, destroy)
    path('', include(router.urls)),
    
    # Additional custom views
    path('nearby/', NearbyWorkersView.as_view(), name='nearby-workers'),
    
    # Availability endpoints
    path('me/availability/', ToggleAvailabilityView.as_view(), name='worker-toggle-availability'),
    path('me/location/', UpdateLocationView.as_view(), name='worker-update-location'),
    
    # Enhanced nearby search
    path('search/nearby/', NearbySearchView.as_view(), name='worker-nearby-search'),
]
