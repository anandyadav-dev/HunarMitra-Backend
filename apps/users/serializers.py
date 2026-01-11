"""
Serializers for authentication and user management.
"""

from rest_framework import serializers
from .models import User
from django.core.validators import RegexValidator


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User details."""
    class Meta:
        model = User
        fields = [
            'id', 'phone', 'role', 'first_name', 'last_name',
            'email', 'profile_picture', 'is_phone_verified',
            'is_active', 'date_joined'
        ]
        read_only_fields = ['id', 'phone', 'is_phone_verified', 'date_joined']


class RequestOTPSerializer(serializers.Serializer):
    """Serializer for requesting an OTP."""
    phone = serializers.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )
    role = serializers.ChoiceField(
        choices=[
            ('worker', 'Worker'),
            ('contractor', 'Contractor'),
            ('employer', 'Employer')
        ],
        required=False,
        default='worker'
    )


class RequestOTPResponseSerializer(serializers.Serializer):
    """Response serializer for OTP request."""
    request_id = serializers.UUIDField()
    ttl = serializers.IntegerField()
    message = serializers.CharField()
    is_existing_user = serializers.BooleanField()
    # dev_otp only included in dev mode, handled by view logic


class VerifyOTPSerializer(serializers.Serializer):
    """Serializer for verifying OTP."""
    request_id = serializers.UUIDField()
    otp = serializers.CharField(min_length=4, max_length=6)


class VerifyOTPResponseSerializer(serializers.Serializer):
    """Response serializer for successful OTP verification."""
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()
    is_new_user = serializers.BooleanField()
