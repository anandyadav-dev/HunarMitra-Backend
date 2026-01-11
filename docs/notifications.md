# Notifications & Timeline API Documentation

## Overview

The Notifications and Timeline system provides:
- Persistent notification records for users
- Activity timeline for bookings and jobs
- Realtime event publishing via Redis
- Push notification support (FCM)
- Comprehensive REST APIs

## Configuration

### Environment Variables

```bash
# Enable/disable notifications system
ENABLE_NOTIFICATIONS=true  # default: true

# Firebase Cloud Messaging (optional)
FCM_SERVER_KEY=  # Leave empty for dev mode
```

When `FCM_SERVER_KEY` is not set, push notifications are logged instead of sent.

---

## API Endpoints

### 1. List Notifications

**GET** `/api/v1/notifications/`

List all notifications for authenticated user with optional filters.

**Query Parameters:**
- `is_read` (boolean): Filter by read status
- `type` (string): Filter by notification type
- `date_from` (ISO date): Filter from date
- `date_to` (ISO date): Filter to date
- `page` (int): Page number
- `page_size` (int): Results per page (default: 20, max: 100)

**Response:**
```json
{
  "count": 42,
  "next": "http://api/notifications/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "user": "uuid",
      "title": "Booking Confirmed",
      "message": "Your booking for Tap Repair is now confirmed.",
      "type": "booking_status",
      "data": {
        "booking_id": "uuid",
        "status": "confirmed",
        "service": "Tap Repair"
      },
      "is_read": false,
      "channel": "in_app",
      "created_at": "2026-01-03T10:50:00Z"
    }
  ]
}
```

### 2. Mark Notification as Read

**PATCH** `/api/v1/notifications/{id}/mark_read/`

Mark a single notification as read.

**Response:**
```json
{
  "status": "success",
  "message": "Notification marked as read"
}
```

### 3. Mark All Notifications as Read

**PATCH** `/api/v1/notifications/mark_all_read/`

Mark all user notifications as read.

**Response:**
```json
{
  "status": "success",
  "count": 12,
  "message": "12 notifications marked as read"
}
```

### 4. Get Booking Timeline

**GET** `/api/v1/bookings/{booking_id}/timeline/`

Retrieve chronological activity timeline for a booking.

**Permissions:** Booking owner, assigned worker, contractor, or admin

**Response:**
```json
{
  "booking_id": "uuid",
  "count": 4,
  "events": [
    {
      "id": "uuid",
      "booking": "uuid",
      "event_type": "booking_requested",
      "actor_display": "John Doe",
      "payload": {"status": "requested"},
      "created_at": "2026-01-03T10:00:00Z"
    },
    {
      "id": "uuid",
      "booking": "uuid",
      "event_type": "booking_confirmed",
      "actor_display": "System",
      "payload": {"status": "confirmed"},
      "created_at": "2026-01-03T10:15:00Z"
    }
  ]
}
```

### 5. Create Test Notification (Admin Only)

**POST** `/api/v1/notifications/test/`

Create a test notification for debugging.

**Permissions:** Admin only

**Request Body:**
```json
{
  "user_id": "uuid",  // optional
  "title": "Test Notification",
  "message": "This is a test",
  "type": "system",
  "channel": "in_app",
  "data": {"test": true}
}
```

---

## Notification Types

- `booking_status` - Booking status changes
- `job_application` - Job application events
- `assignment` - Worker assignment
- `attendance` - Attendance events
- `system` - System messages
- `promo` - Promotional messages

## Timeline Event Types

- `booking_requested` - Booking created
- `booking_confirmed` - Booking confirmed
- `booking_on_the_way` - Worker on the way
- `booking_arrived` - Worker arrived
- `booking_completed` - Booking completed
- `booking_cancelled` - Booking cancelled
- `job_applied` - Worker applied to job
- `job_accepted` - Application accepted
- `worker_assigned` - Worker assigned to booking
- `attendance_marked` - Attendance recorded

---

## Realtime Events

Timeline events are published to Redis channels for realtime subscriptions.

**Channel Format:** `booking_{booking_id}` or `job_{job_id}`

**Event Payload:**
```json
{
  "type": "booking_status",
  "booking_id": "uuid",
  "status": "on_the_way",
  "event_type": "booking_on_the_way",
  "timestamp": "2026-01-03T10:30:00Z"
}
```

**Subscribing (Redis CLI):**
```bash
redis-cli
> SUBSCRIBE booking_abc-123-def
```

**Subscribing (Python):**
```python
import redis
r = redis.Redis()
pubsub = r.pubsub()
pubsub.subscribe('booking_abc-123-def')

for message in pubsub.listen():
    print(message)
```

---

## Push Notifications

Push notifications are sent via FCM when `channel='push'`.

**Dev Mode (no FCM_SERVER_KEY):**
- Notifications are logged to console
- `metadata.fcm_status = 'dev_mode_logged'`

**Production Mode (with FCM_SERVER_KEY):**
- Sent to FCM API
- User must have `fcm_token` field
- `metadata.fcm_status = 'sent'|'failed'`

**Send Push Example:**
```python
from apps.notifications.models import Notification

notification = Notification.objects.create(
    user=user,
    title="New Message",
    message="You have a new booking",
    type=Notification.TYPE_BOOKING_STATUS,
    channel=Notification.CHANNEL_PUSH,
    data={"booking_id": "uuid"}
)

# Task is auto-enqueued for push channel
```

---

## Testing Locally

1. **Create test notification:**
```bash
curl -X POST http://localhost:8000/api/v1/notifications/test/ \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "title": "Test",
    "message": "Test message",
    "type": "system"
  }'
```

2. **Subscribe to realtime channel:**
```bash
docker exec -it hunarmitra_redis redis-cli
> SUBSCRIBE booking_test-123
```

3. **Trigger booking status change:**
```bash
# Update booking status -> timeline event created -> realtime published
```

4. **Check Celery logs for push:**
```bash
docker-compose logs -f celery | grep FCM
```

---

## Example Timeline Sequence

**Booking Lifecycle:**
```
1. booking_requested    - User creates booking
2. worker_assigned      - Admin assigns worker
3. booking_confirmed    - Worker confirms
4. booking_on_the_way   - Worker starts journey
5. booking_arrived      - Worker arrives at location
6. booking_completed    - Service completed
```

Each event creates:
- TimelineEvent record
- Notification for relevant users
- Realtime publish event
- Optional push notification (if channel=push)

---

## Admin Interface

- **Notifications:** http://localhost:8000/admin/notifications/notification/
- **Timeline Events:** http://localhost:8000/admin/notifications/timelineevent/

Filters available:
- Type, read status, channel, date range
- Booking ID, job ID, event type

---

## Implementation Notes

- **Idempotency:** Duplicate events within 10s window are prevented
- **Non-blocking publish:** Redis errors never fail requests
- **Auto-creation:** Signals automatically create timeline/notifications
- **Celery retry:** Push tasks retry 3 times on failure
