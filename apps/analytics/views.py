"""
Analytics API views - Event ingestion and admin reports.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework import status
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.db.models import Count, Q
from django.http import StreamingHttpResponse
import logging
import csv
import io
import json

from .models import Event, EventAggregateDaily
from .serializers import (
    EventIngestionSerializer,
    BulkEventIngestionSerializer,
    EventSerializer
)

logger = logging.getLogger(__name__)


class EventIngestionView(APIView):
    """
    Event ingestion endpoint for analytics tracking.
    
    Accepts single or bulk events.
    """
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        POST /api/analytics/events/
        
        Single event:
        {
          "event_type": "page_view",
          "anonymous_id": "uuid",
          "source": "android",
          "payload": {...}
        }
        
        Bulk events:
        {
          "events": [
            {"event_type": "page_view", ...},
            {"event_type": "booking_created", ...}
          ]
        }
        """
        # Fast path if analytics disabled
        if not settings.ANALYTICS_ENABLED:
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        # Detect bulk vs single
        if 'events' in request.data:
            return self._handle_bulk(request)
        else:
            return self._handle_single(request)
    
    def _handle_single(self, request):
        """Handle single event ingestion."""
        serializer = EventIngestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        event = self._create_event(request, serializer.validated_data)
        
        return Response(
            {'event_id': str(event.id)},
            status=status.HTTP_201_CREATED
        )
    
    def _handle_bulk(self, request):
        """Handle bulk event ingestion."""
        serializer = BulkEventIngestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        events = []
        for event_data in serializer.validated_data['events']:
            events.append(self._create_event(request, event_data, save=False))
        
        # Bulk create for efficiency
        created_events = Event.objects.bulk_create(events)
        
        return Response(
            {
                'events_created': len(created_events),
                'event_ids': [str(e.id) for e in created_events]
            },
            status=status.HTTP_201_CREATED
        )
    
    def _create_event(self, request, data, save=True):
        """Create event instance from validated data."""
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        # Get anonymous ID from data or header
        anonymous_id = data.get('anonymous_id') or request.headers.get('X-Client-ANON-ID')
        
        event = Event(
            user=request.user if request.user.is_authenticated else None,
            anonymous_id=anonymous_id,
            event_type=data['event_type'],
            source=data.get('source', Event.SOURCE_WEB),
            payload=data.get('payload', {}),
            ip_address=ip_address,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
        )
        
        if save:
            event.save()
        
        return event


class DailySummaryView(APIView):
    """
    Admin endpoint for daily event summary.
    """
    
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        """
        GET /api/admin/analytics/daily-summary/?date=YYYY-MM-DD
        
        Returns:
        {
          "date": "2026-01-04",
          "total_events": 1234,
          "unique_users": 456,
          "unique_anonymous": 789,
          "events_by_type": {
            "page_view": 500,
            "booking_created": 100
          }
        }
        """
        date_str = request.query_params.get('date')
        if date_str:
            target_date = parse_date(date_str)
        else:
            target_date = timezone.now().date()
        
        # Try to get from aggregates first
        aggregates = EventAggregateDaily.objects.filter(date=target_date)
        
        if aggregates.exists():
            # Use pre-computed aggregates
            events_by_type = {}
            total_unique_users = 0
            total_unique_anonymous = 0
            
            for agg in aggregates:
                events_by_type[agg.event_type] = events_by_type.get(agg.event_type, 0) + agg.count
                total_unique_users = max(total_unique_users, agg.unique_users)
                total_unique_anonymous = max(total_unique_anonymous, agg.unique_anonymous)
            
            total_events = sum(events_by_type.values())
        else:
            # Compute on-the-fly
            events = Event.objects.filter(created_at__date=target_date)
            
            total_events = events.count()
            total_unique_users = events.filter(user__isnull=False).values('user').distinct().count()
            total_unique_anonymous = events.filter(anonymous_id__isnull=False).values('anonymous_id').distinct().count()
            
            events_by_type = dict(
                events.values('event_type').annotate(count=Count('id')).values_list('event_type', 'count')
            )
        
        return Response({
            'date': str(target_date),
            'total_events': total_events,
            'unique_users': total_unique_users,
            'unique_anonymous': total_unique_anonymous,
            'events_by_type': events_by_type
        })


class TopServicesView(APIView):
    """
    Admin endpoint for top services by event count.
    """
    
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        """
        GET /api/admin/analytics/top-services/?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD&limit=20
        """
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        limit = int(request.query_params.get('limit', 20))
        
        events = Event.objects.filter(event_type='service_search')
        
        if date_from:
            events = events.filter(created_at__gte=date_from)
        if date_to:
            events = events.filter(created_at__lte=date_to)
        
        # Aggregate by service_id from payload
        top_services = events.values('payload__service_id').annotate(
            count=Count('id')
        ).order_by('-count')[:limit]
        
        return Response({
            'top_services': list(top_services)
        })


class ActiveUsersView(APIView):
    """
    Admin endpoint for active users count.
    """
    
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        """
        GET /api/admin/analytics/active-users/?date=YYYY-MM-DD
        
        Returns DAU (Daily Active Users) and unique anonymous count.
        """
        date_str = request.query_params.get('date')
        if date_str:
            target_date = parse_date(date_str)
        else:
            target_date = timezone.now().date()
        
        events = Event.objects.filter(created_at__date=target_date)
        
        dau = events.filter(user__isnull=False).values('user').distinct().count()
        unique_anonymous = events.filter(anonymous_id__isnull=False).values('anonymous_id').distinct().count()
        
        return Response({
            'date': str(target_date),
            'daily_active_users': dau,
            'unique_anonymous': unique_anonymous,
            'total_active': dau + unique_anonymous
        })


class CSVExportView(APIView):
    """
    Admin endpoint for CSV export of events.
    """
    
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        """
        GET /api/admin/analytics/export/?date=YYYY-MM-DD&event_type=...&limit=10000
        
        Returns CSV file stream.
        """
        date_str = request.query_params.get('date')
        event_type = request.query_params.get('event_type')
        limit = int(request.query_params.get('limit', 10000))
        
        events = Event.objects.all()
        
        if date_str:
            events = events.filter(created_at__date=date_str)
        if event_type:
            events = events.filter(event_type=event_type)
        
        events = events.order_by('created_at')[:limit]
        
        # Stream CSV response
        response = StreamingHttpResponse(
            self._csv_generator(events),
            content_type='text/csv'
        )
        
        filename = f'events_{date_str or "all"}.csv'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    
    def _csv_generator(self, events):
        """Generate CSV rows."""
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        
        # Header
        writer.writerow([
            'id', 'created_at', 'event_type', 'user_id', 'anonymous_id',
            'source', 'ip_address', 'payload'
        ])
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)
        
        # Data rows
        for event in events.iterator(chunk_size=1000):
            writer.writerow([
                str(event.id),
                event.created_at.isoformat(),
                event.event_type,
                event.user_id or '',
                event.anonymous_id or '',
                event.source,
                event.ip_address or '',
                json.dumps(event.payload)
            ])
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)
