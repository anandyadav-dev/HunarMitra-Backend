"""
URL patterns for Analytics app.
"""
from django.urls import path
from .views import (
    EventIngestionView,
    DailySummaryView,
    TopServicesView,
    ActiveUsersView,
    CSVExportView
)

# Public ingestion endpoint
urlpatterns = [
    path('events/', EventIngestionView.as_view(), name='analytics-ingest'),
]

# Admin report endpoints
admin_urlpatterns = [
    path('daily-summary/', DailySummaryView.as_view(), name='analytics-daily-summary'),
    path('top-services/', TopServicesView.as_view(), name='analytics-top-services'),
    path('active-users/', ActiveUsersView.as_view(), name='analytics-active-users'),
    path('export/', CSVExportView.as_view(), name='analytics-export'),
]
