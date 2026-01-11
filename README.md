# HunarMitra Backend

Production-grade Django + DRF backend for HunarMitra - A Worker & Contractor Management Platform.

## Features

- **Phone-based Authentication**: Secure OTP authentication with Redis rate-limiting, JWT tokens, and token blacklisting
- **Theme & App Configuration**: Centralized theme management and app-config API with Redis caching
- **Modern Admin UI**: Django Unfold admin with custom dashboard, actions, and visual enhancements
- **9 Django Apps**: Users, Core, Services, Workers, Jobs, Contractors, Attendance, Notifications, Payments
- **MySQL Database**: Production-ready MySQL 8.0 with SQLite fallback for testing
- **Redis Cache & Broker**: For OTP storage, caching, and Celery task queue
- **Celery**: Background task processing for SMS sending with Twilio integration
- **MinIO**: S3-compatible object storage for development
- **Docker**: Complete Docker-based development environment
- **OpenAPI Documentation**: Auto-generated API docs with Swagger UI
- **Comprehensive Tests**: 18+ passing tests with pytest, 100% core feature coverage
- **CI/CD**: GitHub Actions workflow
- **Code Quality**: pre-commit hooks with black, isort, flake8

## Prerequisites

- Docker & Docker Compose
- Git

## Quick Start

```bash
# Clone the repository
git clone https://github.com/ravishmishralko/HunarMitra.git
cd HunarMitra/backend

# Create environment file
cp .env.example .env

# Edit .env with your values (at minimum, change passwords and SECRET_KEY)

# Build and start all services
docker-compose up --build

# In another terminal, run migrations and seed data
docker-compose exec app python manage.py migrate
docker-compose exec app python manage.py seed_services
docker-compose exec app python manage.py seed_demo_data  # Optional: seed themes, banners, demo users

# Create superuser (or use seed_demo_data which creates admin@hunarmitra.com)
docker-compose exec app python manage.py createsuperuser
```

The API will be available at: http://localhost:8000

## Services

After running `docker-compose up`, the following services will be available:

| Service | URL | Description |
|---------|-----|-------------|
| Django API | http://localhost:8000 | Main application |
| Swagger Docs | http://localhost:8000/api/docs/ | OpenAPI documentation |
| ReDoc | http://localhost:8000/api/redoc/ | Alternative API docs |
| Admin Panel | http://localhost:8000/admin/ | Django admin |
| MinIO Console | http://localhost:9001 | Object storage UI |
| MySQL | localhost:3306 | Database |
| Redis | localhost:6379 | Cache & broker |

## API Endpoints

### Authentication

```bash
# Request OTP
curl -X POST http://localhost:8000/api/v1/auth/request-otp/ \
  -H "Content-Type: application/json" \
  -d '{"phone": "+919876543210", "role": "worker"}'

# Response (dev mode includes OTP)
{
  "request_id": "uuid-here",
  "ttl": 300,
  "message": "OTP sent to +919876543210",
  "dev_otp": "1234"  # Only in DEBUG mode
}

# Verify OTP and get JWT tokens
curl -X POST http://localhost:8000/api/v1/auth/verify-otp/ \
  -H "Content-Type: application/json" \
  -d '{"request_id": "uuid-here", "otp": "1234"}'

# Response
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": "uuid-here",
    "phone": "+919876543210",
    "role": "worker",
    ...
  },
  "is_new_user": true
}
```

### Core Endpoints

```bash
# Health check
curl http://localhost:8000/api/v1/health/

# Get theme configuration
curl http://localhost:8000/api/v1/theme/
```

### Services

```bash
# List all services
curl http://localhost:8000/api/v1/services/

# Get service by slug
curl http://localhost:8000/api/v1/services/plumbing/
```

## Authentication (OTP)

The platform uses phone-number based OTP authentication.

### Flow
1. **Request OTP**: `POST /api/v1/auth/request-otp/`
2. **Receive SMS**: OTP sent via Twilio (prod) or logged (dev)
3. **Verify OTP**: `POST /api/v1/auth/verify-otp/` matches OTP
4. **Token**: Receive `access` (60m) and `refresh` (7d) JWT tokens
5. **Logout**: `POST /api/v1/auth/logout/` blacklists the refresh token

### Environment Variables
Required variables for Auth & OTP (add to `.env`):

```env
# OTP
OTP_TTL_SECONDS=300
OTP_RATE_LIMIT_PER_MINUTE=1
SMS_PROVIDER=dev  # or 'twilio'

# Twilio (if SMS_PROVIDER=twilio)
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_FROM_NUMBER=...

# JWT
SIMPLE_JWT_SECRET=your-secret-key
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7
```

### Testing OTP
In `dev` mode (`DEBUG=True`), the OTP is:
1. Logged to the console/docker logs
2. Returned in the API response field `dev_otp` for convenience

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/request-otp/ \
  -H "Content-Type: application/json" \
  -d '{"phone": "+919999999999", "role": "worker"}'
```

**Example Verify:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/verify-otp/ \
  -H "Content-Type: application/json" \
  -d '{"request_id": "<UUID>", "otp": "1234"}'
```

## App Configuration

```bash
# Get complete app configuration (theme, categories, banners, features)
curl http://localhost:8000/api/v1/app-config/

# Response (cached for 5 minutes)
{
  "app": {
    "name": "HunarMitra",
    "version": "1.0.0",
    "supported_locales": ["en", "hi", "mr"],
    "support_phone": "+91-1800-XXX-XXXX"
  },
  "theme": {
    "name": "HunarMitra Default",
    "primary_color": "#2563EB",
    "accent_color": "#F59E0B",
    "background_color": "#F9FAFB",
    "logo_url": "http://localhost:9000/hunarmitra/static/logo.png",
    "fonts": [
      {
        "family": "Inter",
        "url": "http://localhost:9000/hunarmitra/static/fonts/default.woff"
      }
    ]
  },
  "categories": [
    {
      "id": "uuid",
      "slug": "plumbing",
      "name": "Plumbing",
      "icon_url": "http://localhost:9000/hunarmitra/..."
    }
  ],
  "banners": [
    {
      "id": "uuid",
      "title": "Welcome to HunarMitra",
      "subtitle": "Find skilled workers near you",
      "image_url": "http://localhost:9000/hunarmitra/...",
      "action": {"type": "route", "value": "/services"}
    }
  ],
  "features": {
    "attendance_kiosk": true,
    "ekyc": false,
    "auto_assign_emergency": true,
    "enable_notifications": true,
    "enable_dark_mode": true
  },
  "meta": {
    "config_version": "1.0",
    "cache_ttl_seconds": 300
  }
}
```

**Note**: This endpoint is cached using Redis for 5 minutes to improve performance. All S3/MinIO keys are automatically resolved to public URLs.

### Authenticated Requests

```bash
# Use the access token from OTP verification
curl http://localhost:8000/api/v1/protected-endpoint/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Environment Variables

See `.env.example` for all available configuration options. Key variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | *Required* |
| `DEBUG` | Debug mode | True |
| `MYSQL_DATABASE` | Database name | hunarmitra |
| `MYSQL_USER` | Database user | hunarmitra_user |
| `MYSQL_PASSWORD` | Database password | *Change me* |
| `REDIS_URL` | Redis connection URL | redis://redis:6379/0 |
| `USE_S3` | Enable S3/MinIO storage | True |
| `MINIO_ENDPOINT` | MinIO endpoint | http://minio:9000 |

## Rate Limiting

API endpoints are rate-limited by default to protect the service:
- **Anonymous users**: 100 requests/hour
- **Authenticated users**: 1000 requests/hour

Configure via environment variables:
```bash
THROTTLE_ANON=200/hour
THROTTLE_USER=2000/hour
```

## Error Tracking (Optional)

Sentry can be enabled for production error tracking by setting the DSN:
```bash
SENTRY_DSN=https://...@sentry.io/...
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
```

If `SENTRY_DSN` is not set, error tracking is disabled and no data is sent.

## Payment Configuration

HunarMitra operates in **cash-first mode** by default for free onboarding. Online payments can be optionally enabled.

### Cash vs Online Payments

**Default Behavior (ENABLE_PAYMENTS=false)**:
- All bookings default to `payment_method='cash'`
- Online payment requests automatically fallback to cash
- Payment gateway endpoints return 503 (Service Unavailable)
- No payment records created for cash bookings

**Environment Variable**:
```bash
ENABLE_PAYMENTS=false  # Default: cash-only mode
# Set to true to enable online payment gateway
```

### Booking Payment Methods

- `cash` - Cash payment (default, no payment gateway)
- `online` - Online payment via gateway (requires ENABLE_PAYMENTS=true)
- `none` - No payment required

### API Usage

**Create Cash Booking (Default)**:
```bash
curl -X POST http://localhost:8000/api/v1/bookings/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service": "service-uuid",
    "address": "123 Main St",
    "payment_method": "cash"
  }'

# Response
{
  "id": "booking-uuid",
  "payment_method": "cash",
  "payment_status": "n/a",
  "status": "requested",
  ...
}
```

**Request Online Payment (When Disabled)**:
```bash
curl -X POST http://localhost:8000/api/v1/bookings/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service": "service-uuid",
    "address": "123 Main St",
    "payment_method": "online"
  }'

# Response (auto-fallback to cash)
{
  "id": "booking-uuid",
  "payment_method": "cash",  # Fallback applied
  "payment_status": "n/a",
  "payment_note": "Online payments disabled - auto-converted to cash",
  ...
}
```

**Payment Endpoint Behavior**:
When `ENABLE_PAYMENTS=false`, payment endpoints return:
```bash
curl -X POST http://localhost:8000/api/v1/payments/ \
  -H "Authorization: Bearer TOKEN"

# Response: 503 Service Unavailable
{
  "detail": "Online payments are currently disabled. Please use cash payment method.",
  "code": "payments_disabled"
}
```

### Enabling Online Payments

1. Set environment variable:
   ```bash
   ENABLE_PAYMENTS=true
   ```

2. Restart services:
   ```bash
   docker-compose restart app celery
   ```

3. Configure payment gateway credentials (when integration is added)

4. Online payment bookings will now create payment orders

### Admin Interface

Booking admin shows payment fields:
- **payment_method**: Filter and view payment type
- **payment_status**: Track payment state
- **payment_note**: View auto-fallback reasons

Navigate to: http://localhost:8000/admin/bookings/booking/

## Development

### Running Tests

```bash
# Run all tests
docker-compose exec app pytest

# Run with coverage
docker-compose exec app pytest --cov=apps --cov-report=html

# Run specific test file
docker-compose exec app pytest apps/users/tests/test_otp_auth.py

# Run tests with SQLite (bypasses MySQL)
docker-compose exec -e DJANGO_TEST=True app pytest

# Run tests matching pattern
docker-compose exec app pytest -k test_otp
```

### Database Management

```bash
# Create migrations
docker-compose exec app python manage.py makemigrations

# Apply migrations
docker-compose exec app python manage.py migrate

# Seed services data
docker-compose exec app python manage.py seed_services

# Create superuser
docker-compose exec app python manage.py createsuperuser

# Access Django shell
docker-compose exec app python manage.py shell
```

### Code Quality

```bash
# Install pre-commit hooks (run locally, not in Docker)
pip install pre-commit
pre-commit install

# Run formatters manually
docker-compose exec app black .
docker-compose exec app isort --profile black .
docker-compose exec app flake8 . --max-line-length=120 --extend-ignore=E203,W503
```

### Celery Tasks

```bash
# Test notification task
docker-compose exec app python manage.py shell
>>> from apps.notifications.tasks import send_notification
>>> result = send_notification.delay(
...     user_id='user-uuid',
...     title='Test',
...     message='Test notification'
... )
>>> result.get()

# Check Celery worker logs
docker-compose logs -f celery
```

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f app
docker-compose logs -f celery
docker-compose logs -f mysql
```

## Project Structure

```
backend/
├── hunarmitra/              # Django project
│   ├── settings/            # Settings split (base, dev, prod)
│   ├── celery.py            # Celery configuration
│   ├── urls.py              # Main URL configuration
│   └── wsgi.py / asgi.py    # WSGI/ASGI applications
├── apps/                    # Django apps
│   ├── users/               # Custom user model & OTP auth
│   ├── core/                # Theme, health check, base models
│   ├── services/            # Service/skill master data
│   ├── workers/             # Worker profiles & availability
│   ├── jobs/                # Job postings & applications
│   ├── contractors/         # Contractor profiles
│   ├── attendance/          # Kiosk-based attendance
│   ├── notifications/       # Push notifications
│   └── payments/            # Payment processing (placeholder)
├── api/                     # API versioning
│   └── v1/                  # Version 1 endpoints
├── .github/workflows/       # CI/CD workflows
├── docker-compose.yml       # Docker services configuration
├── Dockerfile               # Multi-stage Docker build
├── requirements.txt         # Python dependencies
├── pytest.ini               # Pytest configuration
├── .pre-commit-config.yaml  # Code quality hooks
├── .env.example             # Environment variables template
└── README.md                # This file
```

## Apps Overview

### Users App
- Custom User model with UUID primary key and phone-based auth
- OTP generation with SHA-256 hashing and constant-time comparison
- Redis-based OTP storage with TTL and rate limiting (1/min, 5/hour)
- JWT token management with SimpleJWT and token blacklisting
- OTPLog model for audit trails
- Role-based user creation (worker/contractor)
- Custom admin with Unfold UI

### Core App
- Health check endpoint
- Theme model with exclusive active flag and admin actions
- Banner model for promotional content
- App-config API (cached) with theme, categories, banners, features
- S3 URL resolution utilities
- Base model classes (UUID, timestamps)
- Signal-based cache invalidation
- Custom Unfold admin with dark mode support

### Services App
- Master data for skills/services
- Service model with slug & icons
- Seed data management command
- Read-only API

### Workers App
- Worker profile with location (lat/lng)
- Availability status (available, busy, offline)
- Rating & job completion tracking
- Many-to-many relationship with services

### Jobs App
- Job posting model
- Status tracking (open, assigned, in_progress, completed, cancelled)
- Service association
- Worker assignment
- Location & budget fields

### Contractors App
- Contractor profile
- Company details & license info
- Rating & project tracking

### Attendance App
- Kiosk device management
- Check-in/check-out logging
- Duration calculation
- Location-based tracking

### Notifications App
- Notification model with types
- Celery task for async sending
- Read/unread status
- JSON data field for custom payloads

### Payments App
- Transaction model (placeholder)
- Multiple payment methods (UPI, card, wallet, cash)
- Status tracking
- Gateway response storage

## Testing

The project includes comprehensive tests (18+ passing):

- **OTP Auth Tests** (`test_otp_auth.py`): Request, verify, rate limiting, user creation, logout/blacklisting
- **App Config Tests** (`test_app_config.py`): Structure, caching, theme/banner rendering, S3 URL resolution
- **Health & Theme Tests** (`test_endpoints.py`): Core endpoint validation
- **Auto-Fixtures**: `conftest.py` provides `api_client` and automatic cache clearing

**SQLite Test Mode**: Set `DJANGO_TEST=True` to use SQLite instead of MySQL for faster tests.

All tests use pytest-django with proper database isolation and Redis mock support.

## CI/CD

GitHub Actions workflow runs on:
- Push to `feat/otp-theme`, `feat/backend-skeleton`
- Pull requests to `main`, `feat/contractor-dashboard`

Jobs:
1. **Lint**: black, isort, flake8
2. **Test**: pytest with MySQL and Redis services, coverage reporting

## Deployment

### Production Checklist

1. **Environment**:
   - Set `DEBUG=False`
   - Update `SECRET_KEY` to a strong random value
   - Set `ALLOWED_HOSTS` to your domain
   - Configure production database (not the default credentials)

2. **Security**:
   - Enable HTTPS (SSL certificates)
   - Update CORS settings
   - Configure proper firewall rules
   - Use strong passwords for all services

3. **Storage**:
   - Switch from MinIO to AWS S3 or equivalent
   - Update `MINIO_*` env variables accordingly

4. **Monitoring**:
   - Set up application monitoring (Sentry, etc.)
   - Configure log aggregation
   - Set up alerts for errors

5. **Database**:
   - Regular backups
   - Connection pooling
   - Read replicas if needed

## Troubleshooting

### Database Connection Issues

```bash
# Check MySQL is running
docker-compose ps mysql

# View MySQL logs
docker-compose logs mysql

# Restart MySQL
docker-compose restart mysql
```

### MinIO Access Issues

```bash
# Access MinIO console at http://localhost:9001
# Login: minioadmin / minioadmin123

# Create bucket manually if needed
# Or use boto3 script
docker-compose exec app python manage.py shell
>>> from django.core.files.storage import default_storage
>>> default_storage.bucket.exists() or default_storage.bucket.create()
```

### Celery Not Processing Tasks

```bash
# Check celery worker logs
docker-compose logs celery

# Restart celery
docker-compose restart celery

# Purge all tasks
docker-compose exec app celery -A hunarmitra purge
```

### Migration Issues

```bash
# Reset migrations (CAUTION: destroys data)
docker-compose exec app python manage.py migrate --fake-initial

# Or start fresh
docker-compose down -v
docker-compose up --build
```

## Contributing

1. Create feature branch from `feat/contractor-dashboard`
2. Make changes
3. Run tests: `docker-compose exec app pytest`
4. Run linters: `black .`, `isort .`, `flake8 .`
5. Commit with clear message
6. Push and create pull request

## License

[Add your license here]

## Support

For issues and questions:
- GitHub Issues: [repository URL]
- Email: [support email]
