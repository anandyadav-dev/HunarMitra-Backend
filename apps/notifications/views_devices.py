"""
Views for device registration and management.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from drf_spectacular.utils import extend_schema

from apps.notifications.models import Device
from apps.notifications.serializers import (
    DeviceSerializer,
    RegisterDeviceSerializer,
    UnregisterDeviceSerializer,
)
from apps.users.models import User


class DeviceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for device management.
    
    Supports:
    - Device registration (upsert by registration_token)
    - Device unregistration (deactivation)
    - List user devices
    """
    
    serializer_class = DeviceSerializer
    
    def get_permissions(self):
        """Allow anyone to register, auth required for others."""
        if self.action == 'register':
            return [AllowAny()]
        elif self.action in ['list', 'retrieve', 'unregister']:
            return [IsAuthenticated()]
        return [IsAdminUser()]
    
    def get_queryset(self):
        """Return user's devices or all if admin."""
        if self.request.user.is_staff:
            return Device.objects.all()
        return Device.objects.filter(user=self.request.user)
    
    @extend_schema(
        request=RegisterDeviceSerializer,
        responses={201: DeviceSerializer},
        description="Register or update device for push notifications"
    )
    @action(detail=False, methods=['post'], url_path='register')
    def register(self, request):
        """
        POST /api/notifications/devices/register/
        
        Register or update device. Upsert by registration_token.
        """
        serializer = RegisterDeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['registration_token']
        platform = serializer.validated_data['platform']
        metadata = serializer.validated_data.get('metadata', {})
        
        # Determine user
        user = None
        if request.user.is_authenticated:
            user = request.user
        elif 'user_id' in serializer.validated_data:
            # Admin can associate device with user_id
            if request.user.is_authenticated and request.user.is_staff:
                try:
                    user = User.objects.get(id=serializer.validated_data['user_id'])
                except User.DoesNotExist:
                    return Response(
                        {'error': 'User not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
        
        # Upsert device
        device, created = Device.objects.update_or_create(
            registration_token=token,
            defaults={
                'user': user,
                'platform': platform,
                'metadata': metadata,
                'is_active': True
            }
        )
        
        return Response(
            DeviceSerializer(device).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
    
    @extend_schema(
        request=UnregisterDeviceSerializer,
        responses={200: dict},
        description="Deactivate device to stop receiving push notifications"
    )
    @action(detail=False, methods=['post'], url_path='unregister')
    def unregister(self, request):
        """
        POST /api/notifications/devices/unregister/
        
        Deactivate device.
        """
        serializer = UnregisterDeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['registration_token']
        
        # Deactivate device(s) with this token
        updated = Device.objects.filter(registration_token=token).update(is_active=False)
        
        if updated == 0:
            return Response(
                {'error': 'Device not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({
            'status': 'unregistered',
            'devices_updated': updated
        })
