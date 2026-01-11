"""
Serializers for Booking API.
"""
from rest_framework import serializers
from .models import Booking
from apps.users.serializers import UserSerializer
from apps.workers.serializers import WorkerProfileSerializer
from apps.services.serializers import ServiceSerializer

class BookingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a booking."""
    
    class Meta:
        model = Booking
        fields = [
            'id', 'service', 'address', 'lat', 'lng', 
            'preferred_time', 'notes', 'estimated_price',
            'status', 'created_at'
        ]
        read_only_fields = ['id', 'status', 'created_at']

    def create(self, validated_data):
        # User is set in view
        validated_data['status'] = Booking.STATUS_REQUESTED
        return super().create(validated_data)


class BookingDetailSerializer(serializers.ModelSerializer):
    """Full detail serializer for bookings."""
    user = UserSerializer(read_only=True)
    worker = WorkerProfileSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'user', 'worker', 'service',
            'address', 'lat', 'lng',
            'preferred_time', 'notes',
            'estimated_price',
            'status', 'eta_minutes', 'tracking_url',
            'created_at', 'updated_at'
        ]


class BookingStatusSerializer(serializers.Serializer):
    """Serializer for status updates."""
    status = serializers.ChoiceField(choices=Booking.STATUS_CHOICES)
    eta_minutes = serializers.IntegerField(required=False, allow_null=True)
    
    def validate_status(self, value):
        # Basic validation handled by ChoiceField
        return value

class BookingAssignSerializer(serializers.Serializer):
    """Serializer for assigning a worker."""
    worker_id = serializers.UUIDField()
