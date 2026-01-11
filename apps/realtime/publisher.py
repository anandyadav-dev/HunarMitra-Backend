"""
Realtime event publisher using Redis Pub/Sub.
"""
import json
import logging
# from django_redis import get_redis_connection

logger = logging.getLogger(__name__)

def publish_event(channel_name, payload):
    """
    Publish an event. 
    (Stubbed for non-Redis deployment - just logs the event)
    
    Args:
        channel_name (str): Name of the channel (e.g., 'booking_123')
        payload (dict): Data to publish
    
    Returns:
        bool: True if published, False if failed
    """
    try:
        # redis_conn = get_redis_connection("default")
        # message = json.dumps(payload)
        # redis_conn.publish(channel_name, message)
        logger.info(f"[REALTIME SINK] Channel: {channel_name} | Payload: {payload}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish event to {channel_name}: {str(e)}")
        return False
