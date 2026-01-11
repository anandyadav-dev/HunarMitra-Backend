"""
OTP service for user authentication.
"""

import random
import string
from django.conf import settings
from django.core.cache import cache


class OTPService:
    """Service for managing OTP generation, verification, and rate limiting."""
    
    OTP_PREFIX = 'otp'
    RATE_LIMIT_PREFIX = 'otp_rate_limit'
    
    @staticmethod
    def generate_otp(length=6):
        """Generate a random numeric OTP."""
        return ''.join(random.choices(string.digits, k=length))
    
    @staticmethod
    def get_otp_key(phone):
        """Get Redis key for OTP storage."""
        return f'{OTPService.OTP_PREFIX}:{phone}'
    
    @staticmethod
    def get_rate_limit_key(phone):
        """Get Redis key for rate limiting."""
        return f'{OTPService.RATE_LIMIT_PREFIX}:{phone}'
    
    @staticmethod
    def send_otp(phone):
        """
        Generate and store OTP for a phone number.
        
        Returns:
            dict: {
                'success': bool,
                'message': str,
                'otp': str (only in dev mode)
            }
        """
        # Check rate limiting
        rate_limit_key = OTPService.get_rate_limit_key(phone)
        attempts = cache.get(rate_limit_key, 0)
        
        if attempts >= settings.OTP_RATE_LIMIT_REQUESTS:
            return {
                'success': False,
                'message': 'Too many OTP requests. Please try again later.'
            }
        
        # Generate OTP
        otp = OTPService.generate_otp()
        otp_key = OTPService.get_otp_key(phone)
        
        # Store OTP in Redis
        cache.set(otp_key, otp, timeout=settings.OTP_EXPIRE_SECONDS)
        
        # Increment rate limit counter
        if attempts == 0:
            cache.set(rate_limit_key, 1, timeout=settings.OTP_RATE_LIMIT_WINDOW_SECONDS)
        else:
            cache.incr(rate_limit_key)
        
        # TODO: Send SMS via external provider (Twilio, AWS SNS, etc.)
        # For now, just log it
        print(f'[OTP] Phone: {phone}, OTP: {otp}')
        
        result = {
            'success': True,
            'message': 'OTP sent successfully',
            'expires_in': settings.OTP_EXPIRE_SECONDS
        }
        
        # In development, return OTP in response
        if settings.DEBUG:
            result['otp'] = otp
        
        return result
    
    @staticmethod
    def verify_otp(phone, otp):
        """
        Verify OTP for a phone number.
        
        Returns:
            bool: True if OTP is valid, False otherwise
        """
        otp_key = OTPService.get_otp_key(phone)
        stored_otp = cache.get(otp_key)
        
        if not stored_otp:
            return False
        
        if stored_otp == otp:
            # Delete OTP after successful verification
            cache.delete(otp_key)
            return True
        
        return False
    
    @staticmethod
    def clear_rate_limit(phone):
        """Clear rate limit for a phone number (admin use)."""
        rate_limit_key = OTPService.get_rate_limit_key(phone)
        cache.delete(rate_limit_key)
