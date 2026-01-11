"""
Celery tasks for users app but now running synchronously.
"""

import logging
from django.conf import settings
from twilio.rest import Client

logger = logging.getLogger(__name__)


def send_sms(to, body):
    """
    Send SMS synchronously using configured provider.
    
    Args:
        to (str): Recipient phone number
        body (str): Message content
        
    Returns:
        dict: Status result
    """
    provider = getattr(settings, 'SMS_PROVIDER', 'dev')
    
    logger.info(f"Using SMS Provider: {provider}")
    
    if provider == 'dev':
        # In dev mode, just log the OTP
        # SECURITY: This log will contain the plain OTP but it's only for dev environment
        logger.info(f"======================================")
        logger.info(f"[DEV SMS] To: {to}")
        logger.info(f"[DEV SMS] Body: {body}")
        logger.info(f"======================================")
        return {'status': 'dev_logged', 'to': to, 'provider': 'dev'}
    
    elif provider == 'twilio':
        try:
            account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
            auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
            from_number = getattr(settings, 'TWILIO_FROM_NUMBER', None)
            
            if not all([account_sid, auth_token, from_number]):
                error_msg = "Twilio credentials missing in settings"
                logger.error(error_msg)
                raise ValueError(error_msg)
                
            client = Client(account_sid, auth_token)
            message = client.messages.create(
                to=to,
                from_=from_number,
                body=body
            )
            
            logger.info(f"Twilio SMS sent successfully. SID: {message.sid}")
            return {'status': 'sent', 'sid': message.sid, 'provider': 'twilio'}
            
        except Exception as e:
            logger.error(f"Twilio SMS failed: {str(e)}")
            # No retry possible in sync mode without blocking
            return {'status': 'failed', 'error': str(e)}
            
    else:
        error_msg = f"Unknown SMS Provider: {provider}"
        logger.error(error_msg)
        return {'status': 'failed', 'error': error_msg}
