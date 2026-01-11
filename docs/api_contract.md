# API Contract Documentation

This document defines the strict data contract between the HunarMitra Backend and Frontend (Flutter).  
**Backend developers must ensure these signatures remain stable.**  
**Frontend developers can rely on these fields existing.**

---

## 1. Config & Theme (Launch)

### Active Theme
**Endpoint:** `GET /api/v1/core/theme/active/`  
**Contract:**
```json
{
  "name": "Default",
  "primary_color": "#FF5722",
  "secondary_color": "#FFC107",
  "font_family": "Roboto",
  "logo_url": "https://..."
}
```
**Required:** `primary_color`, `secondary_color`

---

## 2. Workers

### Worker Detail
**Endpoint:** `GET /api/v1/workers/{id}/`  
**Contract:**
```json
{
  "id": "uuid",
  "first_name": "Raju",
  "last_name": "Painter",
  "role": "worker",
  "avatar": "url_or_null",
  "worker_profile": {
    "skill": "Painter",
    "experience_years": 5,
    "price_per_hour": 500.0,
    "bio": "Expert...",
    "is_available": true,
    "lat": 28.61,
    "lng": 77.20,
    "rating": 4.5
  }
}
```
**Critical Fields:** `worker_profile.price_per_hour`, `worker_profile.lat/lng` (for Maps).

---

## 3. Bookings

### Create Booking
**Endpoint:** `POST /api/v1/bookings/`  
**Payload:**
```json
{
  "worker_id": "uuid",
  "job_description": "Fix tap",
  "scheduled_time": "ISO-8601",
  "lat": 28.6,
  "lng": 77.2,
  "address": {"text": "..."}
}
```

### Booking Status Flow
**Endpoint:** `PATCH /api/v1/bookings/{id}/`  
**Allowed Transitions:**
1. `requested` (Initial)
2. `confirmed`
3. `on_the_way`
4. `arrived`
5. `in_progress`
6. `completed`

---

## 4. Feature Flags

**Endpoint:** `GET /api/v1/flags/`  
**Contract:** Map of string keys to booleans.
```json
{
  "FEATURE_CSR": false,
  "FEATURE_CONTRACTOR": true
}
```

---

## Testing Verification
Run strict contract tests before any deploy:
```bash
pytest backend/tests/api_contract_tests/ -v
```
