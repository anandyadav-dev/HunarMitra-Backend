"""
Realtime publish utilities with graceful fallback.

Supports:
1. Django Channels (if available)
2. Redis PUBLISH (fallback)
3. Logging only (no infrastructure)
"""
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def publish_event(channel_name: str, event: dict):
    """
    Publish event to realtime channel with graceful fallback.
    
    Priority order:
    1. Django Channels channel layer (WebSocket)
    2. Redis PUBLISH (existing fallback)
    3. Log only (no infrastructure available)
    
    This function NEVER raises exceptions - it always returns gracefully.
    
    Args:
        channel_name: Channel/group name (e.g., 'booking_123', 'user_456')
        event: Event dictionary to publish
        
    Example:
        publish_event('booking_abc-123', {
            'type': 'booking_status',
            'booking_id': 'abc-123',
            'status': 'on_the_way',
            'timestamp': '2026-01-03T11:00:00Z'
        })
    """
    if not settings.ENABLE_NOTIFICATIONS:
        logger.debug(f"Notifications disabled, skipping publish to {channel_name}")
        return
    
    # Try Channels first (WebSocket)
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                channel_name,
                {
                    "type": "broadcast.message",
                    "event": event
                }
            )
            logger.info(f"[CHANNELS] Published to {channel_name}: {event.get('type')}")
            return
    except ImportError:
        # Channels not installed
        pass
    except Exception as e:
        logger.warning(f"Channels publish failed for {channel_name}: {e}")
    
    # Fallback to Redis PUBLISH (existing implementation)
    try:
        from django.core.cache import cache
        redis_client = cache._cache.get_client()
        redis_client.publish(channel_name, json.dumps(event))
        logger.info(f"[REDIS] Published to {channel_name}: {event.get('type')}")
        return
    except AttributeError:
        # Cache backend doesn't support get_client
        pass
    except Exception as e:
        logger.warning(f"Redis publish failed for {channel_name}: {e}")
    
    # Fallback to logging only
    logger.info(f"[FALLBACK LOG] {channel_name}: {json.dumps(event)}")
