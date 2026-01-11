"""
Rate limiting utility for emergency requests.
"""
from django.core.cache import cache
from rest_framework.exceptions import Throttled


def check_emergency_rate_limit(identifier: str, limit_per_minute: int = 1) -> bool:
    """
    Check if identifier (phone or user_id) has exceeded emergency rate limit.
    
    Args:
        identifier: Unique identifier (phone number or user ID)
        limit_per_minute: Maximum requests allowed per minute
    
    Returns:
        True if allowed
    
    Raises:
        Throttled: If rate limit exceeded
    """
    cache_key = f'emergency_rate_limit:{identifier}'
    
    try:
        # Try to get current count
        count = cache.get(cache_key, 0)
        
        if count >= limit_per_minute:
            raise Throttled(
                detail=f'Rate limit exceeded. Maximum {limit_per_minute} emergency request(s) per minute. Please try again later.',
                wait=60
            )
        
        # Increment counter with 60-second TTL
        cache.set(cache_key, count + 1, timeout=60)
        return True
        
    except Exception as e:
        # If Redis/cache is not available, allow the request (fail open)
        # Log the error in production
        if isinstance(e, Throttled):
            raise
        # For other cache errors, allow request to proceed
        return True


def record_emergency_attempt(phone: str, success: bool = True):
    """
    Record an emergency request attempt for analytics/abuse detection.
    
    Args:
        phone: Phone number making the request
        success: Whether the request was successful
    """
    try:
        cache_key = f'emergency_attempts:{phone}'
        attempts = cache.get(cache_key, [])
        
        from django.utils import timezone
        attempts.append({
            'timestamp': timezone.now().isoformat(),
            'success': success
        })
        
        # Keep last 100 attempts, expire after 24 hours
        cache.set(cache_key, attempts[-100:], timeout=86400)
        
    except Exception:
        # Silently fail - this is for analytics only
        pass
