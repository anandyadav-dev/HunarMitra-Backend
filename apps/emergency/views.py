"""
Views for Emergency app - urgent help requests API.
"""
from django.utils import timezone
from django.db import models
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema

from apps.emergency.models import EmergencyRequest, EmergencyDispatchLog
from apps.emergency.serializers import (
    CreateEmergencyRequestSerializer,
    EmergencyRequestSerializer,
    EmergencyDetailSerializer,
    UpdateEmergencyStatusSerializer,
    EmergencyDispatchLogSerializer,
)
from apps.emergency.rate_limit import check_emergency_rate_limit, record_emergency_attempt
from apps.notifications.models import TimelineEvent, Notification
from apps.core.pagination import StandardPagination


class EmergencyRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for emergency requests API.
    
    Supports:
    - Create emergency (with rate limiting)
    - List/filter emergencies
    - Accept/decline by workers
    - Update status (admin)
    """
    
    serializer_class = EmergencyRequestSerializer
    pagination_class = StandardPagination
    
    def get_permissions(self):
        """Allow anonymous to create, auth required for others."""
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        """Return emergencies based on user role."""
        queryset = EmergencyRequest.objects.select_related(
            'created_by',
            'service_required',
            'assigned_worker__user',
            'assigned_contractor'
        ).prefetch_related('dispatch_logs')
        
        user = self.request.user
        
        # Admin sees all
        if user.is_staff:
            return queryset
        
        # Worker sees emergencies they were notified about or assigned to
        if hasattr(user, 'worker_profile'):
            return queryset.filter(
                models.Q(dispatch_logs__worker=user.worker_profile) |
                models.Q(assigned_worker=user.worker_profile)
            ).distinct()
        
        # Contractor sees escalated emergencies
        if hasattr(user, 'contractor_profile'):
            return queryset.filter(assigned_contractor=user.contractor_profile)
        
        # Regular user (creator) sees their own
        return queryset.filter(created_by=user)
    
    def get_serializer_class(self):
        """Use DetailSerializer for retrieve action."""
        if self.action == 'retrieve':
            return EmergencyDetailSerializer
        return EmergencyRequestSerializer
    
    @extend_schema(
        request=CreateEmergencyRequestSerializer,
        responses={201: EmergencyRequestSerializer},
        description="Create emergency request with rate limiting"
    )
    def create(self, request):
        """
        POST /api/emergency/requests/
        
        Create emergency request. Rate limited to prevent abuse.
        Auto-dispatch if EMERGENCY_AUTO_ASSIGN is enabled.
        """
        from django.conf import settings
        
        serializer = CreateEmergencyRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        contact_phone = serializer.validated_data['contact_phone']
        
        # Rate limiting
        identifier = str(request.user.id) if request.user.is_authenticated else contact_phone
        check_emergency_rate_limit(identifier, settings.EMERGENCY_RATE_LIMIT_PER_MINUTE)
        
        # Extract validated data
        location = serializer.validated_data['location']
        
        # Create emergency request
        emergency = EmergencyRequest.objects.create(
            created_by=request.user if request.user.is_authenticated else None,
            contact_phone=contact_phone,
            location_lat=location['lat'],
            location_lng=location['lng'],
            address_text=serializer.validated_data['address'],
            service_required_id=serializer.validated_data.get('service_id'),
            service_description=serializer.validated_data.get('service_description', ''),
            urgency_level=serializer.validated_data['urgency_level'],
            site_id=serializer.validated_data.get('site_id'),
            status=EmergencyRequest.STATUS_OPEN
        )
        
        # Record attempt for analytics
        record_emergency_attempt(contact_phone, success=True)
        
        # Create timeline event
        TimelineEvent.objects.create(
            event_type=TimelineEvent.EVENT_TYPE_CUSTOM,
            actor_display=contact_phone,
            related_user=request.user if request.user.is_authenticated else None,
            payload={
                'event': 'emergency_created',
                'emergency_id': str(emergency.id),
                'urgency': emergency.urgency_level,
                'location': emergency.address_text
            }
        )
        
        # Trigger auto-dispatch if enabled
        dispatch_status = 'manual'
        
        if settings.EMERGENCY_AUTO_ASSIGN:
            try:
                from apps.emergency.tasks import process_emergency_dispatch
                # Enqueue Celery task
                process_emergency_dispatch.delay(str(emergency.id))
                dispatch_status = 'queued'
                emergency.metadata['dispatch_queued_at'] = timezone.now().isoformat()
                emergency.save(update_fields=['metadata', 'updated_at'])
            except Exception as e:
                # If Celery not available, log error
                emergency.metadata['dispatch_error'] = str(e)
                emergency.save(update_fields=['metadata', 'updated_at'])
        
        response_data = EmergencyRequestSerializer(emergency).data
        response_data['dispatch_status'] = dispatch_status
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        request=None,
        responses={200: EmergencyRequestSerializer},
        description="Worker accepts emergency request"
    )
    @action(detail=True, methods=['post'], url_path='accept')
    def accept(self, request, pk=None):
        """
        POST /api/emergency/requests/{id}/accept/
        
        Worker accepts emergency request.
        """
        emergency = self.get_object()
        
        if not hasattr(request.user, 'worker_profile'):
            return Response(
                {'error': 'Only workers can accept emergencies'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        worker = request.user.worker_profile
        
        # Check if already assigned
        if emergency.status in [EmergencyRequest.STATUS_ACCEPTED, EmergencyRequest.STATUS_RESOLVED]:
            return Response(
                {'error': 'Emergency already assigned or resolved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Assign worker
        emergency.assigned_worker = worker
        emergency.status = EmergencyRequest.STATUS_ACCEPTED
        emergency.metadata['accepted_at'] = timezone.now().isoformat()
        emergency.save(update_fields=['assigned_worker', 'status', 'metadata', 'updated_at'])
        
        # Update dispatch log
        EmergencyDispatchLog.objects.filter(
            emergency=emergency,
            worker=worker,
            status=EmergencyDispatchLog.STATUS_NOTIFIED
        ).update(
            status=EmergencyDispatchLog.STATUS_ACCEPTED,
            response_time=timezone.now()
        )
        
        # Create timeline event
        TimelineEvent.objects.create(
            event_type=TimelineEvent.EVENT_TYPE_CUSTOM,
            actor_display=worker.user.get_full_name() or worker.user.phone,
            related_user=worker.user,
            payload={
                'event': 'emergency_accepted',
                'emergency_id': str(emergency.id),
                'worker_id': str(worker.id)
            }
        )
        
        # Notify creator
        if emergency.created_by:
            Notification.objects.create(
                user=emergency.created_by,
                title='Emergency Accepted ✅',
                message=f'Worker {worker.user.get_full_name() or "a professional"} is on the way!',
                notification_type='emergency_update',
                metadata={'emergency_id': str(emergency.id)}
            )
        
        return Response(EmergencyRequestSerializer(emergency).data)
    
    @extend_schema(
        request=None,
        responses={200: dict},
        description="Worker declines emergency request"
    )
    @action(detail=True, methods=['post'], url_path='decline')
    def decline(self, request, pk=None):
        """
        POST /api/emergency/requests/{id}/decline/
        
        Worker declines emergency request.
        """
        emergency = self.get_object()
        
        if not hasattr(request.user, 'worker_profile'):
            return Response(
                {'error': 'Only workers can decline emergencies'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        worker = request.user.worker_profile
        
        # Update dispatch log
        updated = EmergencyDispatchLog.objects.filter(
            emergency=emergency,
            worker=worker,
            status=EmergencyDispatchLog.STATUS_NOTIFIED
        ).update(
            status=EmergencyDispatchLog.STATUS_DECLINED,
            response_time=timezone.now()
        )
        
        if updated == 0:
            return Response(
                {'error': 'No pending notification found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({'status': 'declined', 'emergency_id': str(emergency.id)})
    
    @extend_schema(
        request=UpdateEmergencyStatusSerializer,
        responses={200: EmergencyRequestSerializer},
        description="Update emergency status (admin/system only)"
    )
    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, pk=None):
        """
        PATCH /api/emergency/requests/{id}/status/
        
        Update emergency status. Admin or system only.
        """
        if not request.user.is_staff:
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        emergency = self.get_object()
        serializer = UpdateEmergencyStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_status = serializer.validated_data['status']
        notes = serializer.validated_data.get('notes', '')
        
        old_status = emergency.status
        emergency.status = new_status
        
        if notes:
            emergency.metadata['status_notes'] = emergency.metadata.get('status_notes', [])
            emergency.metadata['status_notes'].append({
                'timestamp': timezone.now().isoformat(),
                'from_status': old_status,
                'to_status': new_status,
                'notes': notes,
                'updated_by': request.user.username
            })
        
        emergency.save(update_fields=['status', 'metadata', 'updated_at'])
        
        # Create timeline event
        TimelineEvent.objects.create(
            event_type=TimelineEvent.EVENT_TYPE_CUSTOM,
            actor_display=request.user.get_full_name() or request.user.username,
            related_user=request.user,
            payload={
                'event': 'emergency_status_changed',
                'emergency_id': str(emergency.id),
                'old_status': old_status,
                'new_status': new_status
            }
        )
        
        return Response(EmergencyRequestSerializer(emergency).data)
