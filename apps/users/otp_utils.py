import hashlib
import secrets
import logging
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

def generate_otp(length=4):
    """
    Generate a cryptographically secure numeric OTP.
    If USE_FIXED_OTP is enabled, returns fixed OTP '1234' for easier testing.
    """
    if getattr(settings, 'USE_FIXED_OTP', False):
        return "1234"
    return "".join(secrets.choice("0123456789") for _ in range(length))


def hash_otp(otp, phone):
    """
    Create a secure hash of the OTP combined with phone.
    """
    secret = settings.SECRET_KEY
    data = f"{otp}:{phone}:{secret}".encode()
    return hashlib.sha256(data).hexdigest()


def verify_otp(plain_otp, hashed_otp, phone):
    """
    Verify if plaintext OTP matches the hash using constant-time comparison.
    """
    new_hash = hash_otp(plain_otp, phone)
    logger.info(f"[VERIFY_OTP] Input OTP: {plain_otp}, Phone: {phone}")
    return secrets.compare_digest(new_hash, hashed_otp)



# Code reduced to just generation, hashing and verification helpers
# Storage moved to redis_service.py


