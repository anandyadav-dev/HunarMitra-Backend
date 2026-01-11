"""
Emergency app configuration.
"""
from django.apps import AppConfig


class EmergencyConfig(AppConfig):
    """Configuration for Emergency app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.emergency'
    verbose_name = 'Emergency Requests'
    
    def ready(self):
        """Import signal handlers when app is ready."""
        pass  # Import signals here if needed
