"""
URL patterns for realtime tracking endpoints.
"""
from django.urls import path
from .views import BookingTrackingView

urlpatterns = [
    path('tracking/<uuid:booking_id>/', BookingTrackingView.as_view(), name='booking-tracking'),
]
