# Realtime WebSocket API Documentation

## Overview

HunarMitra supports realtime updates via WebSockets using Django Channels. Clients can subscribe to booking channels to receive live status updates and location tracking.

---

## WebSocket Endpoints

### 1. Subscribe to Booking Updates

**Endpoint:** `ws://localhost:8000/ws/bookings/{booking_id}/`

**Authentication:** JWT token required (query parameter)

**Authorized Users:**
- Booking owner (employer)
- Assigned worker
- Admin/staff

**Example Connection (JavaScript):**
```javascript
const token = 'eyJ0eXAiOiJKV1QiLCJhbGc...';
const bookingId = 'abc-123-def-456';

const ws = new WebSocket(
  `ws://localhost:8000/ws/bookings/${bookingId}/?token=${token}`
);

ws.onopen = () => {
  console.log('Connected to booking channel');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event received:', data);
  
  if (data.type === 'booking_status') {
    // Handle status update
    updateBookingStatus(data.status);
  } else if (data.type === 'location_update') {
    // Update map with worker location
    updateMarker(data.lat, data.lng);
  }
};

ws.onclose = () => {
  console.log('Disconnected');
};

// Send ping to keep connection alive
setInterval(() => {
  ws.send(JSON.stringify({ type: 'ping' }));
}, 30000);
```

**Example Connection (Flutter):**
```dart
import 'package:web_socket_channel/web_socket_channel.dart';

final token = 'eyJ0eXAiOiJKV1QiLCJhbGc...';
final bookingId = 'abc-123-def-456';

final channel = WebSocketChannel.connect(
  Uri.parse('ws://localhost:8000/ws/bookings/$bookingId/?token=$token')
);

channel.stream.listen(
  (message) {
    final data = jsonDecode(message);
    print('Event: $data');
    
    if (data['type'] == 'booking_status') {
      // Update UI with new status
      setState(() {
        bookingStatus = data['status'];
      });
    } else if (data['type'] == 'location_update') {
      // Update map marker
      updateWorkerLocation(data['lat'], data['lng']);
    }
  },
  onDone: () {
    print('Connection closed');
  },
  onError: (error) {
    print('Error: $error');
  },
);

// Close connection when done
channel.sink.close();
```

---

### 2. Subscribe to User Notifications

**Endpoint:** `ws://localhost:8000/ws/notifications/`

**Authentication:** JWT token required

**Receives:** All notifications for authenticated user

**Example:**
```javascript
const ws = new WebSocket(
  `ws://localhost:8000/ws/notifications/?token=${token}`
);

ws.onmessage = (event) => {
  const notification = JSON.parse(event.data);
  showNotification(notification.title, notification.message);
};
```

---

## Event Types

### Booking Status Update

Sent when booking status changes.

```json
{
  "type": "booking_status",
  "booking_id": "abc-123-def-456",
  "status": "on_the_way",
  "event_type": "booking_on_the_way",
  "actor": "Worker Name",
  "timestamp": "2026-01-03T11:00:00Z"
}
```

**Status Values:**
- `requested` - Booking created
- `confirmed` - Booking confirmed
- `on_the_way` - Worker is on the way
- `arrived` - Worker has arrived
- `completed` - Service completed
- `cancelled` - Booking cancelled

---

### Location Update

Sent when worker updates their location.

```json
{
  "type": "location_update",
  "booking_id": "abc-123-def-456",
  "lat": 28.6139,
  "lng": 77.2090,
  "timestamp": "2026-01-03T11:05:00Z",
  "actor": "Worker Name"
}
```

---

### Connection Established

Sent immediately after successful connection.

```json
{
  "type": "connection_established",
  "booking_id": "abc-123-def-456",
  "message": "Connected to booking updates"
}
```

---

## HTTP Endpoints

### Update Worker Location

**POST** `/api/v1/tracking/{booking_id}/`

Update worker's current location for a booking.

**Authorization:** JWT token (worker or admin)

**Request Body:**
```json
{
  "lat": 28.6139,
  "lng": 77.2090,
  "timestamp": "2026-01-03T11:05:00Z"  // optional
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Location updated",
  "booking_id": "abc-123-def-456",
  "location": {
    "lat": 28.6139,
    "lng": 77.2090,
    "timestamp": "2026-01-03T11:05:00Z"
  }
}
```

**Rate Limit:** 1 request per 2 seconds

---

## Setup & Configuration

### Installation

1. **Install dependencies:**
```bash
pip install channels channels-redis daphne
```

2. **Configure Redis** (for production):
```bash
# .env file
REDIS_URL=redis://localhost:6379/0
```

3. **Run ASGI server:**
```bash
# Development with Daphne
daphne -b 0.0.0.0 -p 8000 hunarmitra.asgi:application

# Or with Uvicorn
uvicorn hunarmitra.asgi:application --host 0.0.0.0 --port 8000

# Production with Daphne
daphne -b 0.0.0.0 -p 8000 -e ssl:443:privateKey=key.pem:certKey=cert.pem hunarmitra.asgi:application
```

### Testing with wscat

```bash
# Install wscat
npm install -g wscat

# Connect to booking channel
wscat -c "ws://localhost:8000/ws/bookings/abc-123/?token=YOUR_JWT_TOKEN"

# Once connected, you'll receive events
# Send ping
> {"type": "ping"}
< {"type": "pong"}
```

---

## Architecture

### Channel Layers

- **Production:** Redis backend (`channels_redis`)
- **Development/Testing:** In-memory backend

Configuration auto-selects based on `REDIS_URL` environment variable.

### Graceful Fallback

The `publish_event` helper tries multiple backends:
1. **Django Channels** (WebSocket) - if installed
2. **Redis PUBLISH** - if Redis available
3. **Logging** - always works

This ensures the system works even without Channels installed.

---

## Security

### Authentication

- JWT token passed via query parameter: `?token=eyJ...`
- Alternative: `Sec-WebSocket-Protocol: jwt, <token>`
- Token validated using `rest_framework_simplejwt`

### Authorization

**Booking Channel:**
- Owner can subscribe to their bookings
- Assigned worker can subscribe
- Admin/staff can subscribe to any booking
- Others are rejected with close code 4003

**User Notifications:**
- Only authenticated users
- Receives only own notifications

---

## Error Handling

### Close Codes

- `4001` - Unauthenticated (missing/invalid token)
- `4003` - Unauthorized (not allowed to subscribe)

### Client Reconnection

Implement exponential backoff:
```javascript
function connectWithRetry(url, retries = 0) {
  const ws = new WebSocket(url);
  
  ws.onclose = () => {
    const delay = Math.min(1000 * Math.pow(2, retries), 30000);
    setTimeout(() => connectWithRetry(url, retries + 1), delay);
  };
  
  return ws;
}
```

---

##Best Practices

1. **Keep-Alive:** Send ping every 30-60 seconds
2. **Reconnection:** Implement automatic reconnection with backoff
3. **State Management:** Re-fetch booking state on reconnect
4. **Battery:** On mobile, disconnect when app backgrounded
5. **Rate Limiting:** Don't update location more than once per 2 seconds

---

## Example: Live Tracking Map

```javascript
// Initialize map
const map = L.map('map').setView([28.6, 77.2], 13);

// Add marker for worker
const workerMarker = L.marker([28.6, 77.2]).addTo(map);

// Connect to WebSocket
const ws = new WebSocket(
  `ws://localhost:8000/ws/bookings/${bookingId}/?token=${token}`
);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'location_update') {
    // Update marker position
    workerMarker.setLatLng([data.lat, data.lng]);
    
    // Pan map to new location
    map.panTo([data.lat, data.lng]);
    
    // Update ETA (if available)
    if (data.eta_minutes) {
      document.getElementById('eta').textContent = 
        `${data.eta_minutes} minutes away`;
    }
  }
};
```

---

## Troubleshooting

**Connection Refused:**
- Ensure ASGI server is running (not WSGI)
- Check firewall rules allow WebSocket connections

**Authentication Failed:**
- Verify JWT token is valid and not expired
- Check token is passed in query parameter

**Messages Not Received:**
- Check Redis is running (production)
- Verify booking signals are publishing events
- Check server logs for errors

**High Latency:**
- Use Redis channel layer (not in-memory) in production
- Ensure Redis is on same network/region
- Consider connection pooling
