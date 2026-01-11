# Analytics Event Collection System

## Overview

Lightweight analytics system for capturing user/client events, aggregating metrics, and providing admin reports. Privacy-safe, append-only, and designed for easy extension to real analytics pipelines.

---

## Configuration

### Environment Variables

```bash
# .env
ANALYTICS_ENABLED=true                 # Enable/disable event collection
ANALYTICS_RETENTION_DAYS=90            # Event retention period
ANALYTICS_MAX_EVENT_SIZE=2048          # Max payload size in bytes
```

### Django Settings

```python
# settings/base.py
ANALYTICS_ENABLED = env.bool('ANALYTICS_ENABLED', default=True)
ANALYTICS_RETENTION_DAYS = env.int('ANALYTICS_RETENTION_DAYS', default=90)
ANALYTICS_MAX_EVENT_SIZE = env.int('ANALYTICS_MAX_EVENT_SIZE', default=2048)
```

---

## Event Schema

### Supported Event Types

| Event Type | Description | Example Payload |
|------------|-------------|-----------------|
| `page_view` | User viewed a page | `{"page": "dashboard", "section": "jobs"}` |
| `booking_created` | Booking was created | `{"booking_id": "123", "service_id": "456"}` |
| `booking_status` | Booking status changed | `{"booking_id": "123", "status": "confirmed"}` |
| `job_apply` | User applied to job | `{"job_id": "789", "worker_id": "012"}` |
| `emergency_request` | Emergency request created | `{"latitude": 12.34, "longitude": 56.78"}` |
| `service_search` | User searched services | `{"query": "plumber", "service_id": "456"}` |

### Event Model Fields

```python
{
  "id": "uuid",
  "user": "User FK (nullable)",
  "anonymous_id": "client-generated ID (nullable)",
  "event_type": "page_view",
  "source": "android|ios|web|kiosk|admin",
  "payload": {"custom": "data"},
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "created_at": "2026-01-04T10:30:00Z"
}
```

---

## API Endpoints

### Event Ingestion (Public)

**POST** `/api/v1/analytics/events/`

**Single Event:**
```json
{
  "event_type": "page_view",
  "anonymous_id": "anon-12345",
  "source": "android",
  "payload": {
    "page": "dashboard",
    "duration_seconds": 45
  }
}
```

**Response (201):**
```json
{
  "event_id": "uuid"
}
```

**Bulk Events:**
```json
{
  "events": [
    {"event_type": "page_view", "payload": {"page": "home"}},
    {"event_type": "booking_created", "payload": {"booking_id": "123"}}
  ]
}
```

**Response (201):**
```json
{
  "events_created": 2,
  "event_ids": ["uuid1", "uuid2"]
}
```

**Headers:**
- `X-Client-ANON-ID`: Optional anonymous ID (alternative to body)
- `Authorization`: Optional (if user is logged in, user will be auto-linked)

**Behavior:**
- If `ANALYTICS_ENABLED=false`, returns `204 No Content` immediately
- Payload size enforced (max 2KB by default)
- IP address and User-Agent captured automatically
- Fast bulk insert using `bulk_create()`

---

### Admin Reports (Admin Only)

#### Daily Summary

**GET** `/api/admin/analytics/daily-summary/?date=2026-01-04`

```json
{
  "date": "2026-01-04",
  "total_events": 1234,
  "unique_users": 456,
  "unique_anonymous": 789,
  "events_by_type": {
    "page_view": 500,
    "booking_created": 100,
    "job_apply": 50
  }
}
```

---

#### Top Services

**GET** `/api/admin/analytics/top-services/?date_from=2026-01-01&date_to=2026-01-04&limit=20`

```json
{
  "top_services": [
    {"payload__service_id": "456", "count": 234},
    {"payload__service_id": "789", "count": 189}
  ]
}
```

---

#### Active Users

**GET** `/api/admin/analytics/active-users/?date=2026-01-04`

```json
{
  "date": "2026-01-04",
  "daily_active_users": 456,
  "unique_anonymous": 789,
  "total_active": 1245
}
```

---

#### CSV Export

**GET** `/api/admin/analytics/export/?date=2026-01-04&event_type=page_view&limit=10000`

Returns CSV file with columns:
```
id,created_at,event_type,user_id,anonymous_id,source,ip_address,payload
```

**Query Parameters:**
- `date`: Filter by date (YYYY-MM-DD)
- `event_type`: Filter by event type
- `limit`: Max rows (default 10000)

---

## Management Commands

### Daily Aggregation

```bash
# Aggregate yesterday's events
python manage.py analytics_aggregate_daily

# Aggregate specific date
python manage.py analytics_aggregate_daily --date=2026-01-03
```

**What it does:**
- Computes daily aggregates by `event_type` and `source`
- Stores in `EventAggregateDaily` for fast reporting
- Idempotent (safe to run multiple times)

**Schedule (Production):**
```bash
# Crontab example (run daily at 1 AM)
0 1 * * * cd /app && python manage.py analytics_aggregate_daily
```

**Celery Beat (Alternative):**
```python
CELERY_BEAT_SCHEDULE = {
    'aggregate-analytics-daily': {
        'task': 'apps.analytics.tasks.aggregate_daily',
        'schedule': crontab(hour=1, minute=0),
    },
}
```

---

### Retention Purge

```bash
# Purge events older than 90 days (default from settings)
python manage.py analytics_purge_older_than

# Custom retention
python manage.py analytics_purge_older_than --days=30

# Dry run (preview without deleting)
python manage.py analytics_purge_older_than --dry-run
```

**What it does:**
- Deletes events older than `ANALYTICS_RETENTION_DAYS`
- GDPR/privacy compliance
- Frees up database storage

**Schedule (Production):**
```bash
# Crontab (run weekly on Sunday at 2 AM)
0 2 * * 0 cd /app && python manage.py analytics_purge_older_than
```

---

## Client-Side Integration

### JavaScript (Web)

```javascript
// Generate anonymous ID (store in localStorage)
let anonId = localStorage.getItem('anon_id');
if (!anonId) {
  anonId = 'anon-' + Math.random().toString(36).substr(2, 9);
  localStorage.setItem('anon_id', anonId);
}

// Track page view
fetch('/api/v1/analytics/events/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Client-ANON-ID': anonId,
    'Authorization': `Bearer ${accessToken}` // Optional
  },
  body: JSON.stringify({
    event_type: 'page_view',
    source: 'web',
    payload: {
      page: window.location.pathname,
      referrer: document.referrer
    }
  })
});

// Track booking creation
function trackBookingCreated(bookingId) {
  fetch('/api/v1/analytics/events/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      event_type: 'booking_created',
      anonymous_id: anonId,
      source: 'web',
      payload: {booking_id: bookingId}
    })
  });
}
```

---

### Flutter (Mobile)

```dart
import 'package:uuid/uuid.dart';
import 'package:shared_preferences/shared_preferences.dart';

class AnalyticsService {
  static const String _anonIdKey = 'anonymous_id';
  final Dio _dio;
  String? _anonId;
  
  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    _anonId = prefs.getString(_anonIdKey);
    
    if (_anonId == null) {
      _anonId = 'anon-${Uuid().v4()}';
      await prefs.setString(_anonIdKey, _anonId!);
    }
  }
  
  Future<void> trackEvent(String eventType, Map<String, dynamic> payload) async {
    try {
      await _dio.post('/api/v1/analytics/events/', data: {
        'event_type': eventType,
        'anonymous_id': _anonId,
        'source': Platform.isAndroid ? 'android' : 'ios',
        'payload': payload,
      });
    } catch (e) {
      // Fail silently (analytics should not block app)
      print('Analytics error: $e');
    }
  }
  
  // Track page view
  void trackPageView(String pageName) {
    trackEvent('page_view', {'page': pageName});
  }
  
  // Track booking created
  void trackBookingCreated(String bookingId) {
    trackEvent('booking_created', {'booking_id': bookingId});
  }
}

// Usage
final analytics = AnalyticsService();
await analytics.init();
analytics.trackPageView('dashboard');
```

---

## Privacy & GDPR

### Best Practices

1. **No PII in Events:** Do not send personally identifiable information in payloads
   - ❌ BAD: `{"email": "user@example.com", "name": "John"}`
   - ✅ GOOD: `{"user_id": "123", "action": "login"}`

2. **Anonymous Tracking:** Use `anonymous_id` for unauthenticated users
   - Client-generated UUID
   - Stored in localStorage/SharedPreferences
   - Not linked to user account

3. **IP Anonymization (Optional):**
   ```python
   # In views.py, mask last octet
   ip_parts = ip_address.split('.')
   ip_address = '.'.join(ip_parts[:3] + ['0'])
   ```

4. **User Data Deletion:**
   - When user requests deletion, also delete their events:
     ```python
     Event.objects.filter(user=user).delete()
     ```

5. **Retention Policy:**
   - Default 90 days
   - Configure via `ANALYTICS_RETENTION_DAYS`
   - Run purge command regularly

---

## Performance Optimizations

### Database Indexes

Events are indexed on:
- `created_at` (for date range queries)
- `event_type` + `created_at` (composite for filtering)
- `user` + `created_at` (user activity tracking)
- `anonymous_id` (anonymous tracking)

### Query Optimization

**✅ Use aggregates for reports:**
```python
# Good - uses pre-computed aggregates
EventAggregateDaily.objects.filter(date=today)

# Avoid - computes on raw events
Event.objects.filter(created_at__date=today).aggregate(...)
```

**✅ Bulk insert for efficiency:**
```python
Event.objects.bulk_create(events)  # Single query
```

**✅ Streaming CSV export:**
```python
# Generator prevents memory issues
def _csv_generator(events):
    for event in events.iterator(chunk_size=1000):
        yield row
```

---

## Testing

### Run Tests

```bash
# All analytics tests
python manage.py test apps.analytics.tests.test_analytics

# Specific test class
python manage.py test apps.analytics.tests.test_analytics.EventIngestionTests

# Single test
python manage.py test apps.analytics.tests.test_analytics.EventIngestionTests.test_event_payload_size_limit
```

### Test Coverage

✅ `test_event_ingestion_single_authenticated`  
✅ `test_event_ingestion_single_anonymous`  
✅ `test_event_ingestion_bulk`  
✅ `test_event_payload_size_limit`  
✅ `test_analytics_disabled_returns_204`  
✅ `test_daily_aggregation_command_creates_aggregates`  
✅ `test_aggregation_is_idempotent`  
✅ `test_daily_summary_returns_expected_counts`  
✅ `test_csv_export_format`  
✅ `test_retention_purge_command_deletes_old_events`

---

## Troubleshooting

**Problem:** Events not appearing

**Solution:**
- Check `ANALYTICS_ENABLED=true`
- Verify database migration ran: `python manage.py migrate analytics`
- Check logs for errors

---

**Problem:** Payload size error

**Solution:**
- Reduce payload size (max 2KB by default)
- Increase limit: `ANALYTICS_MAX_EVENT_SIZE=4096`

---

**Problem:** CSV export timeout

**Solution:**
- Use smaller date range
- Add `limit` parameter: `?limit=5000`
- Export in batches

---

**Problem:** Slow queries

**Solution:**
- Run daily aggregation: `python manage.py analytics_aggregate_daily`
- Use aggregates instead of raw events for reports
- Add database indexes if needed

---

## Roadmap

**Future Enhancements:**
- [ ] Real-time event streaming (WebSocket)
- [ ] Integration with external analytics (Google Analytics, Mixpanel)
- [ ] Funnel analysis (conversion tracking)
- [ ] Cohort analysis
- [ ] A/B test tracking
- [ ] Session tracking
- [ ] Heatmaps/click tracking

---

## API Reference Summary

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/analytics/events/` | POST | Any | Event ingestion (single/bulk) |
| `/api/admin/analytics/daily-summary/` | GET | Admin | Daily event summary |
| `/api/admin/analytics/top-services/` | GET | Admin | Top services by count |
| `/api/admin/analytics/active-users/` | GET | Admin | DAU and anonymous count |
| `/api/admin/analytics/export/` | GET | Admin | CSV export of events |

---

## Example: Complete Flow

```bash
# 1. Enable analytics
echo "ANALYTICS_ENABLED=true" >> .env

# 2. Run migrations
python manage.py migrate analytics

# 3. Track events (from client)
curl -X POST http://localhost:8000/api/v1/analytics/events/ \
  -H "Content-Type: application/json" \
  -d '{"event_type": "page_view", "source": "web", "payload": {"page": "home"}}'

# 4. Run daily aggregation
python manage.py analytics_aggregate_daily --date=2026-01-04

# 5. Get daily summary (admin)
curl -X GET "http://localhost:8000/api/admin/analytics/daily-summary/?date=2026-01-04" \
  -H "Authorization: Bearer ADMIN_TOKEN"

# 6. Export CSV
curl -X GET "http://localhost:8000/api/admin/analytics/export/?date=2026-01-04" \
  -H "Authorization: Bearer ADMIN_TOKEN" > events.csv

# 7. Purge old events (weekly)
python manage.py analytics_purge_older_than
```

---

## Changelog

**v1.0.0 (2026-01-04)**
- ✅ Event ingestion API (single + bulk)
- ✅ Admin reports (daily summary, top services, active users)
- ✅ CSV export with streaming
- ✅ Daily aggregation command
- ✅ Retention purge command
- ✅ Privacy-safe (no PII required)
- ✅ Comprehensive tests
- ✅ Complete documentation
