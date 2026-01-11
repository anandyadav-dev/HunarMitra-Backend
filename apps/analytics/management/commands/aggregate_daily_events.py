"""
Management command to aggregate daily event counts.

This is a simple utility for quick insights.
No database table needed - just prints grouped counts.
"""
from django.core.management.base import BaseCommand
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from apps.analytics.models import Event


class Command(BaseCommand):
    help = 'Aggregate and display daily event counts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to aggregate (default: 7)'
        )

    def handle(self, *args, **options):
        """Display aggregated event counts."""
        
        days = options['days']
        
        self.stdout.write(f'\nAggregating events for last {days} days...\n')
        
        # Calculate date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get events in date range
        events = Event.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        total_events = events.count()
        self.stdout.write(f'Total events: {total_events}\n')
        
        if total_events == 0:
            self.stdout.write(self.style.WARNING('No events found in this period.\n'))
            return
        
        # Group by event name
        self.stdout.write('\n=== Events by Name ===')
        by_name = events.values('name').annotate(
            count=Count('id')
        ).order_by('-count')
        
        for row in by_name:
            self.stdout.write(f"  {row['name']:<30} {row['count']:>6} events")
        
        # Group by source
        self.stdout.write('\n=== Events by Source ===')
        by_source = events.values('source').annotate(
            count=Count('id')
        ).order_by('-count')
        
        for row in by_source:
            self.stdout.write(f"  {row['source']:<30} {row['count']:>6} events")
        
        # Authenticated vs Anonymous
        self.stdout.write('\n=== Events by Authentication ===')
        authenticated = events.filter(user__isnull=False).count()
        anonymous = events.filter(user__isnull=True).count()
        
        self.stdout.write(f"  Authenticated: {authenticated:>6} events")
        self.stdout.write(f"  Anonymous:     {anonymous:>6} events")
        
        # Daily breakdown
        self.stdout.write('\n=== Daily Breakdown ===')
        
        from django.db.models.functions import TruncDate
        
        by_date = events.annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('-date')
        
        for row in by_date[:10]:  # Show last 10 days
            date_str = row['date'].strftime('%Y-%m-%d')
            self.stdout.write(f"  {date_str}  {row['count']:>6} events")
        
        # Top users (if any)
        authenticated_events = events.filter(user__isnull=False)
        if authenticated_events.exists():
            self.stdout.write('\n=== Top 10 Active Users ===')
            top_users = authenticated_events.values(
                'user__phone'
            ).annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            
            for row in top_users:
                phone = row['user__phone'] or 'Unknown'
                self.stdout.write(f"  {phone:<20} {row['count']:>6} events")
        
        self.stdout.write(self.style.SUCCESS('\n✓ Aggregation complete!\n'))
