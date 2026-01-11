"""
Management command to seed demo services with bilingual support.
"""

from django.core.management.base import BaseCommand
from apps.services.models import Service


class Command(BaseCommand):
    help = 'Seed demo services for UI tiles with bilingual support'
    
    def handle(self, *args, **kwargs):
        """Seed demo services with bilingual titles."""
        
        services_data = [
            {
                'name': 'Plumber',
                'slug': 'plumber',
                'title_en': 'Plumber',
                'title_hi': 'प्लंबर',
                'category': 'construction',
                'description': 'Water supply and drainage systems',
                'icon_s3_key': 'services/icons/plumber.png',
                'display_order': 1
            },
            {
                'name': 'Electrician',
                'slug': 'electrician',
                'title_en': 'Electrician',
                'title_hi': 'इलेक्ट्रीशियन',
                'category': 'construction',
                'description': 'Electrical wiring and repairs',
                'icon_s3_key': 'services/icons/electrician.png',
                'display_order': 2
            },
            {
                'name': 'Mason',
                'slug': 'mason',
                'title_en': 'Mason',
                'title_hi': 'राजमिस्त्री',
                'category': 'construction',
                'description': 'Bricklaying and construction work',
                'icon_s3_key': 'services/icons/mason.png',
                'display_order': 3
            },
            {
                'name': 'Carpenter',
                'slug': 'carpenter',
                'title_en': 'Carpenter',
                'title_hi': 'बढ़ई',
                'category': 'construction',
                'description': 'Wood and furniture work',
                'icon_s3_key': 'services/icons/carpenter.png',
                'display_order': 4
            },
            {
                'name': 'Tile Worker',
                'slug': 'tile-worker',
                'title_en': 'Tile Worker',
                'title_hi': 'टाइल मजदूर',
                'category': 'construction',
                'description': 'Floor and wall tiling',
                'icon_s3_key': 'services/icons/tile_worker.png',
                'display_order': 5
            },
            {
                'name': 'Painter',
                'slug': 'painter',
                'title_en': 'Painter',
                'title_hi': 'पेंटर',
                'category': 'home_services',
                'description': 'Interior and exterior painting',
                'icon_s3_key': 'services/icons/painter.png',
                'display_order': 6
            },
            {
                'name': 'Labour',
                'slug': 'labour',
                'title_en': 'General Labour',
                'title_hi': 'मजदूर',
                'category': 'labour',
                'description': 'General construction and moving work',
                'icon_s3_key': 'services/icons/labour.png',
                'display_order': 7
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for service_data in services_data:
            service, created = Service.objects.update_or_create(
                slug=service_data['slug'],
                defaults=service_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created service: {service.title_en} ({service.title_hi})')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Updated service: {service.title_en} ({service.title_hi})')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Seeding complete: {created_count} created, {updated_count} updated'
            )
        )
