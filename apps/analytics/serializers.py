"""
Analytics serializers for event ingestion and validation.
"""
from rest_framework import serializers
from django.conf import settings
import json

from .models import Event


class EventIngestionSerializer(serializers.Serializer):
    """Serializer for single event ingestion."""
    
    event_type = serializers.CharField(max_length=50)
    anonymous_id = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=True,
        allow_blank=True
    )
    source = serializers.ChoiceField(
        choices=Event.SOURCE_CHOICES,
        default=Event.SOURCE_WEB,
        required=False
    )
    payload = serializers.JSONField(default=dict, required=False)
    
    def validate_payload(self, value):
        """Validate payload size."""
        if not value:
            return {}
        
        payload_str = json.dumps(value)
        payload_size = len(payload_str.encode('utf-8'))
        
        max_size = settings.ANALYTICS_MAX_EVENT_SIZE
        if payload_size > max_size:
            raise serializers.ValidationError(
                f"Payload size {payload_size} bytes exceeds limit of {max_size} bytes"
            )
        
        return value


class BulkEventIngestionSerializer(serializers.Serializer):
    """Serializer for bulk event ingestion."""
    
    events = EventIngestionSerializer(many=True)
    
    def validate_events(self, value):
        """Validate events list is not empty."""
        if not value:
            raise serializers.ValidationError("Events list cannot be empty")
        
        if len(value) > 100:
            raise serializers.ValidationError("Maximum 100 events per bulk request")
        
        return value


class EventSerializer(serializers.ModelSerializer):
    """Serializer for Event model (read-only)."""
    
    user_phone = serializers.CharField(source='user.phone', read_only=True, allow_null=True)
    
    class Meta:
        model = Event
        fields = [
            'id', 'user', 'user_phone', 'anonymous_id', 'event_type', 'source',
            'payload', 'ip_address', 'user_agent', 'created_at'
        ]
        read_only_fields = fields
