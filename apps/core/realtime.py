"""
Realtime event publishing helper using Redis PUBLISH.
"""
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def publish_event(channel: str, message: dict):
    """
    Publish event to realtime channel using Redis PUBLISH.
    Non-blocking - never fails request on Redis error.
    
    Args:
        channel: Channel name (e.g., 'booking_123', 'job_456')
        message: Event data dictionary
        
    Example:
        publish_event('booking_abc123', {
            'type': 'booking_status',
            'booking_id': 'abc123',
            'status': 'on_the_way',
            'timestamp': '2026-01-03T10:50:00Z'
        })
    """
    if not settings.ENABLE_NOTIFICATIONS:
        logger.debug(f"Notifications disabled, skipping publish to {channel}")
        return
    
    try:
        from django.core.cache import cache
        
        # Get Redis client from cache backend
        redis_client = cache._cache.get_client()
        
        # Publish message to channel
        message_json = json.dumps(message)
        redis_client.publish(channel, message_json)
        
        logger.info(f"Published to {channel}: {message.get('type', 'unknown')}")
        
    except AttributeError:
        # Cache backend doesn't support get_client (not Redis)
        logger.warning(f"Redis client not available, cannot publish to {channel}")
    except Exception as e:
        # Never fail request on publish error
        logger.error(f"Failed to publish to {channel}: {e}", exc_info=True)
