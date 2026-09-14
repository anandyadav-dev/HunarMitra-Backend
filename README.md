# Mazdoor Backend (FastAPI & SQLAlchemy/MySQL)

A production-grade Python FastAPI backend using SQLAlchemy and MySQL for the **Mazdoor** two-sided marketplace (connecting Customers and Artisans).

## Features
- **OTP-based Authentication**: Simulated OTP registration/login with in-memory caching and token generation (JWT).
- **Location-based Search**: High-performance worker lookups using a bounding box database query followed by Python Haversine sorting.
- **Job Lifecycle**: Complete state machine mapping bookings from pending, accepted/rejected, to complete.
- **Verification OTP**: Random 6-digit verification code generated at booking creation to verify task completion.
- **Wallet & Balances**: Automated payment/wallet ledger transfers from customer to worker upon OTP-verified job completion.
- **Static File Proof Uploads**: Worker work-proof photos uploaded dynamically and served statically.

---

## Directory Structure
```
mazdoor/
├── app/
│   ├── api/
│   │   ├── deps.py           # Database & JWT verification dependencies
│   │   └── v1/
│   │       ├── api.py         # Merges routers into v1 API
│   │       └── endpoints/
│   │           ├── auth.py    # OTP login & JWT auth APIs
│   │           ├── customer.py# Nearby worker searches, bookings history
│   │           └── worker.py  # Worker dashboard metrics, respond, complete
│   ├── core/
│   │   ├── config.py         # Config validation using pydantic-settings
│   │   ├── database.py       # SQLAlchemy MySQL connection pool
│   │   └── security.py       # JWT utility helpers
│   ├── crud/                 # Database helpers (CRUD encapsulation)
│   │   ├── base.py
│   │   ├── crud_user.py
│   │   ├── crud_worker.py
│   │   └── crud_booking.py
│   ├── models/               # SQLAlchemy Models
│   │   ├── base_class.py
│   │   ├── user.py
│   │   ├── worker.py
│   │   ├── service.py
│   │   ├── booking.py
│   │   ├── wallet.py
│   │   └── work_proof.py
│   ├── schemas/              # Pydantic schemas (validations & responses)
│   │   ├── token.py
│   │   ├── user.py
│   │   ├── worker.py
│   │   ├── service.py
│   │   ├── booking.py
│   │   ├── wallet.py
│   │   └── work_proof.py
│   └── services/             # Business Logic (OTP mock cache)
│       └── otp.py
├── uploads/                  # Upload directory for work proof images
├── .env.example
├── .env
├── requirements.txt
└── README.md
```

---

## Local Development Setup

### 1. Requirements
Ensure you have Python 3.10+ and a MySQL database server running.

### 2. Configure Environment
Create a copy of `.env.example` as `.env` and adjust the parameters (default configuration maps to local MySQL on standard port):
```bash
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/mazdoor
JWT_SECRET_KEY=mazdoor-secret-key-321-prod-grade-app
ACCESS_TOKEN_EXPIRE_MINUTES=11520
OTP_EXPIRE_MINUTES=5
DEBUG_OTP=True
```

### 3. Installation & Run
1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

The application will be accessible at `http://127.0.0.1:8000`. Swagger documentation is available at `http://127.0.0.1:8000/docs`.

---

## API Testing Reference (Debug Mode)

When `DEBUG_OTP=True` is enabled in your `.env` file:
1. **Mock OTP**: Use `'123456'` as the verification code for `/auth/verify-otp` endpoints or when completing bookings.
2. **Console Output**: Generated OTP codes are printed directly to the terminal stdout for testing.
3. **Database Pre-Seed**: Automatically inserts four default services (`Plumber`, `Electrician`, `Carpenter`, `Painter`) on the first database run to facilitate instant endpoint usage.
