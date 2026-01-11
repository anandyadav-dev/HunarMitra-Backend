"""
Serializers for Notifications app.
"""
from rest_framework import serializers
from .models import Notification, TimelineEvent


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications."""
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'title', 'message', 'type', 'data',
            'is_read', 'channel', 'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'metadata']


class TimelineEventSerializer(serializers.ModelSerializer):
    """Serializer for timeline events."""
    
    class Meta:
        model = TimelineEvent
        fields = [
            'id', 'booking', 'job', 'event_type', 'actor_display',
            'payload', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class CreateTestNotificationSerializer(serializers.Serializer):
    """Serializer for creating test notifications (admin only)."""
    
    user_id = serializers.UUIDField(required=False, allow_null=True)
    title = serializers.CharField(max_length=255)
    message = serializers.CharField()
    type = serializers.ChoiceField(
        choices=Notification.TYPE_CHOICES,
        default=Notification.TYPE_SYSTEM
    )
    channel = serializers.ChoiceField(
        choices=Notification.CHANNEL_CHOICES,
        default=Notification.CHANNEL_IN_APP
    )
    data = serializers.JSONField(required=False, default=dict)


class DeviceSerializer(serializers.ModelSerializer):
    """Serializer for device registration."""
    
    user_phone = serializers.CharField(source='user.phone', read_only=True, allow_null=True)
    
    class Meta:
        from apps.notifications.models import Device
        model = Device
        fields = [
            'id', 'user', 'user_phone', 'platform', 'registration_token',
            'last_seen', 'is_active', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'last_seen', 'created_at']


class RegisterDeviceSerializer(serializers.Serializer):
    """Serializer for device registration endpoint."""
    
    from apps.notifications.models import Device
    registration_token = serializers.CharField(max_length=500, help_text="FCM registration token")
    platform = serializers.ChoiceField(choices=Device.PLATFORM_CHOICES, help_text="Device platform")
    metadata = serializers.JSONField(required=False, default=dict, help_text="Device info (optional)")
    user_id = serializers.IntegerField(required=False, allow_null=True, help_text="User ID (admin only)")


class UnregisterDeviceSerializer(serializers.Serializer):
    """Serializer for device unregister endpoint."""
    
    registration_token = serializers.CharField(max_length=500, help_text="FCM registration token to deactivate")


class OutgoingPushSerializer(serializers.ModelSerializer):
    """Serializer for outgoing push logs."""
    
    notification_title = serializers.CharField(source='notification.title', read_only=True, allow_null=True)
    device_platform = serializers.CharField(source='device.get_platform_display', read_only=True, allow_null=True)
   
    class Meta:
        from apps.notifications.models import OutgoingPush
        model = OutgoingPush
        fields = [
            'id', 'notification', 'notification_title', 'device', 'device_platform',
            'payload', 'provider_response', 'status', 'attempts',
            'last_attempt_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
