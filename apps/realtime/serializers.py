"""
Serializers for realtime tracking.
"""
from rest_framework import serializers
from django.utils import timezone


class TrackingUpdateSerializer(serializers.Serializer):
    """Serializer for location tracking updates."""
    
    lat = serializers.FloatField(
        min_value=-90.0,
        max_value=90.0,
        help_text="Latitude coordinate"
    )
    lng = serializers.FloatField(
        min_value=-180.0,
        max_value=180.0,
        help_text="Longitude coordinate"
    )
    timestamp = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="Timestamp of the location update (defaults to now)"
    )
    
    def validate_timestamp(self, value):
        """Validate timestamp is not in the future."""
        if value and value > timezone.now():
            raise serializers.ValidationError("Timestamp cannot be in the future")
        return value
