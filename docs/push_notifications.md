# Push Notifications via FCM - Documentation

## Overview

Server-side FCM (Firebase Cloud Messaging) push notification delivery system with device registration, queued sending via Celery, retry logic with exponential backoff, and comprehensive admin controls.

---

## Features

✅ Device registration/unregistration API  
✅ Automatic push enqueueing on Notification creation  
✅ Batched Celery delivery (100 devices per task)  
✅ Exponential backoff retry (max 3 attempts)  
✅ Invalid token detection → device deactivation  
✅ Admin requeue failed pushes  
✅ Feature-flagged (FCM_ENABLED, default: false)  
✅ No FCM keys required for testing (mocked)

---

## Quick Start

### 1. Enable FCM

```bash
# .env
FCM_ENABLED=true
FCM_SERVER_KEY=your_firebase_server_key_here
```

### 2. Register Device

**POST** `/api/notifications/devices/register/`

```bash
curl -X POST http://localhost:8000/api/notifications/devices/register/ \
  -H "Authorization: Bearer USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "registration_token": "device-fcm-token-123",
    "platform": "android",
    "metadata": {
      "model": "Pixel 5",
      "os_version": "12",
      "app_version": "1.2.0"
    }
  }'
```

**Response (201):**
```json
{
  "id": "uuid",
  "user": 1,
  "user_phone": "+919900000001",
  "platform": "android",
  "registration_token": "device-fcm-token-123",
  "is_active": true,
  "last_seen": "2026-01-03T18:00:00Z",
  "created_at": "2026-01-03T18:00:00Z"
}
```

### 3. Create Notification with Push

```python
from apps.notifications.models import Notification

notification = Notification.objects.create(
    user=user,
    title="Welcome!",
    message="Thanks for registering",
    channel=Notification.CHANNEL_PUSH  # or CHANNEL_BOTH
)

# If FCM_ENABLED=true:
# → Creates OutgoingPush records for user's devices
# → Queues send_push_batch.delay() Celery task
# → Sends via FCM with retry on failure
```

---

## API Endpoints

Base URL: `/api/notifications/devices/`

### 1. Register Device

**POST** `/api/notifications/devices/register/`

Register or update device (upsert by registration_token).

**Authentication:** Optional (AllowAny)

**Body:**
```json
{
  "registration_token": "fcm-token",  // Required
  "platform": "android",              // Required: android|ios|web
  "metadata": {...},                  // Optional
  "user_id": 123                      // Optional (admin only)
}
```

**Behavior:**
- If `registration_token` exists → update platform/metadata, reactivate
- If new → create device
- Associates with authenticated user OR `user_id` (admin only)

**Response:**
- `201 Created` if new device
- `200 OK` if existing device updated

---

### 2. Unregister Device

**POST** `/api/notifications/devices/unregister/`

Deactivate device to stop receiving pushes.

**Authentication:** Required

**Body:**
```json
{
  "registration_token": "fcm-token"
}
```

**Response:**
```json
{
  "status": "unregistered",
  "devices_updated": 1
}
```

---

### 3. List User Devices

**GET** `/api/notifications/devices/`

List authenticated user's registered devices.

**Authentication:** Required

**Response:**
```json
[
  {
    "id": "uuid",
    "platform": "android",
    "is_active": true,
    "last_seen": "2026-01-03T18:00:00Z"
  }
]
```

---

## Push Notification Flow

```
 ┌──────────────┐
 │ Create       │
 │ Notification │
 │ channel=push │
 └──────┬───────┘
        │
        ▼
 ┌──────────────────┐
 │ post_save signal │  (automatic)
 └──────┬───────────┘
        │
        ▼
 ┌──────────────────────────────────┐
 │ enqueue_push_for_notification()  │
 │ - Get active devices for user    │
 │ - Create OutgoingPush records    │
 │ - Batch by FCM_BATCH_SIZE (100)  │
 └──────┬───────────────────────────┘
        │
        ▼
 ┌─────────────────────┐
 │ send_push_batch     │  (Celery task, async)
 │ .delay([push_ids])  │
 └──────┬──────────────┘
        │
        ▼
 ┌──────────────────────────────────┐
 │ For each OutgoingPush:           │
 │ 1. POST to FCM endpoint          │
 │ 2. Handle response:              │
 │    - 200 → STATUS_SENT           │
 │    - 400/404 → Failed + deactivate │
 │    - 5xx → Retry (exp backoff)   │
 │ 3. Update attempts, response     │
 └──────────────────────────────────┘
```

---

## Configuration

### Environment Variables

```bash
# Enable/Disable FCM
FCM_ENABLED=false               # Default: false (opt-in for safety)

# FCM Credentials
FCM_SERVER_KEY=                 # Firebase server key (DO NOT COMMIT)

# Rate Limiting
FCM_RATE_LIMIT_PER_MINUTE=60    # Max pushes per minute (future feature)

# Retry Settings
FCM_MAX_RETRIES=3               # Max retry attempts per push

# Batch Settings
FCM_BATCH_SIZE=100              # Devices per Celery task batch
```

### Django Settings

```python
# hunarmitra/settings/base.py
FCM_ENABLED = env.bool('FCM_ENABLED', default=False)
FCM_SERVER_KEY = env.str('FCM_SERVER_KEY', default='')
FCM_RATE_LIMIT_PER_MINUTE = env.int('FCM_RATE_LIMIT_PER_MINUTE', default=60)
FCM_MAX_RETRIES = env.int('FCM_MAX_RETRIES', default=3)
FCM_BATCH_SIZE = env.int('FCM_BATCH_SIZE', default=100)
FCM_ENDPOINT = 'https://fcm.googleapis.com/fcm/send'  # Legacy HTTP API
```

---

## Admin Interface

### Device Management

**URL:** `/admin/notifications/device/`

**Features:**
- List all registered devices
- Filter by platform, active status, created date
- Search by user phone, registration token
- Bulk action: "Deactivate selected devices"

### Outgoing Push Logs

**URL:** `/admin/notifications/outgoingpush/`

**Features:**
- View all push delivery attempts
- Filter by status (queued/sent/failed)
- Search by notification title, user phone
- View payload + provider response
- **Bulk action: "Requeue failed pushes"**

**To Requeue Failed Pushes:**
1. Navigate to OutgoingPush admin
2. Filter by `status=failed`
3. Select failed pushes
4. Choose "Requeue failed pushes" action
5. Click "Go"
6. Pushes reset to `queued` with `attempts=0`
7. New Celery tasks enqueued

---

## Retry Logic

**Exponential Backoff:**
```python
# Attempt 1: Immediate
# Attempt 2: 2^1 = 2 seconds delay
# Attempt 3: 2^2 = 4 seconds delay
# Max attempts: 3 (configurable via FCM_MAX_RETRIES)
```

**Status Transitions:**
```
queued → sent       (200 OK from FCM)
queued → failed     (400/404 invalid token)
queued → (retry)    (5xx transient error)
(retry) → sent      (eventual success)
(retry) → failed    (max retries exceeded)
```

**Invalid Token Handling:**
```python
if response.status_code in [400, 404]:
    # Permanent failure
    push.status = 'failed'
    push.device.is_active = False  # Deactivate device
```

---

## Development (FCM Disabled)

**Testing without FCM keys:**

```bash
# .env
FCM_ENABLED=false  # Default
```

**Behavior:**
- Device registration works normally
- `OutgoingPush` records NOT created
- Celery tasks NOT enqueued
- Logs payload to console (dev mode)

**To Test Full Flow (Mocked):**

```python
from unittest import mock

@override_settings(FCM_ENABLED=True, FCM_SERVER_KEY='test-key')
@mock.patch('apps.notifications.tasks.requests.post')
def test_send_push(mock_post):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {'success': 1}
    
    # Your test code...
```

---

## Testing

### Run Push Notification Tests

```bash
# All push tests
python manage.py test apps.notifications.tests.test_push

# Specific test class
python manage.py test apps.notifications.tests.test_push.DeviceRegistrationTests

# Single test
python manage.py test apps.notifications.tests.test_push.FCMDeliveryTests.test_send_push_batch_success
```

### Test Coverage

✅ `test_register_device_creates_new_device`  
✅ `test_register_device_upsert_behavior`  
✅ `test_unregister_device_deactivates`  
✅ `test_notification_creation_enqueues_push`  
✅ `test_fcm_disabled_skips_enqueue`  
✅ `test_send_push_batch_success`  
✅ `test_invalid_token_deactivates_device`  
✅ `test_transient_failure_retries`  
✅ `test_inactive_device_skipped`

**All tests use mocked `requests.post` - no real FCM keys needed!**

---

## Production Deployment

**1. Get FCM Server Key:**
- Firebase Console → Project Settings → Cloud Messaging
- Copy "Server key" (legacy)

**2. Set Environment Variable:**
```bash
export FCM_SERVER_KEY="AAAA..."
export FCM_ENABLED=true
```

**3. Start Celery Worker:**
```bash
celery -A hunarmitra worker -l info -Q default,fcm
```

**4. Monitor:**
- Check OutgoingPush admin for failed deliveries
- Monitor Celery logs for FCM errors
- Track device deactivation rate

---

## Troubleshooting

**Problem:** Pushes stuck in `queued` status

**Solution:**
- Check `FCM_ENABLED=true` in settings
- Verify Celery worker is running
- Check Celery logs for task errors

---

**Problem:** All pushes failing with invalid token

**Solution:**
- Verify `FCM_SERVER_KEY` is correct
- Check FCM endpoint is reachable
- Ensure tokens are from same Firebase project

---

**Problem:** Devices not receiving pushes

**Solution:**
- Verify device `is_active=true`
- Check app has valid FCM token
- Test with Firebase Console test message
- Verify notification `channel='push'` or `'both'`

---

**Problem:** High failure rate

**Solution:**
- Check if tokens are stale (refresh on app start)
- Monitor deactivated device count
- Consider implementing token refresh on app launch

---

## Security & Privacy

**Token Storage:**
- FCM tokens stored in `Device.registration_token`
- Tokens are NOT PII (safe to log for debugging)
- Deactivated on invalid response from FCM

**Payload:**
- Title, message, and data payload sent to FCM
- Do NOT include sensitive data (passwords, tokens)
- Use data payload for IDs, not full objects

**Admin Access:**
- Device list shows user phone (PII)
- Restrict admin access appropriately
- Consider data retention policy for old devices

---

## Future Enhancements

**Planned:**
- [ ] FCM HTTP v1 with OAuth (instead of server key)
- [ ] Topic-based messaging for broadcasts
- [ ] A/B testing for push content
- [ ] Push analytics dashboard
- [ ] Rate limiting enforcement (currently placeholder)
- [ ] Platform-specific payload customization (iOS vs Android)

**Consider:**
- Scheduled pushes (cron-based Celery tasks)
- User notification preferences (opt-out)
- Priority/urgent push support
- Rich notifications (images, actions)

---

## API Reference Summary

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/notifications/devices/register/` | POST | Optional | Register device |
| `/api/notifications/devices/unregister/` | POST | Required | Deactivate device |
| `/api/notifications/devices/` | GET | Required | List user devices |
| `/admin/notifications/device/` | - | Admin | Device management |
| `/admin/notifications/outgoingpush/` | - | Admin | Push logs + requeue |

---

## Example: Complete Push Flow

```python
# 1. User registers device (mobile app)
POST /api/notifications/devices/register/
{
  "registration_token": "fcm-token-from-app",
  "platform": "android",
  "metadata": {"model": "Pixel 5"}
}

# 2. Backend creates notification
from apps.notifications.models import Notification

notification = Notification.objects.create(
    user=user,
    title="Booking Confirmed ✅",
    message="Your plumber will arrive at 3 PM",
    channel=Notification.CHANNEL_BOTH,  # In-app + Push
    data={"booking_id": "123"}
)

# 3. Automatic (via post_save signal):
# → OutgoingPush created
# → send_push_batch.delay([push.id])

# 4. Celery task (async):
# → POST to FCM
# → Mark as sent/failed

# 5. Admin monitors:
# → /admin/notifications/outgoingpush/
# → Requeue if needed
```

---

## Changelog

**v1.0.0 (2026-01-03)**
- ✅ Initial release
- ✅ Device registration/unregistration
- ✅ Automatic push enqueueing
- ✅ Celery batch delivery
- ✅ Retry with exponential backoff
- ✅ Admin requeue action
- ✅ Comprehensive tests (mocked FCM)
