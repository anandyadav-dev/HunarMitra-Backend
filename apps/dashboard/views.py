"""
Dashboard API views - Role-based summary endpoints.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status as http_status
from drf_spectacular.utils import extend_schema, OpenApiResponse
import logging

from .services import (
    worker_summary,
    employer_summary,
    contractor_summary,
    admin_summary
)
from .caching import get_with_stale_fallback, clear_dashboard_cache

logger = logging.getLogger(__name__)


class WorkerDashboardView(APIView):
    """
    Worker dashboard summary endpoint.
    
    Returns minimal metrics for worker dashboard tiles.
    """
    
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get worker dashboard summary",
        description="Returns minimal metrics for worker dashboard (jobs, availability, earnings, badges)",
        responses={
            200: OpenApiResponse(description="Worker dashboard data"),
            400: OpenApiResponse(description="User is not a worker"),
        }
    )
    def get(self, request):
        """
        GET /api/dashboard/worker/
        
        Returns worker-specific dashboard metrics.
        """
        # Check if user is a worker
        if not hasattr(request.user, 'worker_profile'):
            return Response(
                {'error': 'User is not a worker'},
                status=http_status.HTTP_400_BAD_REQUEST
            )
        
        try:
            data = get_with_stale_fallback(
                'worker',
                lambda: worker_summary(request.user),
                user_id=request.user.id
            )
            return Response(data)
        except Exception as e:
            logger.error(f"Worker dashboard error: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to fetch dashboard'},
                status=http_status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EmployerDashboardView(APIView):
    """
    Employer dashboard summary endpoint.
    
    Returns minimal metrics for employer dashboard tiles.
    """
    
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get employer dashboard summary",
        description="Returns minimal metrics for employer dashboard (bookings, emergencies)",
        responses={200: OpenApiResponse(description="Employer dashboard data")}
    )
    def get(self, request):
        """
        GET /api/dashboard/employer/
        
        Returns employer-specific dashboard metrics.
        """
        try:
            data = get_with_stale_fallback(
                'employer',
                lambda: employer_summary(request.user),
                user_id=request.user.id
            )
            return Response(data)
        except Exception as e:
            logger.error(f"Employer dashboard error: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to fetch dashboard'},
                status=http_status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ContractorDashboardView(APIView):
    """
    Contractor dashboard summary endpoint.
    
    Returns minimal metrics for contractor dashboard tiles.
    """
    
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get contractor dashboard summary",
        description="Returns minimal metrics for contractor dashboard (sites, attendance, jobs)",
        responses={
            200: OpenApiResponse(description="Contractor dashboard data"),
            400: OpenApiResponse(description="User is not a contractor"),
        }
    )
    def get(self, request):
        """
        GET /api/dashboard/contractor/
        
        Returns contractor-specific dashboard metrics.
        """
        # Check if user is a contractor
        if not hasattr(request.user, 'contractor_profile'):
            return Response(
                {'error': 'User is not a contractor'},
                status=http_status.HTTP_400_BAD_REQUEST
            )
        
        try:
            data = get_with_stale_fallback(
                'contractor',
                lambda: contractor_summary(request.user),
                user_id=request.user.id
            )
            return Response(data)
        except Exception as e:
            logger.error(f"Contractor dashboard error: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to fetch dashboard'},
                status=http_status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdminDashboardView(APIView):
    """
    Admin dashboard global metrics endpoint.
    
    Returns system-wide statistics.
    """
    
    permission_classes = [IsAdminUser]
    
    @extend_schema(
        summary="Get admin dashboard summary",
        description="Returns global system metrics for admin dashboard",
        responses={200: OpenApiResponse(description="Admin dashboard data")}
    )
    def get(self, request):
        """
        GET /api/dashboard/admin/
        
        Returns global admin dashboard metrics.
        """
        try:
            data = get_with_stale_fallback(
                'admin',
                lambda: admin_summary()
            )
            return Response(data)
        except Exception as e:
            logger.error(f"Admin dashboard error: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to fetch dashboard'},
                status=http_status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ClearDashboardCacheView(APIView):
    """
    Admin endpoint to clear dashboard cache.
    
    Useful for debugging or forcing fresh data.
    """
    
    permission_classes = [IsAdminUser]
    
    @extend_schema(
        summary="Clear dashboard cache",
        description="Clear dashboard cache for specific role/user or globally",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'role': {
                        'type': 'string',
                        'enum': ['worker', 'employer', 'contractor', 'admin'],
                        'description': 'Dashboard role to clear (optional)'
                    },
                    'user_id': {
                        'type': 'integer',
                        'description': 'User ID to clear (optional)'
                    }
                }
            }
        },
        responses={200: OpenApiResponse(description="Cache cleared successfully")}
    )
    def post(self, request):
        """
        POST /api/admin/dashboard/cache/clear/
        
        Clear dashboard cache.
        
        Body:
            role (optional): worker, employer, contractor, admin
            user_id (optional): Specific user ID
        """
        role = request.data.get('role')
        user_id = request.data.get('user_id')
        
        try:
            clear_dashboard_cache(role=role, user_id=user_id)
            
            return Response({
                'status': 'cache_cleared',
                'role': role,
                'user_id': user_id
            })
        except Exception as e:
            logger.error(f"Cache clear error: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=http_status.HTTP_500_INTERNAL_SERVER_ERROR
            )
