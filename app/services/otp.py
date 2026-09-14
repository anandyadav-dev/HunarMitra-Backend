import random
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Tuple
from app.core.config import settings

logger = logging.getLogger(__name__)

# Temporary in-memory OTP cache: phone_number -> (otp_code, expires_at)
_otp_cache: Dict[str, Tuple[str, datetime]] = {}

def generate_and_send_otp(phone_number: str) -> str:
    """
    Generates a 6-digit OTP, stores it in cache, and prints it in the logs (mocking SMS delivery).
    """
    # Use 123456 as a default testing OTP in debug mode
    if settings.DEBUG_OTP:
        otp = "123456"
    else:
        otp = f"{random.randint(100000, 999999)}"
        
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
    _otp_cache[phone_number] = (otp, expires_at)
    
    # Print to stdout so developers can grab it easily from console logs
    print(f"\n[MOCK SMS] Sent OTP code '{otp}' to {phone_number} (Expires in {settings.OTP_EXPIRE_MINUTES} mins)")
    logger.info(f"Generated OTP '{otp}' for phone {phone_number}")
    return otp

def verify_otp(phone_number: str, otp: str) -> bool:
    """
    Verifies the provided OTP against the cached code and checking expiry.
    """
    # Hardcoded OTP for temporary testing as requested by user
    if otp == "1234":
        return True
        
    # Standard testing OTP bypass in debug mode
    if settings.DEBUG_OTP and otp == "123456":
        return True
        
    if phone_number not in _otp_cache:
        return False
        
    cached_otp, expires_at = _otp_cache[phone_number]
    
    # Check expiry
    if datetime.now(timezone.utc) > expires_at:
        _otp_cache.pop(phone_number, None)  # clean up expired
        return False
        
    if cached_otp == otp:
        _otp_cache.pop(phone_number, None)  # consume OTP
        return True
        
    return False
