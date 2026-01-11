"""
Signals for Core app to handle cache invalidation.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Theme, Banner

@receiver([post_save, post_delete], sender=Theme)
@receiver([post_save, post_delete], sender=Banner)
def clear_app_config_cache(sender, instance, **kwargs):
    """
    Clear the app_config cache whenever a Theme or Banner is saved or deleted.
    """
    cache.delete('app_config_response')
    # Use pattern matching if possible, but specific key is better for performance
    # If using django-redis with proper key prefixing:
    # cache.delete_pattern("hunarmitra:app_config_response") 
    # But simple delete is safer for the main key.
