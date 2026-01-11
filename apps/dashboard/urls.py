"""
URL patterns for Dashboard app.
"""
from django.urls import path
from .views import (
    WorkerDashboardView,
    EmployerDashboardView,
    ContractorDashboardView,
    AdminDashboardView,
    ClearDashboardCacheView
)

urlpatterns = [
    path('worker/', WorkerDashboardView.as_view(), name='dashboard-worker'),
    path('employer/', EmployerDashboardView.as_view(), name='dashboard-employer'),
    path('contractor/', ContractorDashboardView.as_view(), name='dashboard-contractor'),
    path('admin/', AdminDashboardView.as_view(), name='dashboard-admin'),
]

# Admin cache control (separate URL pattern for clarity)
admin_urlpatterns = [
    path('cache/clear/', ClearDashboardCacheView.as_view(), name='dashboard-cache-clear'),
]
