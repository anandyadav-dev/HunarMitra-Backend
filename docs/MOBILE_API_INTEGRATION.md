# HunarMitra Complete Mobile API Integration Guide (v2.0)

This is the **official, definitive, end-to-end integration manual** for mobile app developers (Flutter / React Native / Kotlin / Swift) building the HunarMitra apps for Customers, Workers, and Contractors.

---

## Table of Contents
1. [Architecture & Server URLs](#1-architecture--server-urls)
2. [Authentication Flow & User Profile (`/auth/me`)](#2-authentication-flow--user-profile-authme)
3. [First-Time Customer Signup Reward (50 Welcome Coins)](#3-first-time-customer-signup-reward-50-welcome-coins)
4. [Wallet Balances & Coin Economy (`/wallet`)](#4-wallet-balances--coin-economy-wallet)
5. [Worker Search, Categories & Public Profiles](#5-worker-search-categories--public-profiles)
6. [Worker Contact Reveal & Phone Privacy (5 Free Reveals, 10 Coins)](#6-worker-contact-reveal--phone-privacy)
7. [Dynamic Coin Packs & In-App Purchases (Razorpay / Cashfree)](#7-dynamic-coin-packs--in-app-purchases)
8. [Worker Reviews, Star Ratings & Photo Proof Uploads](#8-worker-reviews-star-ratings--photo-proof-uploads)
9. [Worker & Contractor Operations](#9-worker--contractor-operations)
10. [Booking & Call History](#10-booking--call-history)
11. [Dynamic System Configuration (`/config/coins`)](#11-dynamic-system-configuration-configcoins)
12. [Mobile Integration Checklist](#12-mobile-integration-checklist)

---

## 1. Architecture & Server URLs

The mobile apps communicate directly with the HunarMitra FastAPI backend over HTTPS using standard JSON payloads and Bearer JWT tokens.

```
Mobile App (Flutter / React Native / Native)
     │
     ▼ (HTTPS + Bearer JWT)
FastAPI Backend (Port 8000)
     │
     ├── Dynamic Business Rules & Configs (system_configs)
     ├── Wallet & Append-Only Coin Ledger (wallets, coin_ledger)
     ├── Contact Reveals & Phone Privacy (engagements)
     ├── Dynamic Coin Packs & Orders (coin_packs, payment_orders)
     └── Worker Reviews & Photo Proofs (feedbacks, feedback_photos)
```

### Server Environments
- **Production URL:** `http://18.142.114.233:8000` (or your domain `https://api.hunarmitra.com`)
- **Android Emulator Local:** `http://10.0.2.2:8000`
- **iOS Simulator / Local Device:** `http://<YOUR_LOCAL_IP>:8000`
- **Interactive Swagger Docs:** `http://18.142.114.233:8000/docs`

> **API Prefix Support:** All endpoints support both `/api/v1/<endpoint>` and direct root `/<endpoint>` (e.g. `/api/v1/auth/me` and `/auth/me`).

---

## 2. Authentication Flow & User Profile (`/auth/me`)

Authentication is OTP-based using mobile phone numbers with country code (e.g., `+919876543210`).

```
Mobile App                  Backend
    │                          │
    ├── 1. Request OTP ───────▶│ POST /api/v1/auth/login-otp
    │                          │
    ├── 2. Verify OTP ────────▶│ POST /api/v1/auth/verify-otp
    │◀── Returns JWT Token ────┤
    │                          │
    ├── 3. Get Profile+Coins ─▶│ GET /api/v1/auth/me (Authorization: Bearer <token>)
    │◀── Profile + Wallet ─────┤
```

### 2.1 User Registration
- **Method:** `POST /api/v1/auth/register` (or `/auth/register`)
- **Auth:** None
- **Request Body:**
```json
{
  "phone_number": "+919876543210",
  "full_name": "Ramesh Kumar",
  "language_preference": "Hindi",
  "city": "Lucknow",
  "role": "customer" 
}
```
*Note: `role` can be `"customer"`, `"worker"`, or `"contractor"`.*
- **Response `201 Created`:**
```json
{
  "id": "74c6e653-e355-4c2d-a1ca-ccb2ccd63c2b",
  "phone_number": "+919876543210",
  "full_name": "Ramesh Kumar",
  "language_preference": "Hindi",
  "city": "Lucknow",
  "is_verified": false,
  "created_at": "2026-10-22T05:41:16",
  "roles": [{ "name": "customer" }]
}
```

### 2.2 Request Login OTP
- **Method:** `POST /api/v1/auth/login-otp`
- **Request Body:**
```json
{
  "phone_number": "+919876543210"
}
```
- **Response `200 OK`:**
```json
{
  "message": "OTP verification code successfully sent (mocked)."
}
```

### 2.3 Verify OTP & Get Token
- **Method:** `POST /api/v1/auth/verify-otp`
- **Request Body:**
```json
{
  "phone_number": "+919876543210",
  "otp": "1234"
}
```
*Note: Sandbox test OTP is `1234` or `123456`.*
- **Response `200 OK`:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
  "token_type": "bearer"
}
```

### 2.4 Get Current User Profile & Coins (`GET /auth/me`)
**Use this single API on app launch, splash screen, or profile screen.** It returns user details AND current wallet coin balances in one call.
- **Method:** `GET /api/v1/auth/me` (or `GET /auth/me`)
- **Headers:** `Authorization: Bearer <access_token>`
- **Response `200 OK`:**
```json
{
  "id": "74c6e653-e355-4c2d-a1ca-ccb2ccd63c2b",
  "phone_number": "+919876543210",
  "full_name": "Ramesh Kumar",
  "language_preference": "Hindi",
  "city": "Lucknow",
  "location_lat": 26.8467,
  "location_lng": 80.9462,
  "is_verified": true,
  "created_at": "2026-10-22T05:41:16",
  "roles": ["customer"],
  "wallet": {
    "purchased_coins": 0,
    "earned_coins": 50,
    "total_coins": 50,
    "balance": "0.00"
  },
  "worker_profile_id": null,
  "contractor_profile_id": null
}
```

---

## 3. First-Time Customer Signup Reward (50 Welcome Coins)

When a customer registers on HunarMitra for the first time, the backend automatically awards **50 promotional earned coins** into their wallet.

### Rules & Flow:
1. Customer registers via `POST /api/v1/auth/register` with role `"customer"`.
2. Backend creates wallet with:
   - `purchased_coins: 0`
   - `earned_coins: 50`
   - `total_coins: 50`
3. A ledger entry is permanently recorded:
   - `transaction_type`: `"SIGNUP_BONUS"`
   - `coin_type`: `"earned"`
   - `amount`: `50`
   - `description`: `"Signup Bonus"`
4. **Idempotency Guarantee:** Reward is credited strictly once per customer.
5. **Mobile Action:** After signup/login, call `GET /auth/me` or `GET /wallet` and show a welcome banner:
   > *"Welcome to HunarMitra! You received 50 free coins to contact skilled workers!"*

---

## 4. Wallet Balances & Coin Economy (`/wallet`)

HunarMitra manages two separate coin categories:
- **`purchased_coins`**: Coins bought via online payment packs (e.g. ₹10, ₹25, ₹50, ₹100).
- **`earned_coins`**: Promotional coins received as signup bonus (50 coins), review rewards (5 coins), or referrals.
- **`total_coins`**: Total spendable coins (`purchased_coins + earned_coins`).

### 4.1 Get Wallet Balance & Recent Ledger
- **Endpoint:** `GET /api/v1/wallet` (or `GET /wallet`)
- **Headers:** `Authorization: Bearer <access_token>`
- **Response `200 OK`:**
```json
{
  "id": "116a5b92-cf0e-4ad4-8509-3263dcb15091",
  "user_id": "74c6e653-e355-4c2d-a1ca-ccb2ccd63c2b",
  "balance": "0.00",
  "purchased_coins": 30,
  "earned_coins": 50,
  "total_coins": 80,
  "recent_transactions": [
    {
      "id": "7b0d2d31-419b-449e-ba78-2d579b1df639",
      "wallet_id": "116a5b92-cf0e-4ad4-8509-3263dcb15091",
      "amount": 50,
      "transaction_type": "SIGNUP_BONUS",
      "coin_type": "earned",
      "description": "Signup Bonus",
      "balance_after": 50,
      "reference_id": null,
      "created_at": "2026-10-22T05:41:16"
    }
  ]
}
```

### 4.2 Get Paginated Coin Ledger History
- **Endpoint:** `GET /api/v1/wallet/transactions?skip=0&limit=20`
- **Headers:** `Authorization: Bearer <access_token>`
- **Response `200 OK`:**
```json
{
  "total": 1,
  "items": [
    {
      "id": "7b0d2d31-419b-449e-ba78-2d579b1df639",
      "amount": -10,
      "transaction_type": "WORKER_REVEAL",
      "coin_type": "purchased",
      "description": "Unlocked contact for Ramesh (Plumber)",
      "balance_after": 70,
      "created_at": "2026-10-22T06:10:00"
    }
  ]
}
```

---

## 5. Worker Search, Categories & Public Profiles

### Privacy Rule:
Worker phone numbers are **NEVER returned** by worker list, search, or profile APIs. The phone number field is `null` until unlocked via the Reveal API.

### 5.1 Public Service Categories
- **Endpoint:** `GET /api/v1/public/categories`
- **Auth:** None
- **Response `200 OK`:**
```json
[
  { "id": "uuid", "name": "Plumber", "slug": "plumber", "description": "Pipe fixing, taps, leaks" },
  { "id": "uuid", "name": "Electrician", "slug": "electrician", "description": "Wiring, switches, repair" }
]
```

### 5.2 Search & Filter Workers
- **Endpoint:** `GET /api/v1/workers?category=Plumber&city=Lucknow&search=Ramesh&skip=0&limit=20`
- **Headers:** `Authorization: Bearer <access_token>`
- **Response `200 OK`:**
```json
[
  {
    "id": "e6a2b53c-1b60-4963-88bc-4670c73919e1",
    "user_id": "a1b2c3d4-...",
    "full_name": "Ramesh Kumar",
    "phone_number": null, 
    "category": "Plumber",
    "experience_years": 5,
    "pricing_per_hour": 150.0,
    "bio": "Experienced plumber with 5 years in residential plumbing.",
    "rating": 4.8,
    "total_jobs_done": 42,
    "city": "Lucknow",
    "availability_status": "available",
    "kyc_status": "verified"
  }
]
```

### 5.3 Nearby Online Workers (GPS Radius)
- **Endpoint:** `GET /api/v1/workers/nearby?lat=26.8467&lng=80.9462&radius_km=15&category=Plumber`
- **Headers:** `Authorization: Bearer <access_token>`

### 5.4 Worker Profile Details
- **Endpoint:** `GET /api/v1/workers/{worker_id}`
- **Headers:** `Authorization: Bearer <access_token>`

---

## 6. Worker Contact Reveal & Phone Privacy

Customers can call or reveal a worker's phone number according to these business rules:
1. **5 Free Reveals:** Every customer gets **5 free unique worker contact unlocks**.
2. **10 Coins per Reveal:** After 5 free contacts are exhausted, each new contact reveal costs **10 coins**.
3. **Repeated Reveals are Free:** Once unlocked, contacting the same worker again is **always free forever**.
4. **Coin Priority:** Purchased coins are deducted first; if depleted, earned promotional coins are deducted.

### 6.1 Check Contact Status & Cost Before Reveal
Call this before displaying the "Call / Reveal Phone" button in the worker detail view:
- **Endpoint:** `GET /api/v1/workers/{worker_id}/contact-status`
- **Headers:** `Authorization: Bearer <access_token>`
- **Response `200 OK`:**
```json
{
  "worker_id": "e6a2b53c-1b60-4963-88bc-4670c73919e1",
  "is_revealed": false,
  "revealed_phone_number": null,
  "free_reveals_remaining": 3,
  "coins_required": 0,
  "wallet_balance_coins": 50,
  "can_reveal": true
}
```

#### UI Decision Logic for Mobile Dev:
- If `is_revealed == true`:
  - Show the unlocked phone number directly with a direct "Call Now" button.
- If `free_reveals_remaining > 0`:
  - Button text: `"Reveal Contact (Free - X left)"`
  - Cost: 0 coins.
- If `free_reveals_remaining == 0`:
  - Button text: `"Unlock Contact (10 Coins)"`
  - If `wallet_balance_coins < 10`:
    - Open "Buy Coins" modal / Coin Packs screen.
  - Else:
    - Prompt confirmation: *"Unlock this worker's contact for 10 coins?"*

### 6.2 Unlock Worker Contact Phone
- **Endpoint:** `POST /api/v1/workers/{worker_id}/reveal`
- **Headers:** `Authorization: Bearer <access_token>`
- **Response `200 OK`:**
```json
{
  "worker_id": "e6a2b53c-1b60-4963-88bc-4670c73919e1",
  "phone_number": "+919876500001",
  "was_free": true,
  "coins_deducted": 0,
  "free_reveals_remaining": 2,
  "remaining_coins": 50,
  "revealed_at": "2026-10-22T06:15:00"
}
```
- **Error `402 Payment Required` (Insufficient Coins):**
```json
{
  "detail": "Insufficient coins to reveal contact. You need 10 coins. Current balance: 4 coins."
}
```

---

## 7. Dynamic Coin Packs & In-App Purchases

Coin pack prices and quantities are **managed dynamically by Admins** from the Admin Dashboard. Mobile apps must NEVER hardcode prices or coin amounts.

### 7.1 Fetch Available Coin Packs
- **Endpoint:** `GET /api/v1/coin-packs`
- **Headers:** `Authorization: Bearer <access_token>`
- **Response `200 OK`:**
```json
[
  { "id": "pack_1", "coins": 10, "price": "10.00", "currency": "INR", "is_active": true, "badge": null },
  { "id": "pack_2", "coins": 30, "price": "25.00", "currency": "INR", "is_active": true, "badge": "Popular" },
  { "id": "pack_3", "coins": 70, "price": "50.00", "currency": "INR", "is_active": true, "badge": "Best Value" },
  { "id": "pack_4", "coins": 150, "price": "100.00", "currency": "INR", "is_active": true, "badge": "Super Saver" }
]
```

### 7.2 Initiate Pack Purchase (Create Order)
- **Endpoint:** `POST /api/v1/coin-packs/purchase`
- **Headers:** `Authorization: Bearer <access_token>`
- **Request Body:**
```json
{
  "coin_pack_id": "pack_2"
}
```
- **Response `201 Created`:**
```json
{
  "order_id": "0d99a463-55be-4ba5-a8ca-9c60e3f284b3",
  "provider_order_id": "order_RZP123456789",
  "provider": "razorpay",
  "amount": "25.00",
  "currency": "INR",
  "coins": 30,
  "status": "pending",
  "key_id": "rzp_test_placeholder_key"
}
```

### 7.3 Complete Payment (SDK) & Server Verification
Open Razorpay / Cashfree checkout in the mobile app with `provider_order_id`, `amount`, and `key_id`. Upon success:
- **Endpoint:** `POST /api/v1/payments/verify`
- **Headers:** `Authorization: Bearer <access_token>`
- **Request Body:**
```json
{
  "order_id": "0d99a463-55be-4ba5-a8ca-9c60e3f284b3",
  "payment_id": "pay_RZP987654321",
  "signature": "razorpay_signature_hash_string"
}
```
- **Response `200 OK`:**
```json
{
  "status": "success",
  "order_id": "0d99a463-55be-4ba5-a8ca-9c60e3f284b3",
  "coins_credited": 30,
  "new_balance_coins": 80,
  "message": "Payment verified successfully and 30 coins credited to your wallet."
}
```

### 7.4 Poll Order Status
- **Endpoint:** `GET /api/v1/payments/status/{order_id}`
- **Headers:** `Authorization: Bearer <access_token>`

---

## 8. Worker Reviews, Star Ratings & Photo Proof Uploads

Customers can rate workers (1-5 stars), leave feedback, and upload job completion photos. Submitting a review awards **5 bonus earned coins** to the customer!

### 8.1 Submit Review (with optional photos)
- **Endpoint:** `POST /api/v1/workers/{worker_id}/reviews`
- **Headers:** `Authorization: Bearer <access_token>`
- **Content-Type:** `multipart/form-data`
- **Form Fields:**
  - `rating` (int, required, 1-5): Rating in stars.
  - `comment` (string, optional): Review text.
  - `photos` (file array, optional): Up to 3 JPEG/PNG photos of the work done.
- **Response `201 Created`:**
```json
{
  "id": "rev_uuid",
  "worker_id": "e6a2b53c-1b60-4963-88bc-4670c73919e1",
  "rating": 5,
  "comment": "Superb piping work, fixed quickly!",
  "reward_coins_earned": 5,
  "photos": [
    { "id": "photo_1", "photo_url": "http://18.142.114.233:8000/uploads/work_proofs/photo_1.jpg" }
  ],
  "created_at": "2026-10-22T07:00:00"
}
```

### 8.2 Get Worker Reviews
- **Endpoint:** `GET /api/v1/workers/{worker_id}/reviews?skip=0&limit=20`
- **Auth:** None (Public)
- **Response `200 OK`:**
```json
{
  "total": 12,
  "average_rating": 4.8,
  "items": [
    {
      "id": "rev_uuid",
      "user_name": "Ramesh K.",
      "rating": 5,
      "comment": "Superb piping work!",
      "photos": ["http://18.142.114.233:8000/uploads/work_proofs/photo_1.jpg"],
      "created_at": "2026-10-22T07:00:00"
    }
  ]
}
```

---

## 9. Worker & Contractor Operations

### 9.1 Worker Dashboard
- **Endpoint:** `GET /api/v1/worker/dashboard`
- **Headers:** `Authorization: Bearer <worker_token>`
- **Response `200 OK`:**
```json
{
  "jobs_completed": 15,
  "pending_requests": 2,
  "total_earnings": 4500.0,
  "rating": 4.8,
  "total_reviews": 12
}
```

### 9.2 Worker Availability Status Update
- **Endpoint:** `PUT /api/v1/worker/status`
- **Headers:** `Authorization: Bearer <worker_token>`
- **Request Body:**
```json
{
  "is_available": true,
  "lat": 26.8467,
  "lng": 80.9462
}
```

### 9.3 Worker KYC Verification
- **Endpoint:** `POST /api/v1/worker/kyc`
- **Headers:** `Authorization: Bearer <worker_token>`
- **Content-Type:** `multipart/form-data`
- **Fields:** `id_proof_type`, `id_proof_number`, `document_file`

### 9.4 Contractor KYC Verification
- **Endpoint:** `POST /api/v1/contractor/kyc`
- **Headers:** `Authorization: Bearer <contractor_token>`
- **Request Body:**
```json
{
  "company_name": "Apex Builders",
  "gst_number": "09AAAAA0000A1Z5",
  "pan_number": "ABCDE1234F"
}
```

---

## 10. Booking & Call History

### 10.1 Create Booking / Record Call
- **Endpoint:** `POST /api/v1/bookings/create`
- **Headers:** `Authorization: Bearer <access_token>`
- **Request Body:**
```json
{
  "worker_id": "e6a2b53c-1b60-4963-88bc-4670c73919e1",
  "service_id": "srv_uuid",
  "booking_date": "2026-10-23",
  "preferred_time": "10:00 AM",
  "job_description": "Fix bathroom leakage"
}
```

### 10.2 Customer Call / Booking History
- **Endpoint:** `GET /api/v1/bookings/my-history`
- **Headers:** `Authorization: Bearer <access_token>`

---

## 11. Dynamic System Configuration (`/config/coins`)

The app can query dynamic parameters set by the backend admin at runtime:
- **Endpoint:** `GET /api/v1/config/coins` (or `GET /config/coins`)
- **Auth:** None
- **Response `200 OK`:**
```json
{
  "free_reveals_limit": 5,
  "coins_per_reveal": 10,
  "signup_bonus_coins": 50,
  "signup_bonus_enabled": true,
  "review_reward_coins": 5,
  "payment_provider": "razorpay",
  "min_wallet_balance_warning": 10
}
```

---

## 12. Mobile Integration Checklist

| Feature | Endpoint | Method | Status |
|---|---|---|---|
| **User Registration** | `/api/v1/auth/register` | `POST` | ✅ Implemented |
| **Request Login OTP** | `/api/v1/auth/login-otp` | `POST` | ✅ Implemented |
| **Verify OTP (JWT Token)** | `/api/v1/auth/verify-otp` | `POST` | ✅ Implemented |
| **Get Profile + Coins in 1 Call** | `/api/v1/auth/me` | `GET` | ✅ Implemented |
| **50 Coins Welcome Reward** | Auto-credited on customer signup | — | ✅ Implemented |
| **Get Wallet & Coin Balances** | `/api/v1/wallet` | `GET` | ✅ Implemented |
| **Coin Ledger History** | `/api/v1/wallet/transactions` | `GET` | ✅ Implemented |
| **Service Categories** | `/api/v1/public/categories` | `GET` | ✅ Implemented |
| **Search & Filter Workers** | `/api/v1/workers` | `GET` | ✅ Implemented (Phone hidden) |
| **Nearby GPS Workers** | `/api/v1/workers/nearby` | `GET` | ✅ Implemented (Phone hidden) |
| **Worker Profile Details** | `/api/v1/workers/{id}` | `GET` | ✅ Implemented (Phone hidden) |
| **Check Contact Status & Cost** | `/api/v1/workers/{id}/contact-status`| `GET` | ✅ Implemented |
| **Reveal Worker Contact Phone**| `/api/v1/workers/{id}/reveal` | `POST` | ✅ Implemented (5 free, then 10 coins) |
| **Fetch Dynamic Coin Packs** | `/api/v1/coin-packs` | `GET` | ✅ Implemented |
| **Create Payment Order** | `/api/v1/coin-packs/purchase` | `POST` | ✅ Implemented |
| **Verify Payment & Credit Coins**| `/api/v1/payments/verify` | `POST` | ✅ Implemented |
| **Poll Payment Order Status** | `/api/v1/payments/status/{id}` | `GET` | ✅ Implemented |
| **Submit Review & Star Rating**| `/api/v1/workers/{id}/reviews` | `POST` | ✅ Implemented (+5 reward coins) |
| **View Worker Reviews** | `/api/v1/workers/{id}/reviews` | `GET` | ✅ Implemented |
| **Worker Dashboard Stats** | `/api/v1/worker/dashboard` | `GET` | ✅ Implemented |
| **Worker Availability Status** | `/api/v1/worker/status` | `PUT` | ✅ Implemented |
| **Worker KYC Verification** | `/api/v1/worker/kyc` | `POST` | ✅ Implemented |
| **Contractor KYC** | `/api/v1/contractor/kyc` | `POST` | ✅ Implemented |
| **Create Booking / Call** | `/api/v1/bookings/create` | `POST` | ✅ Implemented |
| **Booking / Call History** | `/api/v1/bookings/my-history` | `GET` | ✅ Implemented |
| **Dynamic Coin Config** | `/api/v1/config/coins` | `GET` | ✅ Implemented |
