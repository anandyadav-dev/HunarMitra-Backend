"""
Management command to seed demo promotional banners.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from apps.cms.models import Banner


class Command(BaseCommand):
    help = 'Seed demo promotional banners for development'

    def handle(self, *args, **options):
        """Create demo banners."""
        
        self.stdout.write('Seeding demo banners...')
        
        # Clear existing demo banners
        Banner.objects.filter(title__startswith='[DEMO]').delete()
        
        # Get current time
        now = timezone.now()
        
        # Demo banners
        banners = [
            {
                'title': '[DEMO] New Year Sale - Premium Workers',
                'image_url': 'https://via.placeholder.com/800x300/FF6B6B/FFFFFF?text=New+Year+Sale+-+50%25+OFF',
                'link': 'https://example.com/new-year-sale',
                'slot': 'home_top',
                'priority': 100,
                'active': True,
                'starts_at': now - timedelta(days=1),
                'ends_at': now + timedelta(days=30),
            },
            {
                'title': '[DEMO] Featured Workers of the Month',
                'image_url': 'https://via.placeholder.com/800x300/4ECDC4/FFFFFF?text=Featured+Workers',
                'link': 'https://example.com/featured-workers',
                'slot': 'home_top',
                'priority': 50,
                'active': True,
                'starts_at': now - timedelta(days=5),
                'ends_at': now + timedelta(days=25),
            },
            {
                'title': '[DEMO] Download Our Mobile App',
                'image_url': 'https://via.placeholder.com/800x300/95E1D3/333333?text=Download+Mobile+App',
                'link': 'https://example.com/download-app',
                'slot': 'home_mid',
                'priority': 10,
                'active': True,
                'starts_at': None,  # Always visible
                'ends_at': None,
            },
            {
                'title': '[DEMO] Refer & Earn Program',
                'image_url': 'https://via.placeholder.com/800x300/F38181/FFFFFF?text=Refer+%26+Earn',
                'link': 'https://example.com/refer-earn',
                'slot': 'home_bottom',
                'priority': 5,
                'active': True,
                'starts_at': now,
                'ends_at': now + timedelta(days=60),
            },
            {
                'title': '[DEMO] Inactive Banner - Should Not Show',
                'image_url': 'https://via.placeholder.com/800x300/999999/FFFFFF?text=Inactive',
                'link': None,
                'slot': 'home_top',
                'priority': 200,
                'active': False,  # Inactive
                'starts_at': None,
                'ends_at': None,
            },
            {
                'title': '[DEMO] Expired Banner - Should Not Show',
                'image_url': 'https://via.placeholder.com/800x300/999999/FFFFFF?text=Expired',
                'link': None,
                'slot': 'home_top',
                'priority': 150,
                'active': True,
                'starts_at': now - timedelta(days=10),
                'ends_at': now - timedelta(days=1),  # Expired yesterday
            },
        ]
        
        created_count = 0
        for banner_data in banners:
            banner = Banner.objects.create(**banner_data)
            created_count += 1
            status = '✓' if banner.is_visible else '✗'
            self.stdout.write(
                f'  {status} Created: {banner.title} (slot={banner.slot}, priority={banner.priority})'
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully seeded {created_count} demo banners!')
        )
        
        # Show visible banners
        visible_count = Banner.objects.filter(active=True).count()
        self.stdout.write(f'Visible banners: {visible_count}')
