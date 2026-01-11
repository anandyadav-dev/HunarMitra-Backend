"""
URL configuration for Emergency app.
"""
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import EmergencyRequestViewSet

router = DefaultRouter()
router.register(r'requests', EmergencyRequestViewSet, basename='emergency-request')

urlpatterns = router.urls
