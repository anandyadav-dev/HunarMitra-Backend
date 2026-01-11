"""
Views for Contractors app.
"""
from django.utils import timezone
from django.db.models import Count, Q
from django.core.cache import cache
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema

from apps.contractors.models import ContractorProfile
from apps.contractors.serializers import ContractorProfileSerializer, ContractorDashboardSerializer


class ContractorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for contractor registration and management.
    
    - POST: Register new contractor profile
    - GET: Retrieve contractor profiles
    - Dashboard action: Get dashboard summary
    """
    queryset = ContractorProfile.objects.select_related('user').all()
    serializer_class = ContractorProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """Allow any user to register (POST), require auth for others."""
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        """Create contractor profile using user from request payload."""
        # Use user from request payload instead of authenticated user
        serializer.save()
        serializer.save()
    
    @extend_schema(
        responses={200: ContractorDashboardSerializer},
        description="Get contractor dashboard summary with computed metrics"
    )
    @action(detail=True, methods=['get'], url_path='dashboard')
    def dashboard(self, request, pk=None):
        """
        Return dashboard summary with computed metrics.
        
        Metrics:
        - active_sites: Count of active kiosks for this contractor
        - workers_present_today: Count of workers with attendance today
        - pending_jobs: Count of jobs with status in ['open', 'assigned']
        """
        contractor = self.get_object()
        
        # Check cache first
        cache_key = f'contractor_dashboard_{contractor.id}'
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)
        
        # Get today's date
        today = timezone.now().date()
        
        # Compute metrics using ORM aggregates
        # 1. Active sites
        active_sites = contractor.kiosks.filter(is_active=True).count()
        
        # 2. Workers present today
        # Count distinct workers from attendance logs at contractor's kiosks today
        workers_present_today = contractor.kiosks.filter(
            is_active=True,
            logs__check_in__date=today
        ).values('logs__worker').distinct().count()
        
        # 3. Pending jobs
        # Count jobs with status in open/assigned
        pending_jobs = contractor.jobs.filter(
            status__in=['open', 'assigned']
        ).count()
        
        # Prepare response
        dashboard_data = {
            'active_sites': active_sites,
            'workers_present_today': workers_present_today,
            'pending_jobs': pending_jobs
        }
        
        # Cache for 60 seconds
        cache.set(cache_key, dashboard_data, 60)
        
        serializer = ContractorDashboardSerializer(dashboard_data)
        return Response(serializer.data)
