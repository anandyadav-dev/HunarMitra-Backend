"""
Management command to seed default feature flags.
"""
from django.core.management.base import BaseCommand
from apps.flags.models import FeatureFlag


class Command(BaseCommand):
    help = 'Seed default feature flags'

    def handle(self, *args, **options):
        """Create or update default flags."""
        
        self.stdout.write('Seeding feature flags...')
        
        flags = [
            {
                'key': 'FEATURE_CSR',
                'enabled': False,
                'description': 'Corporate Social Responsibility module'
            },
            {
                'key': 'FEATURE_EKYC',
                'enabled': False,
                'description': 'Electronic KYC verification flow'
            },
            {
                'key': 'FEATURE_ATTENDANCE',
                'enabled': False,
                'description': 'Worker attendance tracking system'
            },
            {
                'key': 'FEATURE_CONTRACTOR',
                'enabled': True,
                'description': 'Contractor module and workflows'
            },
            {
                'key': 'FEATURE_EMERGENCY',
                'enabled': True,
                'description': 'Emergency SOS and help features'
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for flag_data in flags:
            flag, created = FeatureFlag.objects.get_or_create(
                key=flag_data['key'],
                defaults=flag_data
            )
            
            if created:
                created_count += 1
                status = 'Created'
            else:
                # Optional: Update existing flags to ensure defaults match
                # Remove this else block if you want to preserve admin changes
                updated_count += 1
                status = 'Exists'
                
            self.stdout.write(
                f'  {status}: {flag.key} = {flag.enabled}'
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nProcessed flags: {created_count} created, {updated_count} existing.'
            )
        )
