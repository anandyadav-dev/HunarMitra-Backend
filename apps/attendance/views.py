"""
Views for Attendance app.
"""
from django.conf import settings
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema

from apps.attendance.models import Attendance, AttendanceKiosk
from apps.attendance.serializers import (
    AttendanceSerializer,
    KioskAttendanceRequestSerializer
)
from django.contrib.auth import get_user_model

User = get_user_model()


class KioskAttendanceView(APIView):
    """
    POST endpoint for marking attendance via kiosk.
    
    Accepts worker_id and device_id, creates or updates attendance
    for the current date. Controlled by FEATURE_BIOMETRIC_STUB flag.
    """
    permission_classes = [AllowAny]  # Kiosk devices don't have user auth
    
    @extend_schema(
        request=KioskAttendanceRequestSerializer,
        responses={201: AttendanceSerializer},
        description="Mark worker attendance via kiosk (stub mode)"
    )
    def post(self, request):
        """Mark attendance for a worker."""
        
        # Check feature flag
        biometric_stub_enabled = getattr(
            settings,
            'FEATURE_BIOMETRIC_STUB',
            True
        )
        
        if not biometric_stub_enabled:
            return Response(
                {'detail': 'Biometric stub is not enabled'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate request
        serializer = KioskAttendanceRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        worker_id = serializer.validated_data['worker_id']
        device_id = serializer.validated_data.get('device_id')
        kiosk_id = serializer.validated_data.get('kiosk_id')
        
        # Get worker
        try:
            worker = User.objects.get(id=worker_id)
        except User.DoesNotExist:
            return Response(
                {'detail': 'Worker not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get kiosk if provided
        kiosk = None
        if kiosk_id:
            try:
                kiosk = AttendanceKiosk.objects.get(id=kiosk_id)
            except AttendanceKiosk.DoesNotExist:
                return Response(
                    {'detail': 'Kiosk not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Get today's date
        today = timezone.now().date()
        
        # Create or update attendance for today
        attendance, created = Attendance.objects.update_or_create(
            worker=worker,
            date=today,
            defaults={
                'kiosk': kiosk,
                'method': 'stub',
                'device_id': device_id,
            }
        )
        
        # Return response
        response_serializer = AttendanceSerializer(attendance)
        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        
        return Response(response_serializer.data, status=response_status)


class SiteAttendanceView(generics.ListAPIView):
    """
    GET endpoint for querying attendance by site/kiosk and date.
    
    Returns list of workers present at a specific site on a given date.
    """
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        parameters=[
            {
                'name': 'date',
                'in': 'query',
                'description': 'Date in YYYY-MM-DD format',
                'required': False,
                'schema': {'type': 'string', 'format': 'date'}
            }
        ],
        description="Get attendance records for a specific site/kiosk"
    )
    def get_queryset(self):
        """Filter attendance by kiosk and date."""
        kiosk_id = self.kwargs.get('kiosk_id')
        date_str = self.request.query_params.get('date')
        
        # Base queryset
        queryset = Attendance.objects.select_related('worker', 'kiosk')
        
        # Filter by kiosk
        if kiosk_id:
            queryset = queryset.filter(kiosk_id=kiosk_id)
        
        # Filter by date
        if date_str:
            try:
                from datetime import datetime
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                queryset = queryset.filter(date=date_obj)
            except ValueError:
                # Invalid date format, return empty queryset
                queryset = queryset.none()
        else:
            # Default to today if no date provided
            today = timezone.now().date()
            queryset = queryset.filter(date=today)
        
        return queryset.order_by('-timestamp')
