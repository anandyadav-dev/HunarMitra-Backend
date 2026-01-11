# Worker Availability & Nearby Search API

## Overview

The HunarMitra backend now supports Uber-like worker availability tracking and location-based nearby worker search. Workers can go online/offline, update their location, and clients can find available workers sorted by distance, price, or rating.

---

## API Endpoints

### 1. Toggle Worker Availability

**POST** `/api/v1/workers/me/availability/`

Toggle worker availability status (online/offline).

**Authentication:** Required (Worker only)

**Request Body:**
```json
{
  "is_available": true
}
```

**Response:**
```json
{
  "status": "success",
  "is_available": true,
  "availability_updated_at": "2026-01-03T11:15:00Z"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/workers/me/availability/ \
  -H "Authorization: Bearer WORKER_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_available": true}'
```

---

### 2. Update Worker Location

**POST** `/api/v1/workers/me/location/`

Update worker's current location for nearby search.

**Authentication:** Required (Worker only)

**Request Body:**
```json
{
  "lat": 26.8467,
  "lng": 80.9462
}
```

**Response:**
```json
{
  "status": "success",
  "location": {
    "lat": 26.8467,
    "lng": 80.9462
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/workers/me/location/ \
  -H "Authorization: Bearer WORKER_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"lat": 26.8467, "lng": 80.9462}'
```

**Notes:**
- If worker is available, a realtime event is published to `worker_{id}` channel
- Location is only used for nearby search when worker is available

---

### 3. Nearby Worker Search

**GET** `/api/v1/workers/search/nearby/`

Find available workers near a location.

**Authentication:** None required (Public endpoint)

**Query Parameters:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `lat` | Yes | - | Search latitude |
| `lng` | Yes | - | Search longitude |
| `radius_km` | No | 5 | Search radius in kilometers |
| `service_id` | No | - | Filter by service ID |
| `min_price` | No | - | Minimum price filter |
| `max_price` | No | - | Maximum price filter |
| `sort_by` | No | `distance` | Sort by: `distance`, `price`, or `rating` |
| `order` | No | `asc` | Sort order: `asc` or `desc` |
| `page` | No | 1 | Page number |
| `per_page` | No | 20 | Items per page |

**Response:**
```json
{
  "count": 12,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 23,
      "user_name": "Ramesh Kumar",
      "service": "Plumber",
      "price_amount": "350.00",
      "price_type": "per_day",
      "rating": "4.60",
      "latitude": "26.8500",
      "longitude": "80.9500",
      "distance_km": "1.82",
      "is_available": true
    }
  ]
}
```

**Examples:**

```bash
# Basic search - workers within 5km
curl "http://localhost:8000/api/v1/workers/search/nearby/?lat=26.8467&lng=80.9462"

# Search within 10km, sorted by price
curl "http://localhost:8000/api/v1/workers/search/nearby/?lat=26.8467&lng=80.9462&radius_km=10&sort_by=price"

# Filter by service and price range
curl "http://localhost:8000/api/v1/workers/search/nearby/?lat=26.8467&lng=80.9462&service_id=1&min_price=300&max_price=800"

# Sort by rating (highest first)
curl "http://localhost:8000/api/v1/workers/search/nearby/?lat=26.8467&lng=80.9462&sort_by=rating&order=desc"
```

---

## Distance Calculation

The API uses the **Haversine formula** to calculate great-circle distance between two points on Earth. This approach:

- ✅ No PostGIS dependency required
- ✅ Works on standard PostgreSQL or SQLite
- ✅ Accurate for distances up to ~1000km
- ✅ Fast for small datasets (<10,000 workers)

**Formula:**
```
a = sin²(Δlat/2) + cos(lat1) × cos(lat2) × sin²(Δlong/2)
c = 2 × atan2(√a, √(1−a))
distance = R × c  (where R = 6371 km, Earth's radius)
```

**Accuracy:**
- ±0.5% for distances < 1000km
- Suitable for city-scale searches

---

## Filters & Sorting

### Availability Filter
Only workers with is_available=True are returned. Workers who are offline are automatically excluded.

### Service Filter
Filter by service_id to show only workers offering a specific service (e.g., plumbers, electricians).

### Price Range
Use min_price and max_price to filter workers within a budget range.

### Sorting Options

**distance** (default):
- Workers closest to the search location appear first
- Most relevant for "find workers near me" use case

**price**:
- Sort by worker's price_amount
- order=asc: cheapest first
- order=desc: most expensive first

**rating**:
- Sort by worker rating
- order=asc: lowest rated first (rarely used)
- order=desc: highest rated first (recommended)

---

## Realtime Events

### Availability Changed

When a worker toggles availability, a realtime event is published to `worker_{id}`:

```json
{
  "type": "availability_changed",
  "is_available": true,
  "timestamp": "2026-01-03T11:15:00Z"
}
```

### Location Updated

When an available worker updates location:

```json
{
  "type": "location_updated",
  "lat": 26.8467,
  "lng": 80.9462,
  "timestamp": "2026-01-03T11:16:00Z"
}
```

**Note:** Location updates only publish realtime events if worker is available.

---

## Admin Interface

### Features

- **Availability Icon:** 🟢 Online / ⚫ Offline
- **Location Display:** Shows lat/lng (4 decimal precision)
- **Bulk Actions:**
  - "Set workers as available (online)"
  - "Set workers as unavailable (offline)"
- **Filters:** is_available, availability_status, price_type, created_at

### Example Usage

1. Select multiple workers
2. Choose "Set workers as available" from actions dropdown
3. Click "Go"
4. Workers are marked online with availability_updated_at timestamp

---

## Performance Considerations

### Current Implementation (Haversine)

**good For:**
- < 10,000 workers
- Regional/city-scale searches
- Simple deployment (no PostGIS)

**Limitations:**
- Distance calculated in Python (not database)
- All workers loaded into memory
- No spatial index

### Scaling Recommendations

For >10,000 workers or national-scale:

1. **Add PostGIS:**
```sql
CREATE EXTENSION postgis;
ALTER TABLE worker_profiles 
  ADD COLUMN location geometry(Point, 4326);
CREATE INDEX worker_location_idx ON worker_profiles USING GIST(location);
```

2. **Use ST_DWithin:**
```python
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D

workers = WorkerProfile.objects.filter(
    is_available=True,
    location__distance_lte=(user_point, D(km=10))
).annotate(
    distance=Distance('location', user_point)
).order_by('distance')
```

---

## Testing

### Manual Testing

**1. Create available worker:**
```bash
# Worker goes online
curl -X POST http://localhost:8000/api/v1/workers/me/availability/ \
  -H "Authorization: Bearer WORKER_TOKEN" \
  -d '{"is_available": true}'

# Update location
curl -X POST http://localhost:8000/api/v1/workers/me/location/ \
  -H "Authorization: Bearer WORKER_TOKEN" \
  -d '{"lat": 26.8467, "lng": 80.9462}'
```

**2. Search nearby:**
```bash
# Find workers within 5km
curl "http://localhost:8000/api/v1/workers/search/nearby/?lat=26.8467&lng=80.9462"
```

**3. Verify:**
- Worker appears in results
- distance_km is calculated correctly
- Only available workers returned

### Seed Data

The `seed_demo_data` command creates workers with realistic locations around Lucknow:

- **Raju** (Gomti Nagar): 26.8500, 80.9500 - Online ✅
- **Sunil** (Hazratganj): 26.8400, 80.9400 - Online ✅
- **Ramesh** (Aliganj): 26.8600, 80.9600 - Offline ❌

Run: `python manage.py seed_demo_data`

---

## Frontend Integration

### Example Flow

**1. Worker App - Go Online:**
```dart
// Toggle availability
final response = await http.post(
  Uri.parse('$baseUrl/workers/me/availability/'),
  headers: {'Authorization': 'Bearer $token'},
  body: jsonEncode({'is_available': true}),
);

// Update location periodically
Timer.periodic(Duration(minutes: 1), (timer) async {
  final position = await Geolocator.getCurrentPosition();
  await http.post(
    Uri.parse('$baseUrl/workers/me/location/'),
    headers: {'Authorization': 'Bearer $token'},
    body: jsonEncode({
      'lat': position.latitude,
      'lng': position.longitude,
    }),
  );
});
```

**2. Client App - Find Workers:**
```dart
// Get current location
final position = await Geolocator.getCurrentPosition();

// Search nearby workers
final response = await http.get(
  Uri.parse('$baseUrl/workers/search/nearby/'),
  queryParameters: {
    'lat': position.latitude.toString(),
    'lng': position.longitude.toString(),
    'radius_km': '5',
    'sort_by': 'distance',
  },
);

// Display on map
for (var worker in response.data['results']) {
  addMarker(
    lat: worker['latitude'],
    lng: worker['longitude'],
    title: worker['user_name'],
    distance: '${worker['distance_km']} km away',
  );
}
```

---

## Error Handling

### Common Errors

**400 Bad Request**
```json
{
  "error": "lat and lng parameters are required"
}
```

**400 Bad Request**
```json
{
  "error": "Invalid coordinates"
}
```

**404 Not Found**
```json
{
  "error": "Worker profile not found"
}
```

---

## Best Practices

1. **Rate Limiting:** Limit location updates to once per minute
2. **Battery Optimization:** Pause location updates when app is backgrounded
3. **Error Handling:** Retry failed location updates with exponential backoff
4. **Caching:** Cache nearby results for 30-60 seconds
5. **User Experience:** Show distance in human-readable format ("1.8 km away")

---

## Future Enhancements

- [ ] ETA calculation based on distance and traffic
- [ ] Worker clustering on map for better visualization
- [ ] Historical location tracking for analytics
- [ ] Geofencing for service area boundaries
- [ ] PostGIS integration for larger scale
- [ ] Real-time worker position updates on map

---

## References

- Haversine Formula: https://en.wikipedia.org/wiki/Haversine_formula
- PostGIS Distance: https://postgis.net/docs/ST_Distance.html
- Django GIS: https://docs.djangoproject.com/en/4.2/ref/contrib/gis/
