"""
Serializers for Attendance app.
"""
from rest_framework import serializers
from apps.attendance.models import Attendance, AttendanceKiosk
from django.contrib.auth import get_user_model

User = get_user_model()


class AttendanceSerializer(serializers.ModelSerializer):
    """Serializer for Attendance records."""
    
    worker_phone = serializers.CharField(source='worker.phone', read_only=True)
    kiosk_name = serializers.CharField(source='kiosk.location_name', read_only=True)
    
    class Meta:
        model = Attendance
        fields = [
            'id', 'worker', 'worker_phone', 'kiosk', 'kiosk_name',
            'method', 'device_id', 'date', 'timestamp', 'created_at'
        ]
        read_only_fields = ['id', 'timestamp', 'created_at']


class KioskAttendanceRequestSerializer(serializers.Serializer):
    """Serializer for kiosk attendance request."""
    
    worker_id = serializers.UUIDField(
        help_text="UUID of the worker marking attendance"
    )
    device_id = serializers.CharField(
        max_length=64,
        required=False,
        allow_blank=True,
        help_text="Device identifier (e.g., KIOSK_001)"
    )
    kiosk_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="UUID of the kiosk (optional)"
    )
