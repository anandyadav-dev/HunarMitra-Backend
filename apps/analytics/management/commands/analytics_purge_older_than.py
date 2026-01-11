"""
Management command to purge old analytics events based on retention policy.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from datetime import timedelta

from apps.analytics.models import Event


class Command(BaseCommand):
    """
    Purge events older than retention period.
    
    Usage:
        python manage.py analytics_purge_older_than
        python manage.py analytics_purge_older_than --days=30
    """
    
    help = 'Purge analytics events older than retention period'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            help=f'Number of days to retain (default: {settings.ANALYTICS_RETENTION_DAYS})'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without deleting'
        )
    
    def handle(self, *args, **options):
        retention_days = options.get('days') or settings.ANALYTICS_RETENTION_DAYS
        dry_run = options.get('dry_run', False)
        
        cutoff_date = timezone.now() - timedelta(days=retention_days)
        
        self.stdout.write(
            f'Purging events older than {cutoff_date.date()} '
            f'({retention_days} days retention)...'
        )
        
        # Find old events
        old_events = Event.objects.filter(created_at__lt=cutoff_date)
        count = old_events.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No events to purge'))
            return
        
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'DRY RUN: Would delete {count} events (not deleting)'
            ))
            return
        
        # Delete old events
        deleted_count, _ = old_events.delete()
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully deleted {deleted_count} events older than {retention_days} days'
        ))
