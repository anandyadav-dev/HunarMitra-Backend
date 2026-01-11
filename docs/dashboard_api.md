# Dashboard API Documentation

## Overview

Role-based dashboard summary endpoints provide minimal, cached metrics for Flutter app dashboards. Responses are cached for 15 seconds with stale-if-error fallback.

---

## Endpoints

### Worker Dashboard

**GET** `/api/v1/dashboard/worker/`

Returns minimal metrics for worker dashboard tiles.

**Authentication:** Required (worker role)

**Response (200):**
```json
{
  "user_id": 123,
  "unread_notifications": 3,
  "today_jobs": {
    "assigned": 2,
    "on_the_way": 0,
    "completed": 1
  },
  "availability": {
    "is_available": true,
    "last_seen_minutes_ago": 5
  },
  "earnings": {
    "today": 0.0,
    "month_to_date": 1250.50
  },
  "badges": ["verify_profile", "complete_kyc"]
}
```

**Payload Size:** < 500 bytes

---

### Employer Dashboard

**GET** `/api/v1/dashboard/employer/`

Returns minimal metrics for employer dashboard tiles.

**Authentication:** Required

**Response (200):**
```json
{
  "user_id": 222,
  "unread_notifications": 1,
  "active_requests": 2,
  "pending_confirmations": 1,
  "recent_bookings": [
    {
      "id": "uuid",
      "status": "on_the_way",
      "eta_minutes": 12
    }
  ],
  "emergency_alerts": 0
}
```

**Payload Size:** < 800 bytes

---

### Contractor Dashboard

**GET** `/api/v1/dashboard/contractor/`

Returns minimal metrics for contractor dashboard tiles.

**Authentication:** Required (contractor role)

**Response (200):**
```json
{
  "contractor_id": 55,
  "unread_notifications": 4,
  "active_sites": 3,
  "workers_present_today": 28,
  "pending_job_requests": 5,
  "attendance_rate_percent": 86.5
}
```

**Payload Size:** < 400 bytes

---

### Admin Dashboard

**GET** `/api/v1/dashboard/admin/`

Returns global system metrics.

**Authentication:** Required (admin only)

**Response (200):**
```json
{
  "total_users": 12345,
  "total_workers_online": 230,
  "open_emergencies": 2,
  "today_bookings": 150,
  "system_health": {
    "queue_length": 3,
    "last_seed_run": "2026-01-02T10:30:00Z"
  }
}
```

**Payload Size:** < 300 bytes

---

## Cache Control

### Clear Dashboard Cache

**POST** `/api/admin/dashboard/cache/clear/`

Clear dashboard cache for debugging or forcing fresh data.

**Authentication:** Required (admin only)

**Request Body:**
```json
{
  "role": "worker",      // Optional: worker|employer|contractor|admin
  "user_id": 123         // Optional: specific user ID
}
```

**Response (200):**
```json
{
  "status": "cache_cleared",
  "role": "worker",
  "user_id": 123
}
```

**Examples:**

```bash
# Clear specific user's worker dashboard
curl -X POST /api/admin/dashboard/cache/clear/ \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{"role": "worker", "user_id": 123}'

# Clear all (not recommended in production)
curl -X POST /api/admin/dashboard/cache/clear/ \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{}'
```

---

## Badge Mapping

Dashboard endpoints return `badges` arrays with string keys. Frontend maps these to UI components:

| Badge Key | Frontend Display | Action | Icon |
|-----------|------------------|--------|------|
| `verify_profile` | "Verify your profile" | Navigate to profile verification | ✓ shield |
| `complete_kyc` | "Complete KYC" | Navigate to KYC form | 📄 document |
| `update_photo` | "Add profile photo" | Open photo picker | 📷 camera |
| `enable_notifications` | "Enable push notifications" | Request FCM permission | 🔔 bell |

**Future Badges:**
- `add_payment_method`
- `complete_training`
- `review_pending_jobs`

---

## Caching

### Cache Behavior

**Hot Cache (15s TTL):**
- Key pattern: `dashboard:{role}:{user_id}`
- Example: `dashboard:worker:123`
- Fast responses (< 10ms)

**Stale Cache (60s fallback):**
- Key pattern: `dashboard:{role}:{user_id}:stale`
- Used if DB fetch fails
- Prevents service degradation

**Cache Workflow:**
```
1. Check hot cache (15s TTL)
   └─ HIT → Return cached data ✓
   └─ MISS → Proceed to step 2

2. Fetch from database
   └─ SUCCESS → Cache + return ✓
   └─ FAILURE → Proceed to step 3

3. Check stale cache (60s TTL)
   └─ HIT → Return stale data (log warning) ⚠
   └─ MISS → Return 500 error ✗
```

### Performance

**Expected Query Counts:**

| Endpoint | Queries (uncached) | Queries (cached) |
|----------|-------------------|------------------|
| Worker | 4-6 | 0 |
| Employer | 3-5 | 0 |
| Contractor | 5-7 | 0 |
| Admin | 3-4 | 0 |

**Optimizations:**
- `select_related()` for foreign keys
- `annotate()` and `aggregate()` for counts
- Single query per metric type
- No N+1 queries

---

## Configuration

### Environment Variables

```bash
# .env
DASHBOARD_CACHE_TTL_SECONDS=15          # Hot cache TTL
DASHBOARD_CACHE_MAX_STALE_SECONDS=60    # Stale cache TTL
```

### Feature Flags

Dashboard metrics conditionally include data based on feature flags:

| Feature Flag | Affected Metrics |
|-------------|------------------|
| `ENABLE_PAYMENTS` | `earnings` (worker) |
| `FEATURE_CONTRACTOR_SITES` | `active_sites`, `workers_present_today`, `attendance_rate_percent` |
| `FEATURE_EMERGENCY` | `emergency_alerts`, `open_emergencies` |

**Example:**
```python
# With ENABLE_PAYMENTS=false
{
  "earnings": {
    "today": 0.0,
    "month_to_date": 0.0
  }
}

# With ENABLE_PAYMENTS=true
{
  "earnings": {
    "today": 450.00,
    "month_to_date": 12500.75
  }
}
```

---

## Testing

### Run Dashboard Tests

```bash
# All tests
python manage.py test apps.dashboard.tests.test_dashboard

# Specific test class
python manage.py test apps.dashboard.tests.test_dashboard.WorkerDashboardTests

# Single test
python manage.py test apps.dashboard.tests.test_dashboard.WorkerDashboardTests.test_worker_dashboard_payload_contains_required_keys
```

### Test Coverage

✅ `test_worker_dashboard_payload_contains_required_keys`  
✅ `test_worker_dashboard_includes_badges`  
✅ `test_worker_dashboard_unauthorized`  
✅ `test_employer_dashboard_recent_bookings`  
✅ `test_employer_dashboard_active_requests_count`  
✅ `test_contractor_dashboard_aggregates_attendance`  
✅ `test_admin_dashboard_global_metrics`  
✅ `test_admin_dashboard_requires_admin_permission`  
✅ `test_cache_is_used_and_cleared`  
✅ `test_cache_expiration`  
✅ `test_payload_size_under_1kb`

### Query Count Assertions

```python
# Verify optimized queries
def test_worker_dashboard_query_count(self):
    with self.assertNumQueries(4):  # Optimized
        response = self.client.get('/api/v1/dashboard/worker/')
    
    # Cached request
    with self.assertNumQueries(0):
        response = self.client.get('/api/v1/dashboard/worker/')
```

---

## Troubleshooting

**Problem:** Dashboard returns stale data

**Solution:**
- Check cache TTL (15s default)
- Clear cache via admin endpoint
- Verify Redis is running

---

**Problem:** Slow dashboard response (> 200ms)

**Solution:**
- Check query count (use Django Debug Toolbar)
- Verify database indexes
- Increase cache TTL if acceptable

---

**Problem:** Missing metrics (e.g., earnings = 0)

**Solution:**
- Verify feature flags enabled
- Check model relationships (worker.user, etc.)
- Review logs for fetch errors

---

**Problem:** 400 Bad Request "User is not a worker"

**Solution:**
- Ensure user has `worker_profile`
- Use correct endpoint for user role
- Verify role in User model

---

## Frontend Integration

### Flutter Example

```dart
class DashboardService {
  Future<WorkerDashboard> getWorkerDashboard() async {
    final response = await dio.get('/api/v1/dashboard/worker/');
    return WorkerDashboard.fromJson(response.data);
  }
}

class WorkerDashboard {
  final int userId;
  final int unreadNotifications;
  final TodayJobs todayJobs;
  final Availability availability;
  final Earnings earnings;
  final List<String> badges;
  
  factory WorkerDashboard.fromJson(Map<String, dynamic> json) {
    return WorkerDashboard(
      userId: json['user_id'],
      unreadNotifications: json['unread_notifications'],
      todayJobs: TodayJobs.fromJson(json['today_jobs']),
      availability: Availability.fromJson(json['availability']),
      earnings: Earnings.fromJson(json['earnings']),
      badges: List<String>.from(json['badges']),
    );
  }
}
```

### Badge Rendering

```dart
Widget buildBadges(List<String> badges) {
  final badgeConfig = {
    'verify_profile': BadgeData(
      label: 'Verify your profile',
      icon: Icons.verified_user,
      color: Colors.orange,
    ),
    'complete_kyc': BadgeData(
      label: 'Complete KYC',
      icon: Icons.description,
      color: Colors.blue,
    ),
  };
  
  return Column(
    children: badges.map((key) {
      final config = badgeConfig[key];
      return BadgeChip(config: config);
    }).toList(),
  );
}
```

---

## Performance Benchmarks

**Target Metrics:**
- Response time (cached): < 10ms
- Response time (uncached): < 100ms
- Payload size: < 1KB
- Cache hit rate: > 80%

**Monitoring:**

```python
# Add logging for monitoring
import time

start = time.time()
data = get_with_stale_fallback('worker', fetch_fn, user_id)
duration_ms = (time.time() - start) * 1000

logger.info(f"Dashboard fetch: {duration_ms:.2f}ms, cached={cached}")
```

---

## Roadmap

**Planned Enhancements:**
- [ ] Real ETA calculation for bookings
- [ ] Celery queue length monitoring
- [ ] Trend indicators (↑ ↓) for metrics
- [ ] Personalized recommendations
- [ ] A/B testing for badge priorities

---

## API Reference Summary

| Endpoint | Method | Auth | Cache | Payload Size |
|----------|--------|------|-------|--------------|
| `/api/v1/dashboard/worker/` | GET | Worker | 15s | < 500 B |
| `/api/v1/dashboard/employer/` | GET | Any | 15s | < 800 B |
| `/api/v1/dashboard/contractor/` | GET | Contractor | 15s | < 400 B |
| `/api/v1/dashboard/admin/` | GET | Admin | 15s | < 300 B |
| `/api/admin/dashboard/cache/clear/` | POST | Admin | - | - |

---

## Example: Complete Flow

```bash
# 1. Login as worker
curl -X POST /api/auth/login/ \
  -d '{"phone":"+919900000001","otp":"123456"}' \
  | jq -r '.access' > token.txt

TOKEN=$(cat token.txt)

# 2. Get worker dashboard
curl -X GET /api/v1/dashboard/worker/ \
  -H "Authorization: Bearer $TOKEN" \
  | jq

# Response:
{
  "user_id": 123,
  "unread_notifications": 3,
  "today_jobs": {
    "assigned": 2,
    "on_the_way": 0,
    "completed": 1
  },
  "availability": {
    "is_available": true,
    "last_seen_minutes_ago": 5
  },
  "earnings": {
    "today": 450.0,
    "month_to_date": 12500.75
  },
  "badges": ["verify_profile"]
}

# 3. Clear cache (admin)
curl -X POST /api/admin/dashboard/cache/clear/ \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"role": "worker", "user_id": 123}'
```

---

## Changelog

**v1.0.0 (2026-01-04)**
- ✅ Initial release
- ✅ Worker, employer, contractor, admin dashboards
- ✅ 15s cache TTL with 60s stale fallback
- ✅ Optimized queries (no N+1)
- ✅ Badge system
- ✅ Admin cache control
- ✅ Comprehensive tests
