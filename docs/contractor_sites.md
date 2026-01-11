# Contractor Site Management API

## Overview

The Site Management API allows contractors to create and manage construction sites, assign workers, track daily attendance, and access aggregated dashboard metrics for workforce management.

---

## Models

### Site
Construction site managed by a contractor.

**Fields:**
- `contractor` (FK): Contractor who owns this site
- `name` (string): Site name/identifier
- `address` (text): Full site address
- `lat`, `lng` (decimal): GPS coordinates
- `phone` (string): Site contact number
- `is_active` (boolean): Whether site is currently active
- `start_date`, `end_date` (date): Project timeline
- `metadata` (JSON): Additional site data

### SiteAssignment
Worker assignment to a construction site.

**Fields:**
- `site` (FK): Site where worker is assigned
- `worker` (FK): Worker assigned
- `assigned_by` (FK): User who made assignment
- `role_on_site` (string): Worker's role (e.g., "Plumber", "Mason")
- `is_active` (boolean): Whether assignment is active

### SiteAttendance
Daily attendance record for worker at site.

**Fields:**
- `site` (FK): Site where attendance is recorded
- `worker` (FK): Worker
- `attendance_date` (date): Date of attendance
- `status` (choice): present | absent | half_day | on_leave
- `checkin_time`, `checkout_time` (datetime): Check-in/out times
- `marked_by` (FK): User who marked attendance
- `notes` (text): Additional notes

---

## API Endpoints

Base URL: `/api/v1/contractors/`

### 1. Create Site

**POST** `/api/v1/contractors/sites/`

Create a new construction site.

**Authentication:** Required (Contractor)

**Request:**
```json
{
  "name": "Green Valley Construction",
  "address": "Plot 42, Sector 15, Lucknow",
  "lat": 26.8500,
  "lng": 80.9500,
  "phone": "+919876543200",
  "is_active": true,
  "start_date": "2025-12-01"
}
```

**Response (201):**
```json
{
  "id": "abc-123-uuid",
  "contractor": 1,
  "contractor_name": "ABC Construction Co.",
  "name": "Green Valley Construction",
  "address": "Plot 42, Sector 15, Lucknow",
  "lat": "26.850000",
  "lng": "80.950000",
  "phone": "+919876543200",
  "is_active": true,
  "start_date": "2025-12-01",
  "end_date": null,
  "metadata": {},
  "assigned_workers_count": 0,
  "created_at": "2026-01-03T11:30:00Z"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/contractors/sites/ \
  -H "Authorization: Bearer CONTRACTOR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Green Valley Construction",
    "address": "Plot 42, Sector 15, Lucknow",
    "lat": 26.8500,
    "lng": 80.9500,
    "is_active": true
  }'
```

---

### 2. List Sites

**GET** `/api/v1/contractors/sites/`

List all sites owned by the authenticated contractor.

**Authentication:** Required

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 20)

**Response (200):**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "abc-123",
      "name": "Green Valley Construction",
      "address": "Plot 42, Sector 15, Lucknow",
      "is_active": true,
      "assigned_workers_count": 5,
      "created_at": "2025-12-01T10:00:00Z"
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:8000/api/v1/contractors/sites/ \
  -H "Authorization: Bearer CONTRACTOR_JWT_TOKEN"
```

---

### 3. Get Site Detail

**GET** `/api/v1/contractors/sites/{site_id}/`

Get detailed information about a specific site.

**Example:**
```bash
curl http://localhost:8000/api/v1/contractors/sites/abc-123/ \
  -H "Authorization: Bearer CONTRACTOR_JWT_TOKEN"
```

---

### 4. Update Site

**PATCH** `/api/v1/contractors/sites/{site_id}/`

Update site information.

**Request:**
```json
{
  "is_active": false,
  "end_date": "2026-03-31"
}
```

---

### 5. Assign Worker to Site

**POST** `/api/v1/contractors/sites/{site_id}/assign/`

Assign a worker to a construction site.

**Request:**
```json
{
  "worker_id": "worker-uuid-123",
  "role_on_site": "Plumber"
}
```

**Response (200):**
```json
{
  "id": "assignment-uuid",
  "site": "site-uuid",
  "site_name": "Green Valley Construction",
  "worker": "worker-uuid",
  "worker_name": "Ramesh Kumar",
  "worker_phone": "+919876543210",
  "role_on_site": "Plumber",
  "assigned_at": "2026-01-03T11:30:00Z",
  "is_active": true
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/contractors/sites/abc-123/assign/ \
  -H "Authorization: Bearer CONTRACTOR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "worker_id": "worker-uuid-123",
    "role_on_site": "Plumber"
  }'
```

---

### 6. List Assigned Workers

**GET** `/api/v1/contractors/sites/{site_id}/workers/`

List all workers assigned to a site.

**Response (200):**
```json
[
  {
    "id": "assignment-1",
    "worker": "worker-uuid-1",
    "worker_name": "Ramesh Kumar",
    "worker_phone": "+919876543210",
    "role_on_site": "Plumber",
    "assigned_at": "2026-01-01T09:00:00Z",
    "is_active": true
  }
]
```

**Example:**
```bash
curl http://localhost:8000/api/v1/contractors/sites/abc-123/workers/ \
  -H "Authorization: Bearer CONTRACTOR_JWT_TOKEN"
```

---

### 7. Mark Attendance

**POST** `/api/v1/contractors/sites/{site_id}/attendance/`

Mark attendance for a worker at the site.

**Request:**
```json
{
  "worker_id": "worker-uuid-123",
  "status": "present",
  "checkin_time": "2026-01-03T09:00:00Z",
  "date": "2026-01-03",
  "notes": "On time"
}
```

**Status Options:**
- `present`: Worker is present
- `absent`: Worker is absent
- `half_day`: Worker worked half day
- `on_leave`: Worker is on approved leave

**Response (201):**
```json
{
  "id": "attendance-uuid",
  "site": "site-uuid",
  "site_name": "Green Valley Construction",
  "worker": "worker-uuid",
  "worker_name": "Ramesh Kumar",
  "attendance_date": "2026-01-03",
  "status": "present",
  "checkin_time": "2026-01-03T09:00:00Z",
  "checkout_time": null,
  "notes": "On time"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/contractors/sites/abc-123/attendance/ \
  -H "Authorization: Bearer CONTRACTOR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "worker_id": "worker-uuid-123",
    "status": "present",
    "date": "2026-01-03"
  }'
```

---

### 8. Get Attendance Records

**GET** `/api/v1/contractors/sites/{site_id}/attendance/?date=2026-01-03`

Get attendance records for a specific date (defaults to today).

**Query Parameters:**
- `date` (string): Date in YYYY-MM-DD format

**Response (200):**
```json
[
  {
    "id": "attendance-1",
    "worker_name": "Ramesh Kumar",
    "worker_phone": "+919876543210",
    "attendance_date": "2026-01-03",
    "status": "present",
    "checkin_time": "2026-01-03T09:00:00Z",
    "checkout_time": null
  }
]
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/contractors/sites/abc-123/attendance/?date=2026-01-03" \
  -H "Authorization: Bearer CONTRACTOR_JWT_TOKEN"
```

---

### 9. Site Dashboard Metrics

**GET** `/api/v1/contractors/sites/{site_id}/dashboard/?date=2026-01-03`

Get aggregated dashboard metrics for a site.

**Query Parameters:**
- `date` (string): Date in YYYY-MM-DD format (defaults to today)

**Response (200):**
```json
{
  "date": "2026-01-03",
  "total_assigned": 10,
  "present_count": 8,
  "absent_count": 2,
  "half_day_count": 0,
  "on_leave_count": 0,
  "attendance_rate": 80.0,
  "on_site_now_count": 6,
  "pending_jobs_count": 3,
  "recent_timeline": [
    {
      "event_type": "custom",
      "actor": "Ramesh Kumar",
      "timestamp": "2026-01-03T09:00:00Z",
      "details": {
        "event": "worker_checked_in",
        "site_name": "Green Valley Construction"
      }
    }
  ]
}
```

**Metrics Explained:**
- **total_assigned**: Total workers assigned to this site
- **present_count**: Workers marked present today
- **absent_count**: Workers marked absent today
- **attendance_rate**: Percentage of workers present (present/total * 100)
- **on_site_now_count**: Workers currently on site (checked in within last 12 hours, not checked out)
- **pending_jobs_count**: Jobs with status 'requested' or 'confirmed' for this site
- **recent_timeline**: Last 10 timeline events related to this site

**Example:**
```bash
curl "http://localhost:8000/api/v1/contractors/sites/abc-123/dashboard/?date=2026-01-03" \
  -H "Authorization: Bearer CONTRACTOR_JWT_TOKEN"
```

---

## Admin Interface

### Site Management

**Admin URL:** `/admin/contractors/site/`

**Features:**
- List view with filters (is_active, created_at, start_date)
- Search by name, address, contractor
- Bulk edit capabilities

### Attendance Management

**Admin URL:** `/admin/contractors/siteattendance/`

**Features:**
- List view with filters (status, attendance_date, site)
- Date hierarchy for easy navigation
- **Bulk Actions:**
  - Mark selected as Present
  - Mark selected as Absent
  - **Export to CSV**

#### CSV Export

1. Go to Site Attendance admin
2. Filter by site and date range
3. Select attendance records
4. Choose "Export selected to CSV" from actions dropdown
5. Click "Go"
6. CSV file downloads with columns: Site, Worker, Phone, Date, Status, Check-in, Check-out, Notes

---

## Performance & Scaling

### Current Implementation

**Optimizations:**
- Database indexes on `(site, attendance_date)` and `(worker, attendance_date)`
- `select_related()` and `prefetch_related()` to avoid N+1 queries
- ORM aggregation for dashboard metrics (no Python-level loops)

**Good For:**
- <100 sites per contractor
- <1000 workers per site
- <10,000 attendance records per day

### Scaling Recommendations

For larger deployments (>1000 sites or >10,000 workers):

**1. Daily Summary Table:**
```python
# Create denormalized daily summary
class SiteDailySummary(models.Model):
    site = models.ForeignKey(Site)
    date = models.DateField()
    total_assigned = models.IntegerField()
    present_count = models.IntegerField()
    absent_count = models.IntegerField()
    attendance_rate = models.FloatField()
    
    # Updated via Celery task nightly
```

**2. Caching:**
```python
# Cache dashboard for 15 minutes
cache_key = f'site_dashboard_{site_id}_{date}'
cached = cache.get(cache_key)
if cached:
    return cached
    
# ... compute metrics ...
cache.set(cache_key, data, timeout=900)
```

**3. Background Processing:**
- Use Celery tasks to compute daily summaries
- Async attendance marking for bulk operations

---

## Security

### Authorization

**Contractors:**
- Can only access their own sites
- Can assign workers to their sites
- Can mark attendance for assigned workers

**Admins:**
- Can access all sites
- Can modify any data
- Can export attendance reports

**Permission Check:**
```python
# In SiteViewSet
def get_queryset(self):
    if self.request.user.is_staff:
        return Site.objects.all()
    return Site.objects.filter(
        contractor__user=self.request.user
    )
```

### Data Validation

- Worker must be assigned to site before marking attendance
- Duplicate attendance for same worker/site/date is prevented (unique constraint)
- Invalid dates return 400 Bad Request

---

## Timeline Events

The system creates timeline events for key actions:

**Worker Assigned:**
```json
{
  "event": "worker_assigned_to_site",
  "site_id": "abc-123",
  "site_name": "Green Valley Construction",
  "worker_id": "worker-123",
  "role": "Plumber"
}
```

**Worker Checked In:**
```json
{
  "event": "worker_checked_in",
  "site_id": "abc-123",
  "site_name": "Green Valley Construction",
  "checkin_time": "2026-01-03T09:00:00Z"
}
```

These events appear in:
- Site dashboard `recent_timeline`
- Global timeline API
- Contractor notifications (if configured)

---

## Error Handling

**Common Errors:**

**401 Unauthorized**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**403 Forbidden**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

**404 Not Found**
```json
{
  "detail": "Not found."
}
```

**400 Bad Request (Invalid Date)**
```json
{
  "error": "Invalid date format. Use YYYY-MM-DD"
}
```

---

## Testing

Run site management tests:
```bash
python manage.py test apps.contractors.tests.test_sites
```

**Test Coverage:**
- ✅ Site creation
- ✅ List sites (contractor-scoped)
- ✅ Worker assignment
- ✅ Attendance marking
- ✅ Dashboard metrics aggregation
- ✅ Permission checks
- ✅ CSV export

---

## Best Practices

1. **Mark Attendance Early:** Mark attendance at start of work day for accurate metrics
2. **Use Check-in Times:** Always include `checkin_time` for present status
3. **Batch Operations:** Use admin bulk actions for marking attendance for multiple workers
4. **Monitor Dashboard:** Check dashboard daily for attendance rates and trends
5. **Export Reports:** Regularly export CSV for payroll and compliance

---

## Future Enhancements

- [ ] Geofencing: Auto-mark attendance when worker enters site boundary
- [ ] Face recognition: Biometric attendance via mobile app
- [ ] Real-time notifications: Push alerts when workers check in/out
- [ ] Attendance analytics: Trends, patterns, predictive insights
- [ ] Payroll integration: Auto-calculate wages based on attendance
- [ ] Break tracking: Record lunch breaks and overtime

---

## Support

For API issues or questions:
- **Documentation:** `/api/schema/swagger/` (Swagger UI)
- **Admin:** Contact system administrator

---

## Changelog

**v1.0.0 (2026-01-03)**
- ✅ Initial release
- ✅ Site CRUD operations
- ✅ Worker assignment
- ✅ Daily attendance tracking
- ✅ Dashboard metrics
- ✅ CSV export
