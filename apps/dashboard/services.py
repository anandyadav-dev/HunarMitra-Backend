"""
Dashboard service layer - Optimized queries for role-based summaries.
"""
from django.db.models import Count, Q, Sum
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


def worker_summary(user):
    """
    Get worker dashboard metrics with optimized queries.
    
    Args:
        user: User instance (must have worker_profile)
    
    Returns:
        dict: Worker dashboard data
    """
    from apps.workers.models import WorkerProfile
    from apps.jobs.models import Job
    from apps.notifications.models import Notification
    
    try:
        worker = WorkerProfile.objects.select_related('user').get(user=user)
    except WorkerProfile.DoesNotExist:
        raise ValueError("User is not a worker")
    
    today = timezone.now().date()
    
    # Today's jobs (single query with annotation)
    today_jobs = Job.objects.filter(
        worker=worker,
        created_at__date=today
    ).aggregate(
        assigned=Count('id', filter=Q(status='confirmed')),
        on_the_way=Count('id', filter=Q(status='on_the_way')),
        completed=Count('id', filter=Q(status='completed'))
    )
    
    # Unread notifications
    unread_count = Notification.objects.filter(
        user=user,
        is_read=False
    ).count()
    
    # Availability
    last_seen_minutes = None
    if worker.last_seen:
        last_seen_minutes = int((timezone.now() - worker.last_seen).total_seconds() / 60)
    
    availability = {
        'is_available': worker.is_available,
        'last_seen_minutes_ago': last_seen_minutes
    }
    
    # Earnings (conditional on ENABLE_PAYMENTS)
    earnings = {'today': 0.0, 'month_to_date': 0.0}
    if settings.ENABLE_PAYMENTS:
        try:
            from apps.payments.models import Payment
            
            earnings_data = Payment.objects.filter(
                worker=worker,
                status='completed'
            ).aggregate(
                today=Sum('amount', filter=Q(created_at__date=today)),
                month_to_date=Sum('amount', filter=Q(
                    created_at__month=today.month,
                    created_at__year=today.year
                ))
            )
            
            earnings = {
                'today': float(earnings_data['today'] or 0.0),
                'month_to_date': float(earnings_data['month_to_date'] or 0.0)
            }
        except Exception as e:
            logger.warning(f"Error fetching earnings: {e}")
    
    # Badges (simple rules)
    badges = []
    if not worker.is_verified:
        badges.append('verify_profile')
    if not getattr(worker, 'kyc_verified', False):
        badges.append('complete_kyc')
    
    return {
        'user_id': user.id,
        'unread_notifications': unread_count,
        'today_jobs': today_jobs,
        'availability': availability,
        'earnings': earnings,
        'badges': badges
    }


def employer_summary(user):
    """
    Get employer dashboard metrics.
    
    Args:
        user: User instance
    
    Returns:
        dict: Employer dashboard data
    """
    from apps.bookings.models import Booking
    from apps.notifications.models import Notification
    
    # Active requests (pending/confirmed/on_the_way)
    active_requests = Booking.objects.filter(
        user=user,
        status__in=['requested', 'confirmed', 'on_the_way']
    ).count()
    
    pending_confirmations = Booking.objects.filter(
        user=user,
        status='requested'
    ).count()
    
    # Recent bookings with minimal data
    recent_bookings_qs = Booking.objects.filter(
        user=user,
        status__in=['confirmed', 'on_the_way', 'arrived']
    ).select_related('worker__user', 'service').order_by('-created_at')[:5]
    
    recent_bookings = [
        {
            'id': str(booking.id),
            'status': booking.status,
            'eta_minutes': 12  # TODO: Calculate from tracking data if available
        }
        for booking in recent_bookings_qs
    ]
    
    # Unread notifications
    unread_count = Notification.objects.filter(
        user=user,
        is_read=False
    ).count()
    
    # Emergency alerts (if feature enabled)
    emergency_alerts = 0
    if settings.FEATURE_EMERGENCY:
        try:
            from apps.emergency.models import EmergencyRequest
            emergency_alerts = EmergencyRequest.objects.filter(
                created_by=user,
                status__in=['open', 'dispatched']
            ).count()
        except Exception as e:
            logger.warning(f"Error fetching emergency alerts: {e}")
    
    return {
        'user_id': user.id,
        'unread_notifications': unread_count,
        'active_requests': active_requests,
        'pending_confirmations': pending_confirmations,
        'recent_bookings': recent_bookings,
        'emergency_alerts': emergency_alerts
    }


def contractor_summary(user):
    """
    Get contractor dashboard metrics.
    
    Args:
        user: User instance (must have contractor_profile)
    
    Returns:
        dict: Contractor dashboard data
    """
    from apps.contractors.models import ContractorProfile
    from apps.notifications.models import Notification
    from apps.jobs.models import Job
    
    try:
        contractor = ContractorProfile.objects.get(user=user)
    except ContractorProfile.DoesNotExist:
        raise ValueError("User is not a contractor")
    
    today = timezone.now().date()
    
    # Active sites (if feature enabled)
    active_sites = 0
    workers_present_today = 0
    attendance_rate = 0.0
    
    if settings.FEATURE_CONTRACTOR_SITES:
        try:
            from apps.contractors.models import Site, SiteAttendance, SiteAssignment
            
            active_sites = Site.objects.filter(
                contractor=contractor,
                is_active=True
            ).count()
            
            # Workers present today
            workers_present_today = SiteAttendance.objects.filter(
                site__contractor=contractor,
                attendance_date=today,
                status='present'
            ).count()
            
            # Attendance rate (today)
            total_assigned = SiteAssignment.objects.filter(
                site__contractor=contractor,
                is_active=True
            ).count()
            
            if total_assigned > 0:
                attendance_rate = (workers_present_today / total_assigned) * 100
        except Exception as e:
            logger.warning(f"Error fetching site metrics: {e}")
    
    # Pending job requests
    pending_jobs = Job.objects.filter(
        contractor=contractor,
        status__in=['requested', 'confirmed']
    ).count()
    
    # Unread notifications
    unread_count = Notification.objects.filter(
        user=user,
        is_read=False
    ).count()
    
    return {
        'contractor_id': contractor.id,
        'unread_notifications': unread_count,
        'active_sites': active_sites,
        'workers_present_today': workers_present_today,
        'pending_job_requests': pending_jobs,
        'attendance_rate_percent': round(attendance_rate, 1)
    }


def admin_summary():
    """
    Get admin dashboard global metrics.
    
    Returns:
        dict: Admin dashboard data
    """
    from apps.users.models import User
    from apps.workers.models import WorkerProfile
    from apps.bookings.models import Booking
    
    today = timezone.now().date()
    thirty_min_ago = timezone.now() - timedelta(minutes=30)
    
    # Total users
    total_users = User.objects.count()
    
    # Workers online (available and active in last 30 min)
    workers_online = WorkerProfile.objects.filter(
        is_available=True,
        last_seen__gte=thirty_min_ago
    ).count()
    
    # Today's bookings
    today_bookings = Booking.objects.filter(
        created_at__date=today
    ).count()
    
    # Open emergencies (if feature enabled)
    open_emergencies = 0
    if settings.FEATURE_EMERGENCY:
        try:
            from apps.emergency.models import EmergencyRequest
            open_emergencies = EmergencyRequest.objects.filter(
                status__in=['open', 'dispatched']
            ).count()
        except Exception as e:
            logger.warning(f"Error fetching emergencies: {e}")
    
    # System health (simplified - TODO: integrate with Celery monitoring)
    system_health = {
        'queue_length': 0,  # Placeholder for Celery queue
        'last_seed_run': None  # Placeholder
    }
    
    return {
        'total_users': total_users,
        'total_workers_online': workers_online,
        'open_emergencies': open_emergencies,
        'today_bookings': today_bookings,
        'system_health': system_health
    }
