"""
API Views for Jobs.
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from decimal import Decimal

from .models import Job, JobApplication
from .serializers import JobSerializer, JobApplicationSerializer
from apps.workers.models import WorkerProfile
from apps.notifications.models import Notification
from apps.realtime import publish_event
from apps.core.pagination import StandardPagination


class JobViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Job CRUD and application management.
    
    List endpoint supports:
    - Pagination: page, per_page
    - Filters: status, min_price, max_price, service_id
    - Sorting: created_at (default), price
    """
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = StandardPagination
    
    def get_queryset(self):
        """Build filtered and sorted queryset."""
        queryset = Job.objects.select_related('poster', 'service', 'contractor').all()
        
        # Only apply filters for list action
        if self.action == 'list':
            # Filter by status
            job_status = self.request.query_params.get('status')
            if job_status:
                queryset = queryset.filter(status=job_status)
            
            # Filter by price range
            min_price = self.request.query_params.get('min_price')
            max_price = self.request.query_params.get('max_price')
            
            if min_price:
                try:
                    queryset = queryset.filter(budget__gte=Decimal(min_price))
                except (ValueError, TypeError):
                    pass
            
            if max_price:
                try:
                    queryset = queryset.filter(budget__lte=Decimal(max_price))
                except (ValueError, TypeError):
                    pass
            
            # Filter by service
            service_id = self.request.query_params.get('service_id')
            if service_id:
                queryset = queryset.filter(service_id=service_id)
            
            # Apply sorting
            sort_key = self.request.query_params.get('sort', 'created_at')
            
            if sort_key == 'price':
                queryset = queryset.order_by('budget')
            elif sort_key == 'created_at':
                queryset = queryset.order_by('-created_at')
            else:
                # Default: newest first
                queryset = queryset.order_by('-created_at')
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """
        Worker applies for a job.
        """
        job = self.get_object()
        user = request.user
        
        # Verify user is a worker
        try:
            worker_profile = WorkerProfile.objects.get(user=user)
        except WorkerProfile.DoesNotExist:
            return Response(
                {"error": "Only workers can apply for jobs."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create application
        try:
            application = JobApplication.objects.create(
                job=job,
                worker=worker_profile,
                status=JobApplication.STATUS_APPLIED
            )
        except IntegrityError:
            return Response(
                {"error": "You have already applied for this job."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create notification for job poster
        Notification.objects.create(
            user=job.poster,
            notification_type='job_application',
            title='New Job Application',
            message=f'{user.get_full_name()} applied for "{job.title}"',
            data={'job_id': str(job.id), 'application_id': str(application.id)}
        )
        
        # Publish realtime event
        publish_event(
            f"user_{job.poster.id}",
            {
                "type": "job_application",
                "action": "applied",
                "job_id": str(job.id),
                "application_id": str(application.id),
                "worker_name": user.get_full_name()
            }
        )
        
        serializer = JobApplicationSerializer(application)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], url_path='applications/(?P<application_id>[^/.]+)/accept')
    def accept_application(self, request, pk=None, application_id=None):
        """
        Accept a job application (Worker or Admin only).
        """
        job = self.get_object()
        application = get_object_or_404(JobApplication, id=application_id, job=job)
        
        # Permission check: Worker (self) or Admin
        is_worker = hasattr(request.user, 'worker_profile') and request.user.worker_profile == application.worker
        is_admin = request.user.is_staff or request.user.is_superuser
        
        if not (is_worker or is_admin):
            return Response(
                {"error": "Only the applicant or admin can accept this application."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update application
        application.status = JobApplication.STATUS_ACCEPTED
        application.save()
        
        # Assign worker to job
        job.assigned_worker = application.worker.user
        job.status = 'assigned'
        job.save()
        
        # Create notification for employer
        Notification.objects.create(
            user=job.poster,
            notification_type='application_accepted',
            title='Application Accepted',
            message=f'{application.worker.user.get_full_name()} accepted your job "{job.title}"',
            data={'job_id': str(job.id), 'application_id': str(application.id)}
        )
        
        # Create notification for worker
        Notification.objects.create(
            user=application.worker.user,
            notification_type='job_assigned',
            title='Job Assigned',
            message=f'You have been assigned to "{job.title}"',
            data={'job_id': str(job.id)}
        )
        
        # Publish realtime events
        publish_event(
            f"user_{job.poster.id}",
            {
                "type": "job_application",
                "action": "accepted",
                "job_id": str(job.id),
                "application_id": str(application.id)
            }
        )
        
        publish_event(
            f"user_{application.worker.user.id}",
            {
                "type": "job_assigned",
                "job_id": str(job.id),
                "job_title": job.title
            }
        )
        
        return Response(JobApplicationSerializer(application).data)
    
    @action(detail=True, methods=['post'], url_path='applications/(?P<application_id>[^/.]+)/decline')
    def decline_application(self, request, pk=None, application_id=None):
        """
        Decline a job application (Worker or Admin only).
        """
        job = self.get_object()
        application = get_object_or_404(JobApplication, id=application_id, job=job)
        
        # Permission check: Worker (self) or Admin
        is_worker = hasattr(request.user, 'worker_profile') and request.user.worker_profile == application.worker
        is_admin = request.user.is_staff or request.user.is_superuser
        
        if not (is_worker or is_admin):
            return Response(
                {"error": "Only the applicant or admin can decline this application."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update application
        application.status = JobApplication.STATUS_DECLINED
        application.save()
        
        # Create notification for employer
        Notification.objects.create(
            user=job.poster,
            notification_type='application_declined',
            title='Application Declined',
            message=f'{application.worker.user.get_full_name()} declined your job "{job.title}"',
            data={'job_id': str(job.id), 'application_id': str(application.id)}
        )
        
        # Publish realtime event
        publish_event(
            f"user_{job.poster.id}",
            {
                "type": "job_application",
                "action": "declined",
                "job_id": str(job.id),
                "application_id": str(application.id)
            }
        )
        
        return Response(JobApplicationSerializer(application).data)
