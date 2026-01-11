"""
Dashboard caching utilities with stale-if-error fallback.
"""
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def get_dashboard_cache_key(role, user_id=None):
    """
    Generate cache key for dashboard.
    
    Args:
        role: Dashboard role (worker, employer, contractor, admin)
        user_id: User ID (None for global dashboards like admin)
    
    Returns:
        str: Cache key
    """
    if user_id:
        return f'dashboard:{role}:{user_id}'
    return f'dashboard:{role}:global'


def get_cached_dashboard(role, user_id=None):
    """
    Get cached dashboard data.
    
    Args:
        role: Dashboard role
        user_id: User ID (optional)
    
    Returns:
        dict or None: Cached data if exists
    """
    cache_key = get_dashboard_cache_key(role, user_id)
    return cache.get(cache_key)


def set_cached_dashboard(role, data, user_id=None):
    """
    Cache dashboard data.
    
    Args:
        role: Dashboard role
        data: Dashboard data dict
        user_id: User ID (optional)
    """
    cache_key = get_dashboard_cache_key(role, user_id)
    ttl = settings.DASHBOARD_CACHE_TTL_SECONDS
    
    # Also store as stale backup
    stale_key = f'{cache_key}:stale'
    max_stale = settings.DASHBOARD_CACHE_MAX_STALE_SECONDS
    
    cache.set(cache_key, data, timeout=ttl)
    cache.set(stale_key, data, timeout=max_stale)


def get_with_stale_fallback(role, fetch_fn, user_id=None):
    """
    Get dashboard with stale-if-error behavior.
    
    Workflow:
    1. Try cache (hot)
    2. If miss, fetch fresh data
    3. If fetch fails, return stale cache up to MAX_STALE_SECONDS
    4. If no stale cache, raise error
    
    Args:
        role: Dashboard role
        fetch_fn: Function to fetch fresh data (callable)
        user_id: User ID (optional)
    
    Returns:
        dict: Dashboard data
    
    Raises:
        Exception: If fetch fails and no stale cache available
    """
    # Try hot cache first
    cached = get_cached_dashboard(role, user_id)
    if cached:
        logger.debug(f"Dashboard cache HIT for {role}:{user_id}")
        return cached
    
    logger.debug(f"Dashboard cache MISS for {role}:{user_id}")
    
    # Fetch fresh data
    try:
        data = fetch_fn()
        set_cached_dashboard(role, data, user_id)
        return data
    except Exception as e:
        logger.error(f"Dashboard fetch failed for {role}:{user_id}: {e}")
        
        # Try stale cache as fallback
        stale_key = f'{get_dashboard_cache_key(role, user_id)}:stale'
        stale_data = cache.get(stale_key)
        
        if stale_data:
            logger.warning(f"Returning STALE dashboard for {role}:{user_id}")
            return stale_data
        
        # No stale data available, re-raise
        raise


def clear_dashboard_cache(role=None, user_id=None):
    """
    Clear dashboard cache.
    
    Args:
        role: Dashboard role (None = all roles)
        user_id: User ID (None = all users for role)
    """
    if role and user_id:
        # Clear specific user's dashboard
        cache_key = get_dashboard_cache_key(role, user_id)
        stale_key = f'{cache_key}:stale'
        cache.delete(cache_key)
        cache.delete(stale_key)
        logger.info(f"Cleared dashboard cache for {role}:{user_id}")
    elif role:
        # Clearing all users for a role requires pattern matching
        # Not all cache backends support this, so we log a warning
        logger.warning(f"Cannot clear all {role} dashboards - pattern matching not universally supported")
    else:
        # Clear all dashboard caches (requires pattern matching or cache.clear())
        # For safety, we don't implement this to avoid clearing non-dashboard caches
        logger.warning("Clearing all dashboards not implemented - use specific role/user_id")
