"""
URL configuration for Help & FAQ.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.help.views import HelpPageViewSet, FAQViewSet

router = DefaultRouter()
router.register(r'help', HelpPageViewSet, basename='help')
router.register(r'faqs', FAQViewSet, basename='faq')

urlpatterns = router.urls
