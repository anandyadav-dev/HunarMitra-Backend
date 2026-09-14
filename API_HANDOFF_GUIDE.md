# Mazdoor App - Frontend API Integration & Handoff Guide

This document details all backend APIs, payload requirements, and endpoint behaviors for integration with the Customer and Worker (Partner) frontend mobile applications.

## Base Configuration
*   **Base URL**: `http://18.142.114.233:8000/api/v1`
*   **Headers**: Add the following header to all authenticated requests:
    ```http
    Authorization: Bearer <jwt_access_token>
    ```

---

## 1. Authentication & Onboarding Flow

### A. Register User (Step 1 - Basic Details)
Register customers, workers, or contractors with contact parameters.
*   **Endpoint**: `POST /auth/register`
*   **Content-Type**: `application/json`
*   **Request Payload**:
    ```json
    {
      "phone_number": "+919999999999",
      "full_name": "Ramesh Kumar",
      "language_preference": "English",
      "role": "plumber" 
    }
    ```
    *Note: `role` can be any root role (`"customer"`, `"worker"`, `"contractor"`) or specific worker sub-role (`"plumber"`, `"electrician"`, `"carpenter"`, `"painter"`, `"mason"`, etc.).*
*   **Response (201 Created)**:
    ```json
    {
      "phone_number": "+919999999999",
      "full_name": "Ramesh Kumar",
      "language_preference": "English",
      "id": 1,
      "is_verified": false,
      "created_at": "2026-08-23T02:00:00Z",
      "roles": [
        {
          "name": "plumber",
          "description": "Plumbing artisan"
        }
      ]
    }
    ```

### B. Send OTP Code (Mocked)
Request a login OTP verification code.
*   **Endpoint**: `POST /auth/login-otp`
*   **Content-Type**: `application/json`
*   **Request Payload**:
    ```json
    {
      "phone_number": "+919999999999"
    }
    ```
*   **Response (200 OK)**:
    ```json
    {
      "message": "OTP verification code successfully sent (mocked)."
    }
    ```
    *Note: In local debug mode (`DEBUG_OTP=True`), the OTP is printed directly in the terminal console output.*

### C. Verify OTP (Obtain Access Token)
Verify the OTP received to retrieve a JWT token.
*   **Endpoint**: `POST /auth/verify-otp`
*   **Content-Type**: `application/json`
*   **Request Payload**:
    ```json
    {
      "phone_number": "+919999999999",
      "otp": "123456"
    }
    ```
    *Note: In debug mode, use the default mock OTP code `"123456"` to bypass.*
*   **Response (200 OK)**:
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "bearer"
    }
    ```

### D. Worker Profile Onboarding & KYC (Step 2 - Required Details)
Collect worker specialties, pricing, coordinates, and photo uploads.
*   **Endpoint**: `POST /worker/kyc`
*   **Content-Type**: `multipart/form-data` (Required due to file uploads)
*   **Headers**: Requires Worker `Bearer <token>`
*   **Multipart Parameters**:
    *   `category`: `Plumber` (text)
    *   `experience_years`: `5` (integer)
    *   `pricing_per_hour`: `150.00` (decimal)
    *   `bio`: `Expert plumbing works, leak repairs` (text)
    *   `location_lat`: `28.6139` (decimal/float)
    *   `location_lng`: `77.2090` (decimal/float)
    *   `aadhaar_number`: `123456789012` (12-digit string)
    *   `profile_picture`: `<selfie_photo_file>`
    *   `aadhaar_image_front`: `<aadhaar_front_file>`
    *   `aadhaar_image_back`: `<aadhaar_back_file>`
*   **Response (200 OK)**:
    ```json
    {
      "id": 1,
      "user_id": 1,
      "category": "Plumber",
      "experience_years": 5,
      "pricing_per_hour": 150.0,
      "bio": "Expert plumbing works, leak repairs",
      "availability_status": false,
      "location_lat": 28.6139,
      "location_lng": 77.2090,
      "profile_picture": "/uploads/kyc/worker_1_selfie.jpg",
      "aadhaar_number": "123456789012",
      "aadhaar_image_front": "/uploads/kyc/worker_1_aadhaar_front.jpg",
      "aadhaar_image_back": "/uploads/kyc/worker_1_aadhaar_back.jpg",
      "kyc_status": "pending",
      "rejection_reason": null,
      "rating": 0.0,
      "total_jobs_done": 0
    }
    ```

### E. Contractor Profile Onboarding & KYC (Step 2 - Required Details)
Collect contractor company licenses and profile details.
*   **Endpoint**: `POST /contractor/kyc`
*   **Content-Type**: `multipart/form-data`
*   **Headers**: Requires Contractor `Bearer <token>`
*   **Multipart Parameters**:
    *   `company_name`: `Apex Civil Builders` (text)
    *   `gst_number`: `07AAAAA1111A1Z1` (15-character string)
    *   `pan_number`: `ABCDE1234F` (10-character string)
    *   `profile_picture`: `<company_logo_file>`
    *   `business_license`: `<license_photo_file>`
*   **Response (200 OK)**:
    ```json
    {
      "id": 1,
      "user_id": 2,
      "company_name": "Apex Civil Builders",
      "gst_number": "07AAAAA1111A1Z1",
      "pan_number": "ABCDE1234F",
      "profile_picture": "/uploads/kyc/contractor_2_logo.png",
      "business_license": "/uploads/kyc/contractor_2_license.png",
      "kyc_status": "pending",
      "rejection_reason": null
    }
    ```

---

## 2. Customer Flows

### A. Find Nearby Workers
Search for online workers based on location coordinates.
*   **Endpoint**: `GET /workers/nearby?lat=28.6140&lng=77.2095&category=Plumber&radius_km=10.0`
*   **Headers**: Requires Customer `Bearer <token>`
*   **Response (200 OK)**:
    ```json
    [
      {
        "id": 1,
        "user_id": 1,
        "category": "Plumber",
        "experience_years": 5,
        "pricing_per_hour": 150.0,
        "bio": "Expert plumbing works, leak repairs",
        "availability_status": true,
        "location_lat": 28.6139,
        "location_lng": 77.2090,
        "profile_picture": "/uploads/kyc/worker_1_selfie.jpg",
        "rating": 4.5,
        "total_jobs_done": 12,
        "distance_km": 0.05,
        "user": {
          "phone_number": "+918888888888",
          "full_name": "Satish Prasad",
          "language_preference": "English",
          "id": 1,
          "is_verified": true,
          "created_at": "2026-08-23T02:00:00Z"
        }
      }
    ]
    ```

### B. Create Job Booking
Book a service category with a worker. Generates the completion verification OTP.
*   **Endpoint**: `POST /bookings/create`
*   **Content-Type**: `application/json`
*   **Headers**: Requires Customer `Bearer <token>`
*   **Request Payload**:
    ```json
    {
      "worker_id": 1,
      "service_id": 1,
      "booking_date": "2026-08-24",
      "preferred_time": "11:00 AM",
      "address": "Connaught Place, New Delhi"
    }
    ```
*   **Response (201 Created)**:
    ```json
    {
      "id": 1,
      "customer_id": 3,
      "worker_id": 1,
      "service_id": 1,
      "booking_date": "2026-08-24",
      "preferred_time": "11:00 AM",
      "address": "Connaught Place, New Delhi",
      "status": "pending",
      "total_amount": null,
      "otp_verification": "433671"
    }
    ```
    *Note: Show the `otp_verification` code to the customer. They must share this with the worker only when the job is successfully done.*

### C. Booking History
Get previous bookings.
*   **Endpoint**: `GET /bookings/my-history?skip=0&limit=100`
*   **Headers**: Requires Customer `Bearer <token>`
*   **Response (200 OK)**:
    ```json
    [
      {
        "id": 1,
        "customer_id": 3,
        "worker_id": 1,
        "service_id": 1,
        "booking_date": "2026-08-24",
        "preferred_time": "11:00 AM",
        "address": "Connaught Place, New Delhi",
        "status": "completed",
        "total_amount": 150.00,
        "otp_verification": "433671",
        "customer": { "id": 3, "full_name": "Ramesh Kumar" },
        "worker": { "id": 1, "category": "Plumber" },
        "service": { "id": 1, "name": "Plumber" },
        "work_proofs": [
          { "id": 1, "image_url": "/uploads/work_proofs/booking_1_proof.jpg", "uploaded_at": "2026-08-23T02:10:00Z" }
        ]
      }
    ]
    ```

---

## 3. Worker Flows

### A. Worker Dashboard Stats
Fetch metrics for dashboard displaying earnings and jobs.
*   **Endpoint**: `GET /worker/dashboard`
*   **Headers**: Requires Worker `Bearer <token>`
*   **Response (200 OK)**:
    ```json
    {
      "earnings": 150.0,
      "jobs_completed": 1,
      "pending_requests": 0,
      "availability_status": true
    }
    ```

### B. Toggle Availability Status
Turn Online/Offline status to join the nearby search list.
*   **Endpoint**: `PATCH /worker/status`
*   **Content-Type**: `application/json`
*   **Headers**: Requires Worker `Bearer <token>`
*   **Request Payload**:
    ```json
    {
      "availability_status": true
    }
    ```
*   **Response (200 OK)**: Returns the updated Worker Profile.

### C. Respond to Booking Request
Accept or reject pending jobs.
*   **Endpoint**: `POST /bookings/{id}/respond`
*   **Content-Type**: `application/json`
*   **Headers**: Requires Worker `Bearer <token>`
*   **Request Payload**:
    ```json
    {
      "status": "accepted" 
    }
    ```
    *Note: `status` must be `"accepted"` or `"rejected"`.*
*   **Response (200 OK)**: Returns updated Booking.

### D. Complete Booking (Verify OTP, Finalize Wallet ledger, Upload work proof)
Finalize invoice, verify customer OTP, and upload photo proof.
*   **Endpoint**: `POST /bookings/{id}/complete`
*   **Content-Type**: `multipart/form-data`
*   **Headers**: Requires Worker `Bearer <token>`
*   **Multipart Parameters**:
    *   `total_amount`: `150.00` (decimal)
    *   `otp`: `433671` (Customer-provided 6-digit OTP string)
    *   `file`: `<photo_of_work_proof>` (Optional file)
*   **Response (200 OK)**:
    ```json
    {
      "id": 1,
      "customer_id": 3,
      "worker_id": 1,
      "service_id": 1,
      "booking_date": "2026-08-24",
      "preferred_time": "11:00 AM",
      "address": "Connaught Place, New Delhi",
      "status": "completed",
      "total_amount": 150.0,
      "otp_verification": "433671"
    }
    ```
    *Note: On completion, funds of `total_amount` are automatically subtracted from the customer's wallet and added to the worker's wallet in the database.*
