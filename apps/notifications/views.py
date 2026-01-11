"""
API Views for Notifications app.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.conf import settings

from .models import Notification, TimelineEvent
from .serializers import (
    NotificationSerializer,
    TimelineEventSerializer,
    CreateTestNotificationSerializer
)
from apps.bookings.models import Booking


class NotificationPagination(PageNumberPagination):
    """Pagination for notifications."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for user notifications."""
    
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    pagination_class = NotificationPagination
    
    def get_queryset(self):
        """Return notifications for current user."""
        queryset = Notification.objects.filter(user=self.request.user)
        
        # Apply filters
        is_read = self.request.query_params.get('is_read')
        notification_type = self.request.query_params.get('type')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == 'true')
        
        if notification_type:
            queryset = queryset.filter(type=notification_type)
        
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['patch'])
    def mark_read(self, request, pk=None):
        """Mark single notification as read."""
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=['is_read', 'updated_at'])
        
        return Response({
            'status': 'success',
            'message': 'Notification marked as read'
        })
    
    @action(detail=False, methods=['patch'])
    def mark_all_read(self, request):
        """Mark all user notifications as read."""
        count = self.get_queryset().update(is_read=True)
        
        return Response({
            'status': 'success',
            'count': count,
            'message': f'{count} notifications marked as read'
        })


class BookingTimelineView(APIView):
    """Get timeline events for a booking."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, booking_id):
        """
        Retrieve chronological timeline events for a booking.
        
        Returns events in reverse chronological order (most recent first).
        """
        # Verify user has access to this booking
        booking = get_object_or_404(
            Booking,
            id=booking_id
        )
        
        # Check permissions: owner, assigned worker, contractor, or admin
        is_owner = booking.user == request.user
        is_worker = booking.worker and booking.worker.user == request.user
        is_admin = request.user.is_staff or request.user.is_superuser
        
        if not (is_owner or is_worker or is_admin):
            return Response(
                {'error': 'You do not have access to this booking timeline'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get timeline events
        events = TimelineEvent.objects.filter(
            booking_id=booking_id
        ).order_by('-created_at')
        
        serializer = TimelineEventSerializer(events, many=True)
        
        return Response({
            'booking_id': str(booking_id),
            'events': serializer.data,
            'count': events.count()
        })


class CreateTestNotificationView(APIView):
    """Create a test notification (admin only)."""
    
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        """
        Create a test notification for debugging/verification.
        
        Body:
            - user_id (optional): UUID of recipient
            - title: Notification title
            - message: Notification message
            - type: Notification type (default: system)
            - channel: Delivery channel (default: in_app)
            - data: Additional JSON payload
        """
        if not settings.ENABLE_NOTIFICATIONS:
            return Response(
                {'error': 'Notifications are disabled'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        serializer = CreateTestNotificationSerializer(data=request.data)
        
        if serializer.is_valid():
            user_id = serializer.validated_data.get('user_id')
            
            # Get user if specified
            user = None
            if user_id:
                from apps.users.models import User
                user = get_object_or_404(User, id=user_id)
            
            # Create notification
            notification = Notification.objects.create(
                user=user,
                title=serializer.validated_data['title'],
                message=serializer.validated_data['message'],
                type=serializer.validated_data.get('type', Notification.TYPE_SYSTEM),
                channel=serializer.validated_data.get('channel', Notification.CHANNEL_IN_APP),
                data=serializer.validated_data.get('data', {})
            )
            
            # Optionally trigger push notification task
            if notification.channel == Notification.CHANNEL_PUSH:
                from .tasks import send_push_notification
                send_push_notification(notification.id)
            
            return Response(
                NotificationSerializer(notification).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
