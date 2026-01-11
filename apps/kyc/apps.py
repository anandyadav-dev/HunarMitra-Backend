"""
KYC app configuration.
"""
from django.apps import AppConfig


class KycConfig(AppConfig):
    """Configuration for KYC app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.kyc'
    verbose_name = 'KYC & Registration'
