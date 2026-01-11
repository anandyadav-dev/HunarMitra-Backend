"""
Signals for Feature Flags app.
Handles cache invalidation when flags are updated.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

from apps.flags.models import FeatureFlag

CACHE_KEY = 'feature_flags_map'


@receiver(post_save, sender=FeatureFlag)
@receiver(post_delete, sender=FeatureFlag)
def invalidate_flags_cache(sender, instance, **kwargs):
    """Clear feature flags cache on any change."""
    cache.delete(CACHE_KEY)
