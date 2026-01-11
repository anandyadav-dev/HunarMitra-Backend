"""
Signal handlers for creating timeline events and notifications.
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.conf import settings

from apps.bookings.models import Booking
from apps.jobs.models import Job, JobApplication
from .models import Notification, TimelineEvent

logger = logging.getLogger(__name__)


def get_actor_display(user):
    """Get human-readable actor display name."""
    if user:
        return user.get_full_name() or user.phone
    return 'System'


def create_notification(user, title, message, notification_type, data=None, channel='in_app'):
    """Helper to create notification."""
    if not settings.ENABLE_NOTIFICATIONS:
        return None
    
    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        type=notification_type,
        data=data or {},
        channel=channel
    )


@receiver(post_save, sender=Booking)
def on_booking_change(sender, instance, created, **kwargs):
    """
    Create timeline event and notification on booking status change.
    """
    if not settings.ENABLE_NOTIFICATIONS:
        return
    
    # Map booking status to timeline event type
    status_to_event_type = {
        'requested': TimelineEvent.EVENT_TYPE_BOOKING_REQUESTED,
        'confirmed': TimelineEvent.EVENT_TYPE_BOOKING_CONFIRMED,
        'on_the_way': TimelineEvent.EVENT_TYPE_BOOKING_ON_THE_WAY,
        'arrived': TimelineEvent.EVENT_TYPE_BOOKING_ARRIVED,
        'completed': TimelineEvent.EVENT_TYPE_BOOKING_COMPLETED,
        'cancelled': TimelineEvent.EVENT_TYPE_BOOKING_CANCELLED,
    }
    
    event_type = status_to_event_type.get(instance.status)
    if not event_type:
        return
    
    # Check if this exact event already exists (idempotency)
    existing = TimelineEvent.objects.filter(
        booking=instance,
        event_type=event_type,
        created_at__gte=timezone.now() - timezone.timedelta(seconds=10)
    ).exists()
    
    if existing:
        logger.debug(f"Timeline event {event_type} already exists for booking {instance.id}")
        return
    
    # Determine actor
    actor_user = getattr(instance, 'updated_by', None)
    if not actor_user and instance.worker:
        actor_user = instance.worker.user
    
    actor_display = get_actor_display(actor_user)
    
    # Create timeline event
    timeline = TimelineEvent.objects.create(
        booking=instance,
        event_type=event_type,
        actor_display=actor_display,
        related_user=actor_user,
        payload={'status': instance.status}
    )
    
    # Create notification for employer
    if instance.user:
        title = f"Booking {instance.status.replace('_', ' ').title()}"
        message = f"Your booking for {instance.service.name} is now {instance.status.replace('_', ' ')}."
        
        create_notification(
            user=instance.user,
            title=title,
            message=message,
            notification_type=Notification.TYPE_BOOKING_STATUS,
            data={
                'booking_id': str(instance.id),
                'status': instance.status,
                'service': instance.service.name
            }
        )
    
    # Create notification for worker if assigned
    if instance.worker and instance.worker.user != instance.user:
        title = f"Booking Update"
        message = f"Booking status changed to {instance.status.replace('_', ' ')}."
        
        create_notification(
            user=instance.worker.user,
            title=title,
            message=message,
            notification_type=Notification.TYPE_BOOKING_STATUS,
            data={
                'booking_id': str(instance.id),
                'status': instance.status
            }
        )
    
    # Publish realtime event
    try:
        from apps.core.realtime import publish_event
        publish_event(
            f'booking_{instance.id}',
            {
                'type': 'booking_status',
                'booking_id': str(instance.id),
                'status': instance.status,
                'event_type': event_type,
                'timestamp': timezone.now().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Failed to publish booking event: {e}")
    
    # Also publish via enhanced pub event (includes WebSocket if Channels installed)
    try:
        from apps.realtime.utils import publish_event as ws_publish_event
        ws_publish_event(
            f'booking_{instance.id}',
            {
                'type': 'booking_status',
                'booking_id': str(instance.id),
                'status': instance.status,
                'event_type': event_type,
                'actor': actor_display,
                'timestamp': timezone.now().isoformat()
            }
        )
    except ImportError:
        # Realtime app not available, skip
        pass
    except Exception as e:
        logger.error(f"Failed to publish WebSocket event: {e}")
    
    logger.info(f"Created timeline event and notifications for booking {instance.id}: {event_type}")


@receiver(post_save, sender=JobApplication)
def on_job_application_change(sender, instance, created, **kwargs):
    """
    Create timeline event and notification on job application changes.
    """
    if not settings.ENABLE_NOTIFICATIONS:
        return
    
    if created:
        # Worker applied to job
        TimelineEvent.objects.create(
            job=instance.job,
            event_type=TimelineEvent.EVENT_TYPE_JOB_APPLIED,
            actor_display=get_actor_display(instance.worker.user),
            related_user=instance.worker.user,
            payload={
                'worker_id': str(instance.worker.id),
                'worker_name': instance.worker.user.get_full_name() or instance.worker.user.phone
            }
        )
        
        # Notify job poster
        if instance.job.user:
            create_notification(
                user=instance.job.user,
                title="New Job Application",
                message=f"{instance.worker.user.get_full_name() or instance.worker.user.phone} applied to your job.",
                notification_type=Notification.TYPE_JOB_APPLICATION,
                data={
                    'job_id': str(instance.job.id),
                    'worker_id': str(instance.worker.id),
                    'application_id': str(instance.id)
                }
            )
    
    elif instance.status == 'accepted':
        # Application accepted
        TimelineEvent.objects.create(
            job=instance.job,
            event_type=TimelineEvent.EVENT_TYPE_JOB_ACCEPTED,
            actor_display=get_actor_display(instance.job.user),
            related_user=instance.job.user,
            payload={
                'worker_id': str(instance.worker.id),
                'application_id': str(instance.id)
            }
        )
        
        # Notify worker
        if instance.worker and instance.worker.user:
            create_notification(
                user=instance.worker.user,
                title="Application Accepted",
                message=f"Your application for {instance.job.title} has been accepted!",
                notification_type=Notification.TYPE_JOB_APPLICATION,
                data={
                    'job_id': str(instance.job.id),
                    'application_id': str(instance.id)
                }
            )


@receiver(post_save, sender=Notification)
def enqueue_push_on_notification_create(sender, instance, created, **kwargs):
    """
    Automatically enqueue push notifications when a Notification is created.
    Only triggers if FCM_ENABLED=true and notification channel includes 'push'.
    """
    if not created:
        return
    
    # Import here to avoid circular imports
    from apps.notifications.tasks import enqueue_push_for_notification
    
    # Enqueue pushes for this notification
    try:
        enqueue_push_for_notification(instance)
    except Exception as e:
        logger.error(f"Failed to enqueue push for notification {instance.id}: {e}")
