"""
Utilities for OTP generation, hashing, and Redis storage.
"""

import hashlib
import secrets
import logging
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

def generate_otp(length=4):
    """
    Generate a cryptographically secure numeric OTP.
    If USE_FIXED_OTP is enabled, returns fixed OTP '1234' for easier testing.
    
    Args:
        length (int): Length of OTP (default 4)
        
    Returns:
        str: Numeric OTP
    """
    # Use fixed OTP if enabled (for testing in any environment)
    if getattr(settings, 'USE_FIXED_OTP', False):
        return "1234"
    
    return "".join(secrets.choice("0123456789") for _ in range(length))


def hash_otp(otp, phone):
    """
    Create a secure hash of the OTP combined with phone.
    
    Args:
        otp (str): Plaintext OTP
        phone (str): Phone number (as salt)
        
    Returns:
        str: SHA-256 hash
    """
    secret = settings.SECRET_KEY
    data = f"{otp}:{phone}:{secret}".encode()
    return hashlib.sha256(data).hexdigest()


def verify_otp(plain_otp, hashed_otp, phone):
    """
    Verify if plaintext OTP matches the hash using constant-time comparison.
    
    Args:
        plain_otp (str): OTP provided by user
        hashed_otp (str): Stored hash
        phone (str): User phone number
        
    Returns:
        bool: True if matches
    """
    new_hash = hash_otp(plain_otp, phone)
    logger.info(f"[VERIFY_OTP] Input OTP: {plain_otp}, Phone: {phone}")
    logger.info(f"[VERIFY_OTP] New hash: {new_hash[:20]}...")
    logger.info(f"[VERIFY_OTP] Stored hash: {hashed_otp[:20]}...")
    logger.info(f"[VERIFY_OTP] Hashes match: {new_hash == hashed_otp}")
    return secrets.compare_digest(new_hash, hashed_otp)


def store_otp_in_redis(request_id, phone, otp_hash, role='worker', ttl=None):
    """
    Store hashed OTP processing data in Redis.
    
    Args:
        request_id (str): Unique request identifier
        phone (str): User phone number
        otp_hash (str): Hashed OTP
        role (str): User role
        ttl (int): Expiry in seconds
    """
    if ttl is None:
        ttl = getattr(settings, 'OTP_EXPIRE_SECONDS', 300)
        
    key = f"otp:{request_id}"
    data = {
        "phone": phone,
        "otp_hash": otp_hash,
        "role": role,
        "attempts": 0
    }
    
    logger.info(f"[CACHE STORE] Storing OTP for request {request_id}")
    logger.info(f"[CACHE STORE] Key: {key}")
    logger.info(f"[CACHE STORE] TTL: {ttl}s")
    logger.info(f"[CACHE STORE] Data: {data}")
    
    cache.set(key, data, timeout=ttl)
    
    # Immediately verify it was stored
    verify_data = cache.get(key)
    if verify_data:
        logger.info(f"[CACHE STORE] ✅ Verification: Data successfully stored and retrieved")
    else:
        logger.error(f"[CACHE STORE] ❌ Verification FAILED: Data not found immediately after storage!")
    
    logger.info(f"OTP stored for request {request_id} (TTL: {ttl}s)")


def get_otp_from_redis(request_id):
    """
    Retrieve OTP data from Redis.
    
    Args:
        request_id (str): Unique request identifier
        
    Returns:
        dict: OTP data or None if expired
    """
    key = f"otp:{request_id}"
    logger.info(f"[CACHE GET] Attempting to retrieve OTP for request {request_id}")
    logger.info(f"[CACHE GET] Key: {key}")
    
    data = cache.get(key)
    
    if data:
        logger.info(f"[CACHE GET] ✅ Data found: {data}")
    else:
        logger.error(f"[CACHE GET] ❌ Data NOT found for key: {key}")
        # Try to list all cache keys (if possible)
        try:
            logger.error(f"[CACHE GET] Cache backend: {cache.__class__.__name__}")
        except:
            pass
    
    return data


def delete_otp_from_redis(request_id):
    """
    Delete OTP data from Redis after successful verification.
    
    Args:
        request_id (str): Unique request identifier
    """
    key = f"otp:{request_id}"
    cache.delete(key)


def check_rate_limit(phone):
    """
    Check if phone number has exceeded rate limits.
    
    Args:
        phone (str): User phone number
        
    Returns:
        tuple: (is_allowed, reason)
    """
    # Rate limits configuration
    limit_min = getattr(settings, 'OTP_RATE_LIMIT_PER_MINUTE', 1)
    limit_hour = getattr(settings, 'OTP_RATE_LIMIT_PER_HOUR', 5)
    
    # Keys
    key_min = f"rate:otp:min:{phone}"
    key_hour = f"rate:otp:hour:{phone}"
    
    # Get current counts
    count_min = cache.get(key_min, 0)
    count_hour = cache.get(key_hour, 0)
    
    if count_min >= limit_min:
        logger.warning(f"OTP rate limit exceeded (min) for {phone}")
        return False, "Too many requests. Please wait a minute."
        
    if count_hour >= limit_hour:
        logger.warning(f"OTP rate limit exceeded (hour) for {phone}")
        return False, "Too many requests. Please try again later."
        
    return True, None


def increment_rate_limit(phone):
    """
    Increment rate limit counters for phone.
    
    Args:
        phone (str): User phone number
    """
    key_min = f"rate:otp:min:{phone}"
    key_hour = f"rate:otp:hour:{phone}"
    
    # Increment or set initial
    if cache.add(key_min, 1, timeout=60):
        # Key didn't exist
        pass
    else:
        try:
            cache.incr(key_min)
        except ValueError:
            cache.set(key_min, 1, timeout=60)
            
    if cache.add(key_hour, 1, timeout=3600):
        # Key didn't exist
        pass
    else:
        try:
            cache.incr(key_hour)
        except ValueError:
            cache.set(key_hour, 1, timeout=3600)
