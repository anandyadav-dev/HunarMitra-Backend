"""
URL patterns for Notifications app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    NotificationViewSet,
    BookingTimelineView,
    CreateTestNotificationView
)
from .views_devices import DeviceViewSet

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'devices', DeviceViewSet, basename='device')

urlpatterns = [
    path('', include(router.urls)),
    path('notifications/test/', CreateTestNotificationView.as_view(), name='notification-test'),
]

# Timeline endpoints (can be in bookings or here)
timeline_urlpatterns = [
    path('bookings/<uuid:booking_id>/timeline/', BookingTimelineView.as_view(), name='booking-timeline'),
]
