"""
Views for Workers app - Availability and nearby search.
"""
from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.response import Response
from django.utils import timezone
from decimal import Decimal

from apps.workers.models import WorkerProfile
from apps.workers.serializers import (
    AvailabilitySerializer,
    LocationUpdateSerializer,
    NearbyWorkerSerializer
)
from apps.workers.utils import haversine_distance
from apps.core.pagination import StandardPagination


class ToggleAvailabilityView(APIView):
    """
    POST /api/workers/me/availability/
    
    Toggle worker availability (online/offline).
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Toggle worker availability."""
        # Get worker profile
        try:
            worker = request.user.worker_profile
        except WorkerProfile.DoesNotExist:
            return Response(
                {'error': 'Worker profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = AvailabilitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        is_available = serializer.validated_data['is_available']
        worker.is_available = is_available
        worker.availability_updated_at = timezone.now()
        worker.save(update_fields=['is_available', 'availability_updated_at', 'updated_at'])
        
        # Create timeline event (optional)
        try:
            from apps.notifications.models import TimelineEvent
            TimelineEvent.objects.create(
                event_type=TimelineEvent.EVENT_TYPE_CUSTOM,
                actor_display=request.user.get_full_name() or request.user.phone,
                related_user=request.user,
                payload={
                    'event': 'worker_availability_changed',
                    'is_available': is_available
                }
            )
        except Exception:
            pass
        
        # Publish realtime event (optional)
        try:
            from apps.realtime.utils import publish_event
            publish_event(
                f'worker_{worker.id}',
                {
                    'type': 'availability_changed',
                    'is_available': is_available,
                    'timestamp': timezone.now().isoformat()
                }
            )
        except Exception:
            pass
        
        return Response({
            'status': 'success',
            'is_available': is_available,
            'availability_updated_at': worker.availability_updated_at.isoformat()
        }, status=status.HTTP_200_OK)


class UpdateLocationView(APIView):
    """
    POST /api/workers/me/location/
    
    Update worker's current location.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Update worker location."""
        # Get worker profile
        try:
            worker = request.user.worker_profile
        except WorkerProfile.DoesNotExist:
            return Response(
                {'error': 'Worker profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = LocationUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        lat = serializer.validated_data['lat']
        lng = serializer.validated_data['lng']
        
        worker.latitude = lat
        worker.longitude = lng
        worker.save(update_fields=['latitude', 'longitude', 'updated_at'])
        
        # Publish realtime event if worker is available
        if worker.is_available:
            try:
                from apps.realtime.utils import publish_event
                publish_event(
                    f'worker_{worker.id}',
                    {
                        'type': 'location_updated',
                        'lat': float(lat),
                        'lng': float(lng),
                        'timestamp': timezone.now().isoformat()
                    }
                )
            except Exception:
                pass
        
        return Response({
            'status': 'success',
            'location': {
                'lat': float(lat),
                'lng': float(lng)
            }
        }, status=status.HTTP_200_OK)


class NearbyWorkersView(APIView):
    """
    GET /api/workers/nearby/
    
    Find available workers near a location.
    
    Query params:
    - lat (required): Search latitude
    - lng (required): Search longitude
    - radius_km: Search radius in kilometers (default: 5)
    - service_id: Filter by service
    - min_price: Minimum price filter
    - max_price: Maximum price filter
    - sort_by: Sort key (distance|price|rating, default: distance)
    - order: Sort order (asc|desc, default: asc)
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Search for nearby workers."""
        # Validate required params
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        
        if not lat or not lng:
            return Response(
                {'error': 'lat and lng parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            lat = float(lat)
            lng = float(lng)
        except ValueError:
            return Response(
                {'error': 'Invalid coordinates'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get filter params
        radius_km = float(request.query_params.get('radius_km', 5))
        service_id = request.query_params.get('service_id')
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        sort_by = request.query_params.get('sort_by', 'distance')
        order = request.query_params.get('order', 'asc')
        
        # Base queryset: only available workers with location
        workers = WorkerProfile.objects.filter(
            is_available=True,
            latitude__isnull=False,
            longitude__isnull=False
        ).select_related('user').prefetch_related('services')
        
        # Apply service filter
        if service_id:
            workers = workers.filter(services__id=service_id)
        
        # Apply price filters
        if min_price:
            try:
                workers = workers.filter(price_amount__gte=Decimal(min_price))
            except (ValueError, TypeError):
                pass
        
        if max_price:
            try:
                workers = workers.filter(price_amount__lte=Decimal(max_price))
            except (ValueError, TypeError):
                pass
        
        # Calculate distance for each worker and filter by radius
        workers_with_distance = []
        for worker in workers:
            distance = haversine_distance(
                lat, lng,
                worker.latitude, worker.longitude
            )
            
            # Filter by radius
            if distance <= radius_km:
                worker.distance_km = distance
                workers_with_distance.append(worker)
        
        # Sort results
        reverse = (order == 'desc')
        
        if sort_by == 'distance':
            workers_with_distance.sort(
                key=lambda w: w.distance_km,
                reverse=reverse
            )
        elif sort_by == 'price':
            workers_with_distance.sort(
                key=lambda w: w.price_amount or Decimal('999999'),
                reverse=reverse
            )
        elif sort_by == 'rating':
            workers_with_distance.sort(
                key=lambda w: w.rating or Decimal('0'),
                reverse=reverse
            )
        
        # Paginate
        paginator = StandardPagination()
        page = paginator.paginate_queryset(workers_with_distance, request)
        
        if page is not None:
            serializer = NearbyWorkerSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = NearbyWorkerSerializer(workers_with_distance, many=True)
        return Response(serializer.data)
