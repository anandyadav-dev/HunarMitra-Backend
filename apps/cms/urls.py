"""
URL configuration for CMS app.
"""
from django.urls import path
from apps.cms.views import BannerListView

urlpatterns = [
    path('banners/', BannerListView.as_view(), name='banner-list'),
]
