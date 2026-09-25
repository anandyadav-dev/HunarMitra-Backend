# Hunar Mitra Mobile API Integration Guide

## 1. Overview

Mobile App
    ↓
FastAPI Backend
    ↓
Service Layer
    ↓
MySQL

Supported mobile roles:
- Customer
- Worker / Labour
- Contractor

The mobile application must use the existing backend APIs to perform all functions. Do not mock functionality.

---

## 4. Base URL

Production URL: `http://18.142.114.233:8000`
Local Development: `http://127.0.0.1:8000` (Use your machine's local IP for 
Base API Path: `/api/v1`

---

## 5. Authentication

Authentication flow is OTP-based:
Request OTP
      ↓
Verify OTP
      ↓
Access Token
      ↓
Authenticated APIs

### Endpoints
**1. Request OTP**
- **Method:** POST
- **URL:** `/api/v1/auth/login-otp`
- **Request:** `{ "phone_number": "+919999999999" }`
- **Response:** `{ "message": "OTP sent successfully" }`

**2. Verify OTP**
- **Method:** POST
- **URL:** `/api/v1/auth/verify-otp`
- **Request:** `{ "phone_number": "+919999999999", "otp": "1234" }`
- **Response:** `{ "access_token": "eyJ...", "token_type": "bearer" }`

To authenticate API requests, include the access token in the Authorization header:
```http
Authorization: Bearer <access_token>
```

---

## 6. Common Response Format

Responses follow the standard REST structure without a nested `data` envelope.
Successful responses directly return the requested object or list.

Example List:
```json
{
  "items": [ ... ],
  "total": 100
}
```

Example Object:
```json
{
  "id": 1,
  "name": "Example"
}
```

---

## 7. Common Error Format

FastAPI uses standard HTTP status codes and a consistent JSON format for errors.

**Validation Error (422)**
```json
{
  "detail": [
    {
      "loc": ["body", "phone_number"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Unauthorized (401)**
```json
{
  "detail": "Not authenticated"
}
```

**Forbidden / Bad Request / Not Found (400, 403, 404)**
```json
{
  "detail": "Error message here"
}
```

---

## 8. API DIRECTORY

| Module | Method | Endpoint | Auth | Role | Purpose |
| ------ | ------ | -------- | ---- | ---- | ------- |
| Public | GET | `/api/v1/public/categories` | No | Any | Get available categories |
| Auth | POST | `/api/v1/auth/register` | No | Any | Register user |
| Auth | POST | `/api/v1/auth/login-otp` | No | Any | Request OTP |
| Auth | POST | `/api/v1/auth/verify-otp` | No | Any | Verify OTP and get Token |
| Customer | GET | `/api/v1/workers/nearby` | Yes | Customer/Contractor | Search workers |
| Customer | GET | `/api/v1/workers/{id}` | Yes | Customer/Contractor | View worker profile |
| Bookings | POST | `/api/v1/bookings/create` | Yes | Customer/Contractor | Create a booking |
| Bookings | GET | `/api/v1/bookings/my-history` | Yes | Any | View call/booking history |
| Worker | GET | `/api/v1/worker/dashboard` | Yes | Worker | Get worker dashboard stats |
| Worker | PUT | `/api/v1/worker/status` | Yes | Worker | Update availability status |
| Worker | POST | `/api/v1/worker/kyc` | Yes | Worker | Submit KYC details |
| Contractor| POST | `/api/v1/contractor/kyc`| Yes | Contractor | Submit KYC details |

---

## 9. CUSTOMER APIs

### Search Workers
- **Endpoint:** `/api/v1/workers/nearby`
- **Method:** GET
- **Authentication:** Required
- **Role:** Customer / Contractor
- **Query Parameters:**
  - `lat` (float, required): User latitude
  - `lng` (float, required): User longitude
  - `radius` (float, optional): Search radius (km)
  - `category` (string, optional): Filter by category
- **Response:**
```json
{
  "total": 10,
  "items": [
    {
      "id": 1,
      "user_id": 10,
      "category": "Plumber",
      "rating": 4.5
    }
  ]
}
```
- **Mobile Usage:** Call this API when the Worker Search map or list screen loads.

### Create Booking (Call Action)
- **Endpoint:** `/api/v1/bookings/create`
- **Method:** POST
- **Authentication:** Required
- **Role:** Customer / Contractor
- **Request Body:**
```json
{
  "worker_id": 1,
  "job_description": "Need a plumber"
}
```

---

## 10. WORKER APIs

### Worker Dashboard
- **Endpoint:** `/api/v1/worker/dashboard`
- **Method:** GET
- **Authentication:** Required
- **Role:** Worker
- **Mobile Usage:** Call on Worker Home screen.

### Worker Status Update
- **Endpoint:** `/api/v1/worker/status`
- **Method:** PUT
- **Authentication:** Required
- **Role:** Worker
- **Request Body:**
```json
{
  "is_available": true,
  "lat": 12.34,
  "lng": 56.78
}
```

### Worker KYC Verification
- **Endpoint:** `/api/v1/worker/kyc`
- **Method:** POST
- **Authentication:** Required
- **Role:** Worker
- **Request Body:** Multipart Form Data or JSON as implemented (Check backend schemas).

---

## 11. CONTRACTOR APIs

### Contractor KYC
- **Endpoint:** `/api/v1/contractor/kyc`
- **Method:** POST
- **Authentication:** Required
- **Role:** Contractor

Contractors primarily use Customer APIs (`/api/v1/workers/nearby`) to find and hire workers.

---

## 12. WORKER SEARCH API

- **Endpoint:** `/api/v1/workers/nearby`
- **Method:** GET
- **Supported Query Parameters:**

| Parameter | Type | Required | Example | Description |
| --------- | ---- | -------- | ------- | ----------- |
| lat       | float| Yes      | 28.704  | Latitude |
| lng       | float| Yes      | 77.102  | Longitude |
| radius    | int  | No       | 15      | Distance in KM |
| category  | str  | No       | Plumber | Filter by job |

---

## 13. WORKER PROFILE API

### Get Worker Profile
- **Endpoint:** `/api/v1/workers/{id}`
- **Method:** GET
- **Authentication:** Required

---

## 14. FAVOURITES / SAVED WORKERS

Not implemented in current backend.

---

## 15. CALL APIs

Calls are logged as Bookings in this system.
1. Mobile calls `/api/v1/bookings/create` to log the interaction.
2. Backend returns the worker's contact number.
3. Mobile app invokes native phone dialer with the returned number.

---

## 16. REVIEW & RATING APIs

Not implemented as standalone APIs in the current backend.

---

## 17. VERIFICATION APIs

Worker verification uses the `/api/v1/worker/kyc` endpoint.
Supported statuses:
- pending
- approved
- rejected

---

## 18. PROFILE & LOCATION APIs

Location is updated via `/api/v1/worker/status`.

---

## 19. NOTIFICATION APIs

Not implemented in current backend.

---

## 20. PAGINATION

Pagination uses standard `limit` and `skip`.
Query Parameters:
- `skip` (default 0)
- `limit` (default 100)

Response Format:
```json
{
  "items": [...],
  "total": 50
}
```

---

## 21. FILE UPLOAD

File uploads (e.g. KYC docs) use `multipart/form-data`.
- **Content-Type:** `multipart/form-data`
- Ensure boundaries are set correctly by the mobile networking library.

---

## 22. TOKEN REFRESH

Refresh token flow is not implemented in the current backend.
Users must log in again with OTP if the access token expires.

---

## 23. ROLE & PERMISSION MATRIX

| API | Customer | Worker | Contractor | Admin |
| --- | -------- | ------ | ---------- | ----- |
| /public/* | Yes | Yes | Yes | Yes |
| /workers/nearby | Yes | No | Yes | Yes |
| /bookings/* | Yes | Yes | Yes | Yes |
| /worker/* | No | Yes | No | Yes |
| /contractor/* | No | No | Yes | Yes |

---

## 24. MOBILE SCREEN → API MAPPING

### Customer
| Mobile Screen | API | Method | When Called |
| ------------- | --- | ------ | ----------- |
| Login / OTP | `/api/v1/auth/login-otp` | POST | Submitting phone number |
| Verify OTP | `/api/v1/auth/verify-otp` | POST | Submitting OTP |
| Home / Search | `/api/v1/workers/nearby` | GET | Loading worker map/list |
| Worker Profile | `/api/v1/workers/{id}` | GET | Opening worker details |
| Call History | `/api/v1/bookings/my-history`| GET | Viewing past calls |

### Worker
| Mobile Screen | API | Method | When Called |
| ------------- | --- | ------ | ----------- |
| Registration | `/api/v1/auth/register` | POST | First time signup |
| Dashboard | `/api/v1/worker/dashboard` | GET | Home screen load |
| Status Toggle | `/api/v1/worker/status` | PUT | Toggling availability |

---

## 25. END-TO-END CUSTOMER FLOW

1. Request OTP: `POST /api/v1/auth/login-otp`
2. Verify OTP: `POST /api/v1/auth/verify-otp`
3. Store access token in mobile secure storage.
4. Call Worker Search API: `GET /api/v1/workers/nearby?lat=...&lng=...`
5. Open Worker Profile: `GET /api/v1/workers/{id}`
6. Request Call: `POST /api/v1/bookings/create`
7. Open native dialer.

---

## 26. END-TO-END WORKER FLOW

1. Registration: `POST /api/v1/auth/register`
2. OTP verification: `POST /api/v1/auth/verify-otp`
3. Complete KYC: `POST /api/v1/worker/kyc`
4. Load Dashboard: `GET /api/v1/worker/dashboard`
5. Accept Booking: `PUT /api/v1/bookings/{id}/respond`

---

## 27. END-TO-END CONTRACTOR FLOW

1. Registration: `POST /api/v1/auth/register`
2. Verify OTP: `POST /api/v1/auth/verify-otp`
3. Complete Contractor KYC: `POST /api/v1/contractor/kyc`
4. Find Labour: `GET /api/v1/workers/nearby`
5. Hire: `POST /api/v1/bookings/create`

---

## 28. COMPLETE CURL EXAMPLES

```bash
curl -X GET \
  "http://18.142.114.233:8000/api/v1/workers/nearby?lat=28.704&lng=77.102" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>"
```

---

## 29. MOBILE CODE EXAMPLES

**Dart / Flutter (http package):**
```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

Future<void> fetchCategories() async {
  final response = await http.get(
    Uri.parse('http://18.142.114.233:8000/api/v1/public/categories'),
  );
  
  if (response.statusCode == 200) {
    var data = jsonDecode(response.body);
    print(data);
  }
}
```

---

## 30. REAL RESPONSE EXAMPLES

**Example Response for `/api/v1/public/categories`**
```json
[
  {
    "name": "Plumber",
    "icon_url": "/static/icons/plumber.png",
    "base_price": 100.0,
    "id": "uuid-string"
  }
]
```

---

## 31. NULL / OPTIONAL FIELD HANDLING

Fields like `icon_url`, `rating`, or `experience_years` may return `null`. Mobile clients must use nullable types (e.g. `String?` in Dart) to avoid JSON parsing crashes.

---

## 32. COMMON INTEGRATION MISTAKES

- **Missing Authorization header**: Ensure `Bearer ` is prepended to the token.
- **Localhost resolution**: Using `localhost` or `127.0.0.1` on Android Emulator will fail. Use `10.0.2.2` or your machine's local network IP.
- **Incorrect multipart fields**: When uploading images, ensure the field name matches the backend schema exactly (e.g., `file` vs `image`).

---

## 33. API INTEGRATION CHECKLIST

[x] Base URL configured
[x] Authentication integrated
[x] OTP integrated
[x] JWT integrated
[ ] Refresh token integrated if available (Not implemented)
[x] Customer APIs integrated
[x] Worker APIs integrated
[x] Contractor APIs integrated
[x] Worker search integrated
[x] Worker profile integrated
[ ] Favourites integrated (Not implemented)
[ ] Saved workers integrated (Not implemented)
[x] Calls integrated
[x] Call history integrated
[ ] Reviews integrated (Not implemented)
[ ] Ratings integrated (Not implemented)
[x] Verification integrated
[x] File upload integrated
[x] Pagination integrated
[x] Error handling integrated
