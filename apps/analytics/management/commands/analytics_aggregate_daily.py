"""
Management command to aggregate events by day for faster reporting.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.db.models import Count
from datetime import timedelta

from apps.analytics.models import Event, EventAggregateDaily


class Command(BaseCommand):
    """
    Aggregate events by day for faster reporting.
    
    Usage:
        python manage.py analytics_aggregate_daily
        python manage.py analytics_aggregate_daily --date=2026-01-03
    """
    
    help = 'Aggregate analytics events by day'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date to aggregate (YYYY-MM-DD), defaults to yesterday'
        )
    
    def handle(self, *args, **options):
        # Determine target date
        date_str = options.get('date')
        if date_str:
            target_date = parse_date(date_str)
            if not target_date:
                self.stdout.write(self.style.ERROR(f'Invalid date format: {date_str}'))
                return
        else:
            # Default to yesterday
            target_date = (timezone.now() - timedelta(days=1)).date()
        
        self.stdout.write(f'Aggregating events for {target_date}...')
        
        # Get events for the day
        events = Event.objects.filter(created_at__date=target_date)
        total_count = events.count()
        
        if total_count == 0:
            self.stdout.write(self.style.WARNING(f'No events found for {target_date}'))
            return
        
        # Aggregate by event_type and source
        aggregates = events.values('event_type', 'source').annotate(
            count=Count('id'),
            unique_users=Count('user', distinct=True),
            unique_anonymous=Count('anonymous_id', distinct=True)
        )
        
        # Create or update aggregates
        created_count = 0
        updated_count = 0
        
        for agg in aggregates:
            obj, created = EventAggregateDaily.objects.update_or_create(
                date=target_date,
                event_type=agg['event_type'],
                source=agg['source'] or '',
                defaults={
                    'count': agg['count'],
                    'unique_users': agg['unique_users'],
                    'unique_anonymous': agg['unique_anonymous']
                }
            )
            
            if created:
                created_count += 1
            else:
                updated_count += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'Aggregated {total_count} events for {target_date}:\n'
            f'  - Created {created_count} aggregates\n'
            f'  - Updated {updated_count} aggregates'
        ))
