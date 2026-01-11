"""
Views for Workers app.
"""
from rest_framework.views import APIView
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.db.models import F, FloatField, Q
from django.db.models.functions import ACos, Cos, Radians, Sin
from decimal import Decimal
import math
from rest_framework import viewsets
from rest_framework.decorators import action


from apps.workers.models import WorkerProfile
from apps.workers.serializers import WorkerProfileSerializer
from apps.core.pagination import StandardPagination


class WorkerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for worker registration and management.
    
    - POST: Register new worker profile
    - GET: Retrieve worker profiles (list/detail)
    """
    queryset = WorkerProfile.objects.select_related('user').all()
    serializer_class = WorkerProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_permissions(self):
        """Allow authenticated users to register, require auth for updates."""
        if self.action == 'create':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticatedOrReadOnly()]
    
    def perform_create(self, serializer):
        """Create worker profile using authenticated user from token."""
        # Use authenticated user from JWT token, not from request payload
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """Get current user's worker profile."""
        try:
            worker = request.user.worker_profile
            serializer = self.get_serializer(worker)
            return Response(serializer.data)
        except Exception:
            # AttributeError if no worker_profile, DoesNotExist if not found
            return Response(
                {'error': 'User is not a registered worker'},
                status=status.HTTP_404_NOT_FOUND
            )


class WorkerListView(generics.ListAPIView):
    """
    List workers with pagination, filtering, and sorting.
    
    Query params:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20, max: 50)
    - skill: Filter by skill/service name
    - min_price: Minimum price filter
    - max_price: Maximum price filter
    - rating: Minimum rating filter
    - available_now: Filter by availability (true/false)
    - lat, lng: Optional for distance-based sorting
    - sort: Sorting key (price|rating|distance)
    """
    serializer_class = WorkerProfileSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardPagination
    
    def get_queryset(self):
        """Build filtered and sorted queryset."""
        queryset = WorkerProfile.objects.select_related('user').prefetch_related('services')
        
        # Filter by skill
        skill = self.request.query_params.get('skill')
        if skill:
            queryset = queryset.filter(services__name__icontains=skill)
        
        # Filter by price range
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        
        if min_price:
            try:
                queryset = queryset.filter(price_amount__gte=Decimal(min_price))
            except (ValueError, TypeError):
                pass
        
        if max_price:
            try:
                queryset = queryset.filter(price_amount__lte=Decimal(max_price))
            except (ValueError, TypeError):
                pass
        
        # Filter by minimum rating
        rating = self.request.query_params.get('rating')
        if rating:
            try:
                queryset = queryset.filter(rating__gte=Decimal(rating))
            except (ValueError, TypeError):
                pass
        
        # Filter by availability
        available_now = self.request.query_params.get('available_now')
        if available_now and available_now.lower() == 'true':
            queryset = queryset.filter(availability_status='available')
        
        # Apply sorting
        sort_key = self.request.query_params.get('sort', 'created_at')
        
        if sort_key == 'price':
            queryset = queryset.order_by('price_amount')
        elif sort_key == 'rating':
            queryset = queryset.order_by('-rating')
        elif sort_key == 'distance':
            # Distance sorting requires lat/lng
            try:
                user_lat = float(self.request.query_params.get('lat'))
                user_lng = float(self.request.query_params.get('lng'))
                
                # Filter workers with location data
                queryset = queryset.filter(
                    latitude__isnull=False,
                    longitude__isnull=False
                )
                
                # Calculate distance using Haversine formula
                user_lat_rad = math.radians(user_lat)
                user_lng_rad = math.radians(user_lng)
                
                queryset = queryset.annotate(
                    distance_km=6371 * ACos(
                        Cos(user_lat_rad) * Cos(Radians(F('latitude'))) *
                        Cos(Radians(F('longitude')) - user_lng_rad) +
                        Sin(user_lat_rad) * Sin(Radians(F('latitude'))),
                        output_field=FloatField()
                    )
                )
                queryset = queryset.order_by('distance_km')
            except (TypeError, ValueError):
                # Fall back to default sorting if lat/lng invalid
                queryset = queryset.order_by('-created_at')
        else:
            # Default: newest first
            queryset = queryset.order_by('-created_at')
        
        return queryset.distinct()


class NearbyWorkersView(APIView):
    """
    Get nearby available workers sorted by distance.
    
    Query params:
    - lat (required): User's latitude
    - lng (required): User's longitude
    - radius_km (optional): Search radius in kilometers (default: 10)
    - skill (optional): Filter by skill/service name
    - page (optional): Page number for pagination
    """
    permission_classes = [permissions.AllowAny]  # Public endpoint
    
    def get(self, request):
        """Get nearby workers with distance calculation."""
        # Get query parameters
        try:
            user_lat = float(request.query_params.get('lat'))
            user_lng = float(request.query_params.get('lng'))
        except (TypeError, ValueError):
            return Response(
                {"error": "Invalid or missing lat/lng parameters"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        radius_km = float(request.query_params.get('radius_km', 10))
        skill = request.query_params.get('skill', None)
        
        # Start with available workers who have location data
        queryset = WorkerProfile.objects.filter(
            availability_status='available',
            latitude__isnull=False,
            longitude__isnull=False
        )
        
        # Filter by skill if provided
        if skill:
            queryset = queryset.filter(services__name__icontains=skill)
        
        # Calculate distance using Haversine formula
        # Distance = 6371 * acos(cos(radians(user_lat)) * cos(radians(worker_lat)) * 
        #                         cos(radians(worker_lng) - radians(user_lng)) + 
        #                         sin(radians(user_lat)) * sin(radians(worker_lat)))
        
        # Convert user coordinates to radians for calculation
        user_lat_rad = math.radians(user_lat)
        user_lng_rad = math.radians(user_lng)
        
        # Annotate queryset with distance
        queryset = queryset.annotate(
            distance_km=6371 * ACos(
                Cos(user_lat_rad) * Cos(Radians(F('latitude'))) *
                Cos(Radians(F('longitude')) - user_lng_rad) +
                Sin(user_lat_rad) * Sin(Radians(F('latitude'))),
                output_field=FloatField()
            )
        )
        
        # Filter by radius
        queryset = queryset.filter(distance_km__lte=radius_km)
        
        # Order by distance (nearest first)
        queryset = queryset.order_by('distance_km')
        
        # Apply pagination
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = WorkerProfileSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        # Fallback without pagination
        serializer = WorkerProfileSerializer(queryset, many=True)
        return Response(serializer.data)
