"""
Celery tasks for Notifications app but now running synchronously.
"""
import logging
import requests
from django.conf import settings
from .models import Notification

logger = logging.getLogger(__name__)


def send_push_notification(notification_id):
    """
    Send push notification via FCM (Firebase Cloud Messaging).
    
    In development (no FCM_SERVER_KEY): logs payload
    In production (with FCM_SERVER_KEY): calls FCM API
    
    Args:
        notification_id: UUID of the Notification to send
        
    Returns:
        dict: Status information
    """
    try:
        notification = Notification.objects.get(id=notification_id)
        
        # Check if FCM is configured
        if not settings.FCM_SERVER_KEY:
            # Development mode: just log
            logger.info(
                f"[FCM STUB] Push notification for {notification.user.phone if notification.user else 'broadcast'}: "
                f"{notification.title} - {notification.message}"
            )
            notification.metadata['fcm_status'] = 'dev_mode_logged'
            notification.metadata['fcm_logged_at'] = str(notification.created_at)
            notification.save(update_fields=['metadata', 'updated_at'])
            
            return {'status': 'dev_logged', 'notification_id': str(notification_id)}
        
        # Production mode: call FCM API
        # Note: This is a stub implementation. Real FCM integration would require:
        # 1. User FCM token storage
        # 2. Proper FCM API endpoint and authentication
        # 3. Handle token refresh, etc.
        
        if not notification.user:
            logger.warning(f"Cannot send push to broadcast notification {notification_id}")
            return {'status': 'skipped_broadcast'}
        
        # TODO: Get user's FCM token (assumes user model has fcm_token field)
        fcm_token = getattr(notification.user, 'fcm_token', None)
        
        if not fcm_token:
            logger.warning(f"User {notification.user.phone} has no FCM token")
            notification.metadata['fcm_status'] = 'no_token'
            notification.save(update_fields=['metadata', 'updated_at'])
            return {'status': 'no_token'}
        
        # Prepare FCM payload
        fcm_payload = {
            'to': fcm_token,
            'notification': {
                'title': notification.title,
                'body': notification.message,
                'sound': 'default'
            },
            'data': notification.data,
            'priority': 'high'
        }
        
        # Send to FCM
        fcm_url = 'https://fcm.googleapis.com/fcm/send'
        headers = {
            'Authorization': f'key={settings.FCM_SERVER_KEY}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            fcm_url,
            json=fcm_payload,
            headers=headers,
            timeout=10
        )
        
        response.raise_for_status()
        
        # Update notification metadata
        notification.metadata['fcm_status'] = 'sent'
        notification.metadata['fcm_response'] = response.json()
        notification.save(update_fields=['metadata', 'updated_at'])
        
        logger.info(f"FCM push sent for notification {notification_id}")
        
        return {
            'status': 'sent',
            'notification_id': str(notification_id),
            'fcm_response': response.json()
        }
        
    except Notification.DoesNotExist:
        logger.error(f"Notification {notification_id} not found")
        return {'status': 'not_found', 'error': 'Notification not found'}
        
    except requests.exceptions.RequestException as exc:
        logger.error(f"FCM API error for notification {notification_id}: {exc}")
        
        # Update metadata with error
        try:
            notification.metadata['fcm_status'] = 'failed'
            notification.metadata['fcm_error'] = str(exc)
            notification.save(update_fields=['metadata', 'updated_at'])
        except:
            pass
        
        # Retry the task
        return {'status': 'error', 'error': str(exc)}
        
    except Exception as exc:
        logger.error(f"Unexpected error sending push notification {notification_id}: {exc}", exc_info=True)
        
        try:
            notification.metadata['fcm_status'] = 'error'
            notification.metadata['fcm_error'] = str(exc)
            notification.save(update_fields=['metadata', 'updated_at'])
        except:
            pass
        
        return {'status': 'error', 'error': str(exc)}


def send_notification(user_id, title, message, **kwargs):
    """Legacy task - wrapper for send_push_notification."""
    from .models import Notification
    from apps.users.models import User
    
    user = User.objects.get(id=user_id)
    
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        **kwargs
    )
    
    if notification.channel == Notification.CHANNEL_PUSH:
        send_push_notification(notification.id)
    
    return str(notification.id)


def send_push_batch(outgoing_push_ids):
    """
    Send push notifications to FCM for a batch of OutgoingPush records.
    New implementation using Device model and OutgoingPush tracking.
    
    Args:
        outgoing_push_ids: List of OutgoingPush IDs to process
    
    Returns:
        dict: Summary with sent/failed counts
    """
    from apps.notifications.models import OutgoingPush
    from django.utils import timezone
    
    if not settings.FCM_ENABLED:
        logger.info(f"FCM disabled - skipping push batch of {len(outgoing_push_ids)} items")
        return {
            'status': 'skipped',
            'reason': 'FCM_ENABLED=False',
            'push_count': len(outgoing_push_ids)
        }
    
    if not settings.FCM_SERVER_KEY:
        logger.error("FCM_SERVER_KEY not configured")
        return {'status': 'error', 'reason': 'FCM_SERVER_KEY not set'}
    
    pushes = OutgoingPush.objects.filter(
        id__in=outgoing_push_ids
    ).select_related('device', 'notification')
    
    sent_count = 0
    failed_count = 0
    skipped_count = 0
    
    for push in pushes:
        # Skip if already sent
        if push.status == OutgoingPush.STATUS_SENT:
            skipped_count += 1
            continue
        
        # Skip if device is inactive
        if push.device and not push.device.is_active:
            push.status = OutgoingPush.STATUS_FAILED
            push.provider_response = {'error': 'Device inactive'}
            push.save(update_fields=['status', 'provider_response', 'updated_at'])
            skipped_count += 1
            continue
        
        # Prepare FCM payload (legacy HTTP API)
        payload = {
            'to': push.device.registration_token,
            'notification': {
                'title': push.payload.get('title', ''),
                'body': push.payload.get('message', ''),
            },
            'data': push.payload.get('data', {})
        }
        
        # Send to FCM
        try:
            response = requests.post(
                settings.FCM_ENDPOINT,
                json=payload,
                headers={
                    'Authorization': f'key={settings.FCM_SERVER_KEY}',
                    'Content-Type': 'application/json'
                },
                timeout=10
            )
            
            push.attempts += 1
            push.last_attempt_at = timezone.now()
            
            try:
                push.provider_response = response.json() if response.content else {}
            except ValueError:
                push.provider_response = {'raw_response': response.text[:500]}
            
            if response.status_code == 200:
                # Success - check FCM response for failures
                response_data = push.provider_response
                
                if response_data.get('failure', 0) > 0:
                    results = response_data.get('results', [{}])
                    error = results[0].get('error', 'Unknown error')
                    
                    if error in ['InvalidRegistration', 'NotRegistered']:
                        # Invalid token - deactivate device
                        push.status = OutgoingPush.STATUS_FAILED
                        if push.device:
                            push.device.is_active = False
                            push.device.save(update_fields=['is_active', 'updated_at'])
                        failed_count += 1
                    else:
                        # Retry if attempts remaining
                        if push.attempts < settings.FCM_MAX_RETRIES:
                            push.save(update_fields=['attempts', 'last_attempt_at', 'provider_response', 'updated_at'])
                            # raise self.retry(countdown=2 ** push.attempts)
                            # NO RETRY in Sync Mode
                            logger.warning(f"Soft failure for push {push.id}, retry skipped in sync mode")
                            failed_count += 1
                        else:
                            push.status = OutgoingPush.STATUS_FAILED
                            failed_count += 1
                else:
                    push.status = OutgoingPush.STATUS_SENT
                    sent_count += 1
                
                push.save(update_fields=['status', 'attempts', 'last_attempt_at', 'provider_response', 'updated_at'])
                
            elif response.status_code in [400, 404]:
                # Permanent failure
                push.status = OutgoingPush.STATUS_FAILED
                push.save(update_fields=['status', 'attempts', 'last_attempt_at', 'provider_response', 'updated_at'])
                
                # Deactivate device
                if push.device:
                    push.device.is_active = False
                    push.device.save(update_fields=['is_active', 'updated_at'])
                
                failed_count += 1
                
            elif response.status_code >= 500:
                # Transient failure - retry
                if push.attempts < settings.FCM_MAX_RETRIES:
                    push.save(update_fields=['attempts', 'last_attempt_at', 'provider_response', 'updated_at'])
                    # raise self.retry(countdown=2 ** push.attempts)
                    logger.warning(f"Server error for push {push.id}, retry skipped in sync mode")
                    failed_count += 1
                else:
                    push.status = OutgoingPush.STATUS_FAILED
                    push.save(update_fields=['status', 'attempts', 'last_attempt_at', 'provider_response', 'updated_at'])
                    failed_count += 1
            
        except requests.RequestException as exc:
            push.attempts += 1
            push.last_attempt_at = timezone.now()
            push.provider_response = {'error': str(exc)}
            
            if push.attempts < settings.FCM_MAX_RETRIES:
                push.save(update_fields=['attempts', 'last_attempt_at', 'provider_response', 'updated_at'])
                # raise self.retry(exc=exc, countdown=2 ** push.attempts)
                logger.warning(f"Request exception for push {push.id}: {exc}, retry skipped")
                failed_count += 1
            else:
                push.status = OutgoingPush.STATUS_FAILED
                push.save(update_fields=['status', 'attempts', 'last_attempt_at', 'provider_response', 'updated_at'])
                failed_count += 1
    
    return {
        'sent': sent_count,
        'failed': failed_count,
        'skipped': skipped_count,
        'total': len(outgoing_push_ids)
    }


def enqueue_push_for_notification(notification):
    """
    Create OutgoingPush records and enqueue Celery tasks for a notification.
    
    Args:
        notification: Notification instance
    """
    from apps.notifications.models import Device, OutgoingPush
    
    if not settings.FCM_ENABLED:
        return
    
    # Check if notification should trigger push
    if notification.channel not in [notification.CHANNEL_PUSH, notification.CHANNEL_BOTH]:
        return
    
    # Get target devices
    if notification.user:
        devices = Device.objects.filter(user=notification.user, is_active=True)
    else:
        devices = Device.objects.filter(is_active=True)
    
    if not devices.exists():
        return
    
    # Create OutgoingPush records
    outgoing_pushes = [
        OutgoingPush(
            notification=notification,
            device=device,
            payload={
                'title': notification.title,
                'message': notification.message,
                'data': notification.data or {}
            },
            status=OutgoingPush.STATUS_QUEUED
        )
        for device in devices
    ]
    
    created_pushes = OutgoingPush.objects.bulk_create(outgoing_pushes)
    
    # Enqueue Celery tasks in batches
    push_ids = [p.id for p in created_pushes]
    batch_size = settings.FCM_BATCH_SIZE
    
    for i in range(0, len(push_ids), batch_size):
        batch = push_ids[i:i+batch_size]
        # send_push_batch.delay(batch)
        send_push_batch(batch)  # Call synchronously
