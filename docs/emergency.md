# Emergency Help-Now System API Documentation

## Overview

The Emergency Help-Now system enables users to raise urgent service requests that are automatically routed to nearby available workers with real-time notifications, rate limiting to prevent abuse, and comprehensive tracking.

---

## Features

- ✅ Anonymous or authenticated emergency request creation
- ✅ Rate limiting (1 request/minute per phone/user)
- ✅ Auto-dispatch to nearest available workers (optional)
- ✅ Worker accept/decline workflow
- ✅ Admin escalation and status management
- ✅ Timeline events and notifications integration
- ✅ Comprehensive dispatch logging for audit

---

## API Endpoints

Base URL: `/api/v1/emergency/`

### 1. Create Emergency Request

**POST** `/api/v1/emergency/requests/`

Create urgent help request with rate limiting.

**Authentication:** Anonymous or Authenticated

**Request:**
```json
{
  "contact_phone": "+919900000001",
  "location": {
    "lat": 26.8467,
    "lng": 80.9462
  },
  "address": "123 Main Street, Lucknow",
  "service_id": "uuid-service-id",  // Optional
  "service_description": "Burst pipe emergency",  // Optional
  "urgency_level": "high",  // low, medium, high
  "site_id": "uuid-site-id"  // Optional
}
```

**Response (201):**
```json
{
  "id": "uuid-emergency-id",
  "contact_phone": "+919900000001",
  "location_lat": "26.846700",
  "location_lng": "80.946200",
  "address_text": "123 Main Street, Lucknow",
  "service_required": "uuid-service-id",
  "service_name": "Plumbing",
  "urgency_level": "high",
  "status": "open",
  "dispatch_status": "queued",  // or "manual"
  "created_at": "2026-01-03T12:00:00Z"
}
```

**Rate Limit (429):**
```json
{
  "detail": "Rate limit exceeded. Maximum 1 emergency request(s) per minute. Please try again later."
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/emergency/requests/ \
  -H "Content-Type: application/json" \
  -d '{
    "contact_phone": "+919900000001",
    "location": {"lat": 26.8467, "lng": 80.9462},
    "address": "123 Main St",
    "urgency_level": "high"
  }'
```

---

### 2. List Emergency Requests

**GET** `/api/v1/emergency/requests/`

List emergencies (filtered by user role).

**Authentication:** Required

**Query Parameters:**
- `status`: Filter by status (open, dispatched, accepted, etc.)
- `urgency_level`: Filter by urgency
- `page`, `per_page`: Pagination

**Response (200):**
```json
{
  "count": 25,
  "results": [
    {
      "id": "uuid",
      "contact_phone": "+919900000001",
      "status": "accepted",
      "assigned_worker_name": "John Doe",
      "urgency_level": "high",
      "created_at": "2026-01-03T12:00:00Z"
    }
  ]
}
```

---

### 3. Get Emergency Detail

**GET** `/api/v1/emergency/requests/{id}/`

Get detailed emergency information including dispatch logs.

**Response (200):**
```json
{
  "id": "uuid",
  "contact_phone": "+919900000001",
  "location_lat": "26.846700",
  "status": "accepted",
  "assigned_worker_name": "John Doe",
  "dispatch_logs": [
    {
      "worker_name": "John Doe",
      "attempt_time": "2026-01-03T12:01:00Z",
      "status": "accepted",
      "response_time": "2026-01-03T12:02:30Z"
    }
  ],
  "metadata": {
    "candidates_notified": 3,
    "dispatch_processed_at": "2026-01-03T12:01:00Z"
  }
}
```

---

### 4. Worker Accept Emergency

**POST** `/api/v1/emergency/requests/{id}/accept/`

Worker accepts emergency request.

**Authentication:** Required (Worker)

**Response (200):**
```json
{
  "id": "uuid",
  "status": "accepted",
  "assigned_worker": "worker-uuid",
  "assigned_worker_name": "John Doe"
}
```

**Error (400):**
```json
{
  "error": "Emergency already assigned or resolved"
}
```

---

### 5. Worker Decline Emergency

**POST** `/api/v1/emergency/requests/{id}/decline/`

Worker declines emergency request.

**Response (200):**
```json
{
  "status": "declined",
  "emergency_id": "uuid"
}
```

---

### 6. Update Emergency Status (Admin)

**PATCH** `/api/v1/emergency/requests/{id}/status/`

Update emergency status (admin only).

**Request:**
```json
{
  "status": "resolved",
  "notes": "Issue resolved, worker dispatched successfully"
}
```

---

## Auto-Dispatch Mechanism

When `EMERGENCY_AUTO_ASSIGN=true`, the system automatically:

1. **Finds Nearby Workers**:
   - Filters workers with `is_available=True`
   - Calculates distance using Haversine formula
   - Filters by `EMERGENCY_SEARCH_RADIUS_KM` (default: 5km)
   - Filters by service type if specified

2. **Ranks Candidates**:
   - Sorts by distance (nearest first)
   - Secondary sort by rating (highest first)
   - Limits to `EMERGENCY_MAX_CANDIDATES` (default: 5)

3. **Notifies Workers**:
   - Creates `EmergencyDispatchLog` for each candidate
   - Sends push notification with distance and details
   - Tracks notification delivery

4. **Handles Responses**:
   - First worker to accept gets assigned
   - Declines are logged
   - Timeout after `EMERGENCY_RESPONSE_TIMEOUT_SECONDS` (default: 45s)

5. **Escalation**:
   - If no worker accepts, marks for escalation
   - Admin can manually assign or escalate to contractors

---

## Rate Limiting

**Policy:**
- **Limit**: 1 request per minute per phone/user
- **Identifier**: Phone number (anonymous) or User ID (authenticated)
- **Storage**: Redis cache with 60-second TTL
- **Behavior**: Fail-open (allows request if Redis unavailable)

**Configuration:**
```bash
EMERGENCY_RATE_LIMIT_PER_MINUTE=1
```

**Example Error:**
```json
{
  "detail": "Rate limit exceeded. Maximum 1 emergency request(s) per minute. Please try again later.",
  "wait": 60
}
```

---

## Admin Interface

### Emergency Requests Admin

**URL:** `/admin/emergency/emergencyrequest/`

**Features:**
- List display: ID, phone, urgency, status, assigned worker
- Filters: Status, urgency level, created date, service
- Search: Phone, address, ID
- Date hierarchy: By created date

**Bulk Actions:**
1. **Escalate to contractors**: Marks emergencies for contractor assignment
2. **Mark as resolved**: Bulk resolve emergencies

### Dispatch Logs Admin

**URL:** `/admin/emergency/emergencydispatchlog/`

**Features:**
- Tracks all worker notification attempts
- Shows attempt time, status, response time
- Filter by status (notified, accepted, declined, timeout)

---

## Configuration

### Environment Variables

```bash
# Enable/disable emergency system
FEATURE_EMERGENCY=true

# Auto-dispatch settings
EMERGENCY_AUTO_ASSIGN=false  # Set to true to enable
EMERGENCY_SEARCH_RADIUS_KM=5
EMERGENCY_MAX_CANDIDATES=5
EMERGENCY_RESPONSE_TIMEOUT_SECONDS=45

# Rate limiting
EMERGENCY_RATE_LIMIT_PER_MINUTE=1
```

### Settings (hunarmitra/settings/base.py)

```python
FEATURE_EMERGENCY = env.bool('FEATURE_EMERGENCY', default=True)
EMERGENCY_AUTO_ASSIGN = env.bool('EMERGENCY_AUTO_ASSIGN', default=False)
EMERGENCY_SEARCH_RADIUS_KM = env.int('EMERGENCY_SEARCH_RADIUS_KM', default=5)
EMERGENCY_RATE_LIMIT_PER_MINUTE = env.int('EMERGENCY_RATE_LIMIT_PER_MINUTE', default=1)
EMERGENCY_MAX_CANDIDATES = env.int('EMERGENCY_MAX_CANDIDATES', default=5)
EMERGENCY_RESPONSE_TIMEOUT_SECONDS = env.int('EMERGENCY_RESPONSE_TIMEOUT_SECONDS', default=45)
```

---

## Testing

### Run Tests

```bash
python manage.py test apps.emergency.tests
```

### Test Coverage

- ✅ Create emergency with rate limiting
- ✅ Auto-dispatch flow (mocked)
- ✅ Worker accept/decline
- ✅ Admin status updates
- ✅ Permission checks

### Manual Testing

**1. Create Emergency (Anonymous):**
```bash
curl -X POST http://localhost:8000/api/v1/emergency/requests/ \
  -H "Content-Type: application/json" \
  -d '{
    "contact_phone": "+919900000001",
    "location": {"lat": 26.8467, "lng": 80.9462},
    "address": "Test Emergency",
    "urgency_level": "high"
  }'
```

**2. Worker Accept:**
```bash
# Get worker token
TOKEN=$(curl -X POST /api/auth/login/ \
  -d '{"phone":"+919876543210","otp":"123456"}' | jq -r '.access')

# Accept emergency
curl -X POST http://localhost:8000/api/v1/emergency/requests/EMERGENCY_ID/accept/ \
  -H "Authorization: Bearer $TOKEN"
```

**3. Simulate Auto-Dispatch (requires Celery):**
```bash
# Start Celery worker
celery -A hunarmitra worker -l info

# Create emergency with auto-dispatch enabled
# Check logs for dispatch task execution
```

---

## Integration

### Timeline Events

Automatic timeline events created:
- `emergency_created`: When emergency is created
- `emergency_accepted`: When worker accepts
- `emergency_status_changed`: When status is updated

### Notifications

**Worker Notification (Dispatch):**
```json
{
  "title": "🚨 Emergency Request Nearby",
  "message": "Urgent help needed 2.3km away. Tap to respond immediately.",
  "type": "emergency_dispatch",
  "metadata": {
    "emergency_id": "uuid",
    "distance_km": 2.3,
    "urgency": "high"
  }
}
```

**Creator Notification (Accepted):**
```json
{
  "title": "Emergency Accepted ✅",
  "message": "Worker John Doe is on the way!",
  "type": "emergency_update"
}
```

---

## Security & Abuse Prevention

### Rate Limiting
- Prevents spam/abuse
- Per-phone for anonymous
- Per-user for authenticated
- 60-second cooldown

### Validation
- Lat/lng range validation (-90 to 90, -180 to 180)
- Phone number required
- Address text required

### Permissions
- **Create**: Anonymous or authenticated
- **List**: Authenticated (filtered by role)
- **Accept/Decline**: Workers only
- **Status Update**: Admins only

---

## Scaling Considerations

**Current Implementation (Good for <1000 emergencies/day):**
- Redis-based rate limiting
- Haversine distance calculation (Python)
- Celery async dispatch

**For Higher Scale (>10,000/day):**
1. **Use PostGIS** for spatial queries
2. **Add caching** for nearby worker lookups
3. **Batch notifications** using Celery chord/group
4. **Add monitoring** for dispatch success rate

---

## Troubleshooting

**Emergency not dispatching?**
- Check `EMERGENCY_AUTO_ASSIGN=true`
- Verify Celery is running: `celery -A hunarmitra worker`
- Check workers have `is_available=True` and valid coordinates

**Rate limiting not working?**
- Verify Redis is running: `docker ps | grep redis`
- Check Redis connection in settings
- Rate limit fails open if Redis unavailable

**No workers notified?**
- Check `EMERGENCY_SEARCH_RADIUS_KM` (increase if needed)
- Verify workers are marked available
- Check worker has matching service

---

## Changelog

**v1.0.0 (2026-01-03)**
- ✅ Initial release
- ✅ Emergency request CRUD
- ✅ Auto-dispatch with Haversine distance
- ✅ Rate limiting (Redis)
- ✅ Worker accept/decline
- ✅ Admin escalation
- ✅ Comprehensive tests
