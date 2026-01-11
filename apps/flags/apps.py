"""
Flags app configuration.
"""
from django.apps import AppConfig


class FlagsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.flags'
    verbose_name = 'Feature Flags'

    def ready(self):
        # Import signals to register receivers
        import apps.flags.signals
