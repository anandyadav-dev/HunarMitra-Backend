"""
Serializers for Emergency app.
"""
from rest_framework import serializers
from .models import EmergencyRequest, EmergencyDispatchLog


class CreateEmergencyRequestSerializer(serializers.Serializer):
    """Serializer for creating emergency request."""
    
    contact_phone = serializers.CharField(max_length=20, help_text="Contact phone number")
    location = serializers.DictField(
        child=serializers.DecimalField(max_digits=9, decimal_places=6),
        help_text="Location object with 'lat' and 'lng' keys"
    )
    address = serializers.CharField(help_text="Human-readable address")
    service_id = serializers.UUIDField(required=False, allow_null=True, help_text="Service UUID")
    service_slug = serializers.CharField(required=False, allow_blank=True, help_text="Service slug (alternative to ID)")
    service_description = serializers.CharField(required=False, allow_blank=True, help_text="Custom service description")
    urgency_level = serializers.ChoiceField(
        choices=EmergencyRequest.URGENCY_CHOICES,
        default=EmergencyRequest.URGENCY_HIGH,
        help_text="Urgency level: low, medium, high"
    )
    site_id = serializers.UUIDField(required=False, allow_null=True, help_text="Related site ID (optional)")
    
    def validate_location(self, value):
        """Validate location has lat and lng."""
        if 'lat' not in value or 'lng' not in value:
            raise serializers.ValidationError("Location must include 'lat' and 'lng' fields")
        
        # Validate coordinate ranges
        lat = float(value['lat'])
        lng = float(value['lng'])
        
        if not (-90 <= lat <= 90):
            raise serializers.ValidationError("Latitude must be between -90 and 90")
        if not (-180 <= lng <= 180):
            raise serializers.ValidationError("Longitude must be between -180 and 180")
        
        return value


class EmergencyRequestSerializer(serializers.ModelSerializer):
    """Serializer for emergency request."""
    
    service_name = serializers.CharField(
        source='service_required.name',
        read_only=True,
        allow_null=True
    )
    assigned_worker_name = serializers.CharField(
        source='assigned_worker.user.get_full_name',
        read_only=True,
        allow_null=True
    )
    assigned_worker_phone = serializers.CharField(
        source='assigned_worker.user.phone',
        read_only=True,
        allow_null=True
    )
    dispatch_count = serializers.IntegerField(read_only=True, required=False)
    
    class Meta:
        model = EmergencyRequest
        fields = [
            'id',
            'created_by',
            'contact_phone',
            'site',
            'location_lat',
            'location_lng',
            'address_text',
            'service_required',
            'service_name',
            'service_description',
            'urgency_level',
            'status',
            'assigned_worker',
            'assigned_worker_name',
            'assigned_worker_phone',
            'assigned_contractor',
            'dispatch_count',
            'metadata',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EmergencyDispatchLogSerializer(serializers.ModelSerializer):
    """Serializer for dispatch log."""
    
    worker_name = serializers.CharField(source='worker.user.get_full_name', read_only=True)
    worker_phone = serializers.CharField(source='worker.user.phone', read_only=True)
    emergency_contact = serializers.CharField(source='emergency.contact_phone', read_only=True)
    
    class Meta:
        model = EmergencyDispatchLog
        fields = [
            'id',
            'emergency',
            'emergency_contact',
            'worker',
            'worker_name',
            'worker_phone',
            'attempt_time',
            'status',
            'response_time',
            'raw_response',
        ]
        read_only_fields = ['id', 'attempt_time']


class EmergencyDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with dispatch logs included."""
    
    service_name = serializers.CharField(
        source='service_required.name',
        read_only=True,
        allow_null=True
    )
    assigned_worker_name = serializers.CharField(
        source='assigned_worker.user.get_full_name',
        read_only=True,
        allow_null=True
    )
    dispatch_logs = EmergencyDispatchLogSerializer(many=True, read_only=True)
    
    class Meta:
        model = EmergencyRequest
        fields = [
            'id',
            'created_by',
            'contact_phone',
            'site',
            'location_lat',
            'location_lng',
            'address_text',
            'service_required',
            'service_name',
            'service_description',
            'urgency_level',
            'status',
            'assigned_worker',
            'assigned_worker_name',
            'assigned_contractor',
            'dispatch_logs',
            'metadata',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UpdateEmergencyStatusSerializer(serializers.Serializer):
    """Serializer for updating emergency status."""
    
    status = serializers.ChoiceField(
        choices=EmergencyRequest.STATUS_CHOICES,
        help_text="New status for emergency"
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional notes about status change"
    )
