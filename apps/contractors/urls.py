"""
URL configuration for Contractors app - profiles and site management.
"""
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ContractorViewSet
from .views_sites import SiteViewSet

# Create router for viewsets
router = DefaultRouter()
router.register(r'contractors', ContractorViewSet, basename='contractor')
router.register(r'sites', SiteViewSet, basename='site')

urlpatterns = router.urls
