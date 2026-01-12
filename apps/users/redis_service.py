"""
Redis service for handling OTP storage and retrieval.
Separated from utils as requested.
"""
import logging
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

def store_otp_in_redis(request_id, phone, otp_hash, role='worker', ttl=None):
    """
    Store hashed OTP processing data in Redis.
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
    
    logger.info(f"[REDIS STORE] Key: {key}, TTL: {ttl}s")
    cache.set(key, data, timeout=ttl)
    
    # Verify
    if cache.get(key):
        logger.info(f"[REDIS STORE] ✅ Successfully stored")
    else:
        logger.error(f"[REDIS STORE] ❌ Verification FAILED")


def get_otp_from_redis(request_id):
    """
    Retrieve OTP data from Redis.
    """
    key = f"otp:{request_id}"
    logger.info(f"[REDIS GET] Key: {key}")
    
    data = cache.get(key)
    if data:
        logger.info(f"[REDIS GET] ✅ Data found")
    else:
        logger.warning(f"[REDIS GET] ❌ Data NOT found")
        
    return data


def delete_otp_from_redis(request_id):
    """
    Delete OTP data from Redis.
    """
    key = f"otp:{request_id}"
    cache.delete(key)
