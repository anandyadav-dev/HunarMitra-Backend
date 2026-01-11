"""
URL configuration for Feature Flags app.
"""
from django.urls import path
from apps.flags.views import FeatureFlagListView

urlpatterns = [
    path('', FeatureFlagListView.as_view(), name='feature-flags'),
]
