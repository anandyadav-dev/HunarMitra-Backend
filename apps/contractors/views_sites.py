"""
Views for Site Management - construction sites, worker assignment, and attendance.
"""
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Q, Prefetch
from django.utils.dateparse import parse_date
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.contractors.models import Site, SiteAssignment, SiteAttendance
from apps.contractors.serializers import (
    SiteSerializer,
    SiteAssignmentSerializer,
    SiteAttendanceSerializer,
    MarkAttendanceSerializer,
    AssignWorkerSerializer,
    SiteDashboardSerializer,
)
from apps.notifications.models import TimelineEvent
from apps.core.pagination import StandardPagination


class IsContractorOrAdmin(IsAuthenticated):
    """Permission: contractor owner or admin only."""
    
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.is_staff or hasattr(request.user, 'contractor_profile')
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        # Contractor can only access their own sites
        if hasattr(obj, 'contractor'):
            return obj.contractor.user == request.user
        return False


class SiteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing construction sites.
    
    Provides CRUD operations, worker assignment, attendance tracking,
    and dashboard metrics.
    """
    serializer_class = SiteSerializer
    permission_classes = [IsContractorOrAdmin]
    pagination_class = StandardPagination
    
    def get_queryset(self):
        """Return sites for contractor (or all if admin)."""
        queryset = Site.objects.select_related('contractor__user').all()
        
        if self.request.user.is_staff:
            return queryset
        
        if hasattr(self.request.user, 'contractor_profile'):
            return queryset.filter(contractor=self.request.user.contractor_profile)
        
        return queryset.none()
    
    def get_serializer_context(self):
        """Add request to serializer context."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_create(self, serializer):
        """Set contractor from authenticated user."""
        if hasattr(self.request.user, 'contractor_profile'):
            serializer.save(contractor=self.request.user.contractor_profile)
        else:
            serializer.save()
    
    def list(self, request, *args, **kwargs):
        """List sites with worker count annotation."""
        queryset = self.filter_queryset(self.get_queryset())
        
        # Annotate with assigned workers count
        queryset = queryset.annotate(
            assigned_workers_count=Count('assignments', filter=Q(assignments__is_active=True))
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        request=AssignWorkerSerializer,
        responses={200: SiteAssignmentSerializer},
        description="Assign a worker to this site"
    )
    @action(detail=True, methods=['post'], url_path='assign')
    def assign_worker(self, request, pk=None):
        """
        POST /api/sites/{id}/assign/
        
        Assign a worker to this construction site.
        Body: {"worker_id": "uuid", "role_on_site": "Mason"}
        """
        site = self.get_object()
        serializer = AssignWorkerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        worker_id = serializer.validated_data['worker_id']
        role = serializer.validated_data.get('role_on_site', '')
        
        # Get or create assignment
        assignment, created = SiteAssignment.objects.get_or_create(
            site=site,
            worker_id=worker_id,
            defaults={
                'assigned_by': request.user,
                'role_on_site': role,
                'is_active': True
            }
        )
        
        if not created:
            # Reactivate if was inactive
            assignment.is_active = True
            assignment.role_on_site = role
            assignment.save()
        
        # Create timeline event
        TimelineEvent.objects.create(
            event_type=TimelineEvent.EVENT_TYPE_CUSTOM,
            actor_display=request.user.get_full_name() or request.user.phone,
            related_user=request.user,
            payload={
                'event': 'worker_assigned_to_site',
                'site_id': str(site.id),
                'site_name': site.name,
                'worker_id': str(worker_id),
                'role': role
            }
        )
        
        response_serializer = SiteAssignmentSerializer(assignment)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'], url_path='workers')
    def list_workers(self, request, pk=None):
        """
        GET /api/sites/{id}/workers/
        
        List all workers assigned to this site.
        """
        site = self.get_object()
        assignments = site.assignments.filter(is_active=True).select_related(
            'worker__user', 'assigned_by'
        )
        
        serializer = SiteAssignmentSerializer(assignments, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        request=MarkAttendanceSerializer,
        responses={200: SiteAttendanceSerializer},
        description="Mark attendance for a worker at this site"
    )
    @action(detail=True, methods=['post'], url_path='attendance')
    def mark_attendance(self, request, pk=None):
        """
        POST /api/sites/{id}/attendance/
        
        Mark attendance for a worker.
        Body: {
            "worker_id": "uuid",
            "status": "present",
            "checkin_time": "2026-01-03T09:00:00Z",
            "date": "2026-01-03"
        }
        """
        site = self.get_object()
        serializer = MarkAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        worker_id = serializer.validated_data['worker_id']
        attendance_status = serializer.validated_data['status']
        checkin_time = serializer.validated_data.get('checkin_time')
        checkout_time = serializer.validated_data.get('checkout_time')
        notes = serializer.validated_data.get('notes', '')
        attendance_date = serializer.validated_data.get('date') or timezone.now().date()
        
        # Create or update attendance
        attendance, created = SiteAttendance.objects.update_or_create(
            site=site,
            worker_id=worker_id,
            attendance_date=attendance_date,
            defaults={
                'status': attendance_status,
                'checkin_time': checkin_time or (timezone.now() if attendance_status == 'present' else None),
                'checkout_time': checkout_time,
                'marked_by': request.user,
                'notes': notes
            }
        )
        
        # Create timeline event if checked in
        if attendance_status == SiteAttendance.STATUS_PRESENT:
            TimelineEvent.objects.create(
                event_type=TimelineEvent.EVENT_TYPE_CUSTOM,
                actor_display=attendance.worker.user.get_full_name() or attendance.worker.user.phone,
                related_user=attendance.worker.user,
                payload={
                    'event': 'worker_checked_in',
                    'site_id': str(site.id),
                    'site_name': site.name,
                    'checkin_time': checkin_time.isoformat() if checkin_time else None
                }
            )
        
        response_serializer = SiteAttendanceSerializer(attendance)
        return Response(response_serializer.data, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)
    
    @extend_schema(
        parameters=[
            OpenApiParameter(name='date', description='Date in YYYY-MM-DD format', required=False, type=str)
        ],
        responses={200: SiteAttendanceSerializer(many=True)},
        description="Get attendance records for a specific date"
    )
    @action(detail=True, methods=['get'], url_path='attendance')
    def get_attendance(self, request, pk=None):
        """
        GET /api/sites/{id}/attendance/?date=2026-01-03
        
        Get attendance records for a specific date (defaults to today).
        """
        site = self.get_object()
        date_str = request.query_params.get('date')
        
        if date_str:
            attendance_date = parse_date(date_str)
            if not attendance_date:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            attendance_date = timezone.now().date()
        
        attendance_records = SiteAttendance.objects.filter(
            site=site,
            attendance_date=attendance_date
        ).select_related('worker__user', 'marked_by')
        
        serializer = SiteAttendanceSerializer(attendance_records, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        parameters=[
            OpenApiParameter(name='date', description='Date in YYYY-MM-DD format', required=False, type=str)
        ],
        responses={200: SiteDashboardSerializer},
        description="Get aggregated dashboard metrics for a site"
    )
    @action(detail=True, methods=['get'], url_path='dashboard')
    def dashboard(self, request, pk=None):
        """
        GET /api/sites/{id}/dashboard/?date=2026-01-03
        
        Get aggregated metrics for site dashboard.
        Returns:
        - total_assigned: Total active workers assigned
        - present_count: Workers marked present
        - absent_count: Workers marked absent
        - attendance_rate: Percentage present
        - on_site_now_count: Workers currently on site
        - pending_jobs_count: Pending jobs for this site
        - recent_timeline: Recent events
        """
        site = self.get_object()
        date_str = request.query_params.get('date')
        
        if date_str:
            target_date = parse_date(date_str)
            if not target_date:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            target_date = timezone.now().date()
        
        # 1. Total assigned workers
        total_assigned = site.assignments.filter(is_active=True).count()
        
        # 2. Attendance for the date
        attendance_records = SiteAttendance.objects.filter(
            site=site,
            attendance_date=target_date
        )
        
        present_count = attendance_records.filter(status=SiteAttendance.STATUS_PRESENT).count()
        absent_count = attendance_records.filter(status=SiteAttendance.STATUS_ABSENT).count()
        half_day_count = attendance_records.filter(status=SiteAttendance.STATUS_HALF_DAY).count()
        on_leave_count = attendance_records.filter(status=SiteAttendance.STATUS_ON_LEAVE).count()
        
        # 3. Attendance rate
        attendance_rate = (present_count / total_assigned * 100) if total_assigned > 0 else 0.0
        
        # 4. Workers on site now (checked in within last 12 hours, not checked out)
        cutoff_time = timezone.now() - timedelta(hours=12)
        on_site_now_count = attendance_records.filter(
            status=SiteAttendance.STATUS_PRESENT,
            checkin_time__gte=cutoff_time,
            checkout_time__isnull=True
        ).count()
        
        # 5. Pending jobs (if Booking model has site FK - for now return 0)
        # This would need a site FK on Booking model
        pending_jobs_count = 0
        try:
            from apps.bookings.models import Booking
            if hasattr(Booking, 'site'):
                pending_jobs_count = Booking.objects.filter(
                    site=site,
                    status__in=['requested', 'confirmed']
                ).count()
        except Exception:
            pass
        
        # 6. Recent timeline events
        recent_timeline = TimelineEvent.objects.filter(
            Q(payload__site_id=str(site.id)) | Q(payload__site_name=site.name)
        ).order_by('-created_at')[:10]
        
        timeline_data = [{
            'event_type': event.event_type,
            'actor': event.actor_display,
            'timestamp': event.created_at.isoformat(),
            'details': event.payload
        } for event in recent_timeline]
        
        data = {
            'date': target_date,
            'total_assigned': total_assigned,
            'present_count': present_count,
            'absent_count': absent_count,
            'half_day_count': half_day_count,
            'on_leave_count': on_leave_count,
            'attendance_rate': round(attendance_rate, 2),
            'on_site_now_count': on_site_now_count,
            'pending_jobs_count': pending_jobs_count,
            'recent_timeline': timeline_data
        }
        
        serializer = SiteDashboardSerializer(data)
        return Response(serializer.data)
