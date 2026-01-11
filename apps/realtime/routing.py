"""
WebSocket URL routing for realtime app.
"""
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/bookings/<uuid:booking_id>/', consumers.BookingConsumer.as_asgi()),
    path('ws/notifications/', consumers.NotificationConsumer.as_asgi()),
]
