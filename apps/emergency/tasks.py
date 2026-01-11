"""
Celery tasks for emergency request processing but now running synchronously.
"""
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


def process_emergency_dispatch(emergency_id):
    """
    Process emergency dispatch - find nearby workers and notify them.
    
    Args:
        emergency_id: UUID of emergency request
    
    Returns:
        dict with emergency_id and notified_count
    """
    from apps.emergency.models import EmergencyRequest, EmergencyDispatchLog
    from apps.workers.models import WorkerProfile
    from apps.workers.utils import haversine_distance
    from apps.notifications.models import Notification
    
    try:
        emergency = EmergencyRequest.objects.select_related(
            'service_required',
            'site'
        ).get(id=emergency_id)
    except EmergencyRequest.DoesNotExist:
        return {'error':  'Emergency not found', 'emergency_id': str(emergency_id)}
    
    # Find nearby available workers
    workers = WorkerProfile.objects.filter(
        is_available=True,
        latitude__isnull=False,
        longitude__isnull=False
    ).select_related('user')
    
    # Filter by service if specified
    if emergency.service_required:
        workers = workers.filter(services=emergency.service_required)
    
    # Calculate distances and filter by radius
    candidates = []
    radius_km = settings.EMERGENCY_SEARCH_RADIUS_KM
    
    for worker in workers[:100]:  # Limit initial query
        try:
            distance = haversine_distance(
                emergency.location_lat,
                emergency.location_lng,
                worker.latitude,
                worker.longitude
            )
            
            if distance <= radius_km:
                candidates.append((worker, distance))
        except Exception:
            # Skip workers with invalid coordinates
            continue
    
    # Sort by distance first, then by rating (descending)
    candidates.sort(key=lambda x: (x[1], -float(x[0].rating or Decimal('0'))))
    
    # Limit to max candidates
    max_candidates = settings.EMERGENCY_MAX_CANDIDATES
    candidates = candidates[:max_candidates]
    
    # Notify each candidate
    notified_count = 0
    notified_worker_ids = []
    
    for worker, distance in candidates:
        try:
            # Create dispatch log
            dispatch_log = EmergencyDispatchLog.objects.create(
                emergency=emergency,
                worker=worker,
                status=EmergencyDispatchLog.STATUS_NOTIFIED,
                raw_response={
                    'distance_km': float(distance),
                    'worker_rating': float(worker.rating or 0),
                    'search_radius_km': radius_km
                }
            )
            
            # Send notification
            Notification.objects.create(
                user=worker.user,
                title='🚨 Emergency Request Nearby',
                message=f'Urgent help needed {distance:.1f}km away. Tap to respond immediately.',
                notification_type='emergency_dispatch',
                metadata={
                    'emergency_id': str(emergency.id),
                    'distance_km': float(distance),
                    'urgency': emergency.urgency_level,
                    'service': emergency.service_required.name if emergency.service_required else None,
                    'address': emergency.address_text
                }
            )
            
            notified_count += 1
            notified_worker_ids.append(str(worker.id))
            
        except Exception as e:
            # Log error but continue with other workers
            print(f"Error notifying worker {worker.id}: {str(e)}")
            continue
    
    # Update emergency status and metadata
    if notified_count > 0:
        emergency.status = EmergencyRequest.STATUS_DISPATCHED
        emergency.metadata.update({
            'candidates_notified': notified_count,
            'dispatch_processed_at': timezone.now().isoformat(),
            'search_radius_km': radius_km,
            'notified_worker_ids': notified_worker_ids
        })
        emergency.save(update_fields=['status', 'metadata', 'updated_at'])
    else:
        # No workers found - mark for escalation
        emergency.metadata.update({
            'dispatch_failed': True,
            'dispatch_failed_at': timezone.now().isoformat(),
            'failure_reason': 'No available workers in radius'
        })
        emergency.save(update_fields=['metadata', 'updated_at'])
    
    return {
        'emergency_id': str(emergency_id),
        'notified_count': notified_count,
        'status': emergency.status
    }


def check_emergency_timeouts():
    """
    Check for emergency requests that haven't been accepted within timeout period.
    Run periodically (e.g., every minute).
    """
    from apps.emergency.models import EmergencyRequest
    from datetime import timedelta
    
    timeout_seconds = settings.EMERGENCY_RESPONSE_TIMEOUT_SECONDS
    cutoff_time = timezone.now() - timedelta(seconds=timeout_seconds)
    
    # Find dispatched emergencies older than timeout
    timed_out = EmergencyRequest.objects.filter(
        status=EmergencyRequest.STATUS_DISPATCHED,
        created_at__lte=cutoff_time
    )
    
    escalated_count = 0
    for emergency in timed_out:
        # Mark as requiring escalation
        emergency.metadata.update({
            'escalation_needed': True,
            'escalation_reason': 'No worker acceptance within timeout',
            'timed_out_at': timezone.now().isoformat()
        })
        emergency.save(update_fields=['metadata', 'updated_at'])
        escalated_count += 1
        
        # TODO: Notify admin/contractors
    
    return {'escalated_count': escalated_count}
