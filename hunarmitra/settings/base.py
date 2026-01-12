"""
Base Django settings for HunarMitra project.
"""

import os
from pathlib import Path

import environ

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Initialize environment variables
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
)

# Read .env file if it exists
env_file = os.path.join(BASE_DIR, '.env')
if os.path.exists(env_file):
    environ.Env.read_env(env_file)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='django-insecure-dev-key-change-in-production')

# Application definition
INSTALLED_APPS = [
    # Unfold admin theme (must be before django.contrib.admin)
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_spectacular',
    'rest_framework_simplejwt.token_blacklist',
    
    # Local apps
    'apps.users',
    'apps.core',
    'apps.services',
    'apps.workers',
    'apps.jobs',
    'apps.contractors',
    'apps.emergency',  # Emergency help-now system
    'apps.dashboard',  # Role-based dashboard summaries
    'apps.attendance',
    'apps.notifications',
    'apps.payments',
    'apps.bookings',
    'apps.tracking',
    'apps.media',
    'apps.tts',
    'apps.help',
    'apps.cms',
    'apps.analytics',
    'apps.kyc',
    'apps.flags',
]

# Add channels if installed (optional dependency)
try:
    import channels
    INSTALLED_APPS.append('channels')
except ImportError:
    pass

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'hunarmitra.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'hunarmitra.wsgi.application'

# Database
if os.environ.get('DJANGO_TEST') == 'True':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': env('MYSQL_DATABASE', default='hunarmitra'),
            'USER': env('MYSQL_USER', default='hunarmitra_user'),
            'PASSWORD': env('MYSQL_PASSWORD', default='password'),
            'HOST': env('MYSQL_HOST', default='localhost'),
            'PORT': env('MYSQL_PORT', default='3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    # Rate Limiting
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': env('THROTTLE_ANON', default='100/hour'),
        'user': env('THROTTLE_USER', default='1000/hour'),
    },
}

# JWT Settings
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=env.int('JWT_ACCESS_TOKEN_LIFETIME_MINUTES', default=60)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=env.int('JWT_REFRESH_TOKEN_LIFETIME_DAYS', default=7)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': env('SIMPLE_JWT_SECRET', default=SECRET_KEY),
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# CORS Settings
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    'http://localhost:3000',
    'http://127.0.0.1:3000',
])

# Cache Configuration - Redis
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://redis:6379/1'),
    }
}

# OTP Configuration
OTP_EXPIRE_SECONDS = env.int('OTP_TTL_SECONDS', default=300)
OTP_RATE_LIMIT_PER_MINUTE = env.int('OTP_RATE_LIMIT_PER_MINUTE', default=1)
OTP_RATE_LIMIT_PER_HOUR = env.int('OTP_RATE_LIMIT_PER_HOUR', default=5)
OTP_RATE_LIMIT_REQUESTS = env.int('OTP_RATE_LIMIT_REQUESTS', default=5)  # Max requests per window
OTP_RATE_LIMIT_WINDOW_SECONDS = env.int('OTP_RATE_LIMIT_WINDOW_SECONDS', default=3600)  # 1 hour window
USE_FIXED_OTP = env.bool('USE_FIXED_OTP', default=False)  # For testing: always use OTP 1234
SMS_PROVIDER = env('SMS_PROVIDER', default='dev')

# Storage Configuration (S3/MinIO)
USE_S3 = env.bool('USE_S3', default=False)

if USE_S3:
    # AWS S3 / MinIO configuration
    AWS_ACCESS_KEY_ID = env('MINIO_ACCESS_KEY', default='')
    AWS_SECRET_ACCESS_KEY = env('MINIO_SECRET_KEY', default='')
    AWS_STORAGE_BUCKET_NAME = env('MINIO_BUCKET', default='hunarmitra')
    AWS_S3_ENDPOINT_URL = env('MINIO_ENDPOINT', default='http://localhost:9000')
    AWS_S3_USE_SSL = env.bool('MINIO_USE_SSL', default=False)
    AWS_S3_CUSTOM_DOMAIN = f"{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}"
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    AWS_DEFAULT_ACL = 'public-read'
    AWS_QUERYSTRING_AUTH = False
    
    # Use S3 ONLY for media files (uploads), NOT for static files (CSS/JS)
    # Static files should be served locally for admin panel to work correctly
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    # STATICFILES_STORAGE is intentionally NOT set to use default local serving

# DRF Spectacular (OpenAPI)
SPECTACULAR_SETTINGS = {
    'TITLE': 'HunarMitra API',
    'DESCRIPTION': 'API documentation for HunarMitra backend',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': '/api/v1',
    'COMPONENT_SPLIT_REQUEST': True,
}

# Feature Flags
# -----------------------------------------------------------------------------
FEATURE_BIOMETRIC_STUB = env.bool('FEATURE_BIOMETRIC_STUB', default=True)

# Payment Configuration
# -----------------------------------------------------------------------------
ENABLE_PAYMENTS = env.bool('ENABLE_PAYMENTS', default=False)

# Notifications Configuration
# -----------------------------------------------------------------------------
ENABLE_NOTIFICATIONS = env.bool('ENABLE_NOTIFICATIONS', default=True)
FCM_SERVER_KEY = env('FCM_SERVER_KEY', default='')

# Django Channels Configuration (WebSocket support)
# -----------------------------------------------------------------------------
if 'channels' in INSTALLED_APPS:
    ASGI_APPLICATION = 'hunarmitra.asgi.application'
    
    # Channel layers - In-memory for development
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer'
        }
    }

# Contractor Site Management
# -----------------------------------------------------------------------------
FEATURE_CONTRACTOR_SITES = env.bool('FEATURE_CONTRACTOR_SITES', default=True)

# Emergency / Help-Now System
# -----------------------------------------------------------------------------
FEATURE_EMERGENCY = env.bool('FEATURE_EMERGENCY', default=True)
EMERGENCY_AUTO_ASSIGN = env.bool('EMERGENCY_AUTO_ASSIGN', default=False)
EMERGENCY_SEARCH_RADIUS_KM = env.int('EMERGENCY_SEARCH_RADIUS_KM', default=5)
EMERGENCY_RATE_LIMIT_PER_MINUTE = env.int('EMERGENCY_RATE_LIMIT_PER_MINUTE', default=1)
EMERGENCY_MAX_CANDIDATES = env.int('EMERGENCY_MAX_CANDIDATES', default=5)
EMERGENCY_RESPONSE_TIMEOUT_SECONDS = env.int('EMERGENCY_RESPONSE_TIMEOUT_SECONDS', default=45)

# FCM Push Notifications
# -----------------------------------------------------------------------------
FCM_ENABLED = env.bool('FCM_ENABLED', default=False)
FCM_SERVER_KEY = env.str('FCM_SERVER_KEY', default='')
FCM_RATE_LIMIT_PER_MINUTE = env.int('FCM_RATE_LIMIT_PER_MINUTE', default=60)
FCM_MAX_RETRIES = env.int('FCM_MAX_RETRIES', default=3)
FCM_BATCH_SIZE = env.int('FCM_BATCH_SIZE', default=100)
FCM_ENDPOINT = 'https://fcm.googleapis.com/fcm/send'  # Legacy HTTP API

# Dashboard Configuration
# -----------------------------------------------------------------------------
DASHBOARD_CACHE_TTL_SECONDS = env.int('DASHBOARD_CACHE_TTL_SECONDS', default=15)
DASHBOARD_CACHE_MAX_STALE_SECONDS = env.int('DASHBOARD_CACHE_MAX_STALE_SECONDS', default=60)

# Analytics Configuration
# -----------------------------------------------------------------------------
ANALYTICS_ENABLED = env.bool('ANALYTICS_ENABLED', default=True)
ANALYTICS_RETENTION_DAYS = env.int('ANALYTICS_RETENTION_DAYS', default=90)
ANALYTICS_MAX_EVENT_SIZE = env.int('ANALYTICS_MAX_EVENT_SIZE', default=2048)

# KYC & Registration Configuration
# -----------------------------------------------------------------------------
KYC_UPLOAD_MAX_SIZE_MB = env.int('KYC_UPLOAD_MAX_SIZE_MB', default=5)
KYC_AUTO_APPROVE_THRESHOLD = env.int('KYC_AUTO_APPROVE_THRESHOLD', default=0)
KYC_DOCUMENT_RETENTION_DAYS = env.int('KYC_DOCUMENT_RETENTION_DAYS', default=90)
KYC_PRESIGNED_URL_EXPIRY_MINUTES = env.int('KYC_PRESIGNED_URL_EXPIRY_MINUTES', default=15)

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': env('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# ==============================================================================
# Django Unfold Admin Theme Configuration
# ==============================================================================

from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

UNFOLD = {
    "SITE_TITLE": "HunarMitra Admin",
    "SITE_HEADER": "HunarMitra",
    "SITE_URL": "/",
    "SITE_ICON": {
        "light": lambda request: static("logo.svg"),  # Light theme icon
        "dark": lambda request: static("logo-dark.svg"),  # Dark theme icon
    },
    "SITE_LOGO": {
        "light": lambda request: static("logo.svg"),  # Light theme logo
        "dark": lambda request: static("logo-dark.svg"),  # Dark theme logo
    },
    "SITE_SYMBOL": "🔧",  # Symbol for compact sidebar
    "SHOW_HISTORY": True,  # Show history on detail pages
    "SHOW_VIEW_ON_SITE": True,  # Show "View on site" link
    "ENVIRONMENT": "apps.core.utils.environment_callback",
    "DASHBOARD_CALLBACK": "apps.core.utils.dashboard_callback",
    "LOGIN": {
        "image": lambda request: static("images/login-bg.jpg"),
        "redirect_after": lambda request: reverse_lazy("admin:index"),
    },
    "STYLES": [
        lambda request: static("css/admin-custom.css"),
    ],
    "SCRIPTS": [
        lambda request: static("js/admin-custom.js"),
    ],
    "COLORS": {
        "primary": {
            "50": "236 253 245",
            "100": "209 250 229",
            "200": "167 243 208",
            "300": "110 231 183",
            "400": "52 211 153",
            "500": "37 99 235",  # HunarMitra Primary Blue
            "600": "30 64 175",
            "700": "29 78 216",
            "800": "30 64 175",
            "900": "23 37 84",
            "950": "13 25 52",
        },
    },
    "EXTENSIONS": {
        "modeltranslation": {
            "flags": {
                "en": "🇬🇧",
                "hi": "🇮🇳",
                "mr": "🇮🇳",
            },
        },
    },
    "SIDEBAR": {
        "show_search": True,  # Search in sidebar
        "show_all_applications": True,  # Show all applications
        "navigation": [
            {
                "title": _("Dashboard"),
                "separator": False,
                "items": [
                    {
                        "title": _("Dashboard"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                ],
            },
            {
                "title": _("User Management"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Users"),
                        "icon": "person",
                        "link": reverse_lazy("admin:users_user_changelist"),
                    },
                    {
                        "title": _("Workers"),
                        "icon": "engineering",
                        "link": reverse_lazy("admin:workers_workerprofile_changelist"),
                    },
                    {
                        "title": _("Contractors"),
                        "icon": "business",
                        "link": reverse_lazy("admin:contractors_contractorprofile_changelist"),
                    },
                ],
            },
            {
                "title": _("Services & Jobs"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Services"),
                        "icon": "build",
                        "link": reverse_lazy("admin:services_service_changelist"),
                    },
                    {
                        "title": _("Jobs"),
                        "icon": "work",
                        "link": reverse_lazy("admin:jobs_job_changelist"),
                    },
                ],
            },
            {
                "title": _("Operations"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Attendance Kiosks"),
                        "icon": "schedule",
                        "link": reverse_lazy("admin:attendance_attendancekiosk_changelist"),
                    },
                    {
                        "title": _("Attendance Logs"),
                        "icon": "assignment",
                        "link": reverse_lazy("admin:attendance_attendancelog_changelist"),
                    },
                ],
            },
            {
                "title": _("Content & Settings"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Themes"),
                        "icon": "palette",
                        "link": reverse_lazy("admin:core_theme_changelist"),
                    },
                    {
                        "title": _("Banners"),
                        "icon": "image",
                        "link": reverse_lazy("admin:core_banner_changelist"),
                    },
                    {
                        "title": _("Notifications"),
                        "icon": "notifications",
                        "link": reverse_lazy("admin:notifications_notification_changelist"),
                    },
                ],
            },
            {
                "title": _("Financial"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Transactions"),
                        "icon": "payment",
                        "link": reverse_lazy("admin:payments_transaction_changelist"),
                    },
                ],
            },
        ],
    },
    "TABS": [
        {
            "models": [
                "users.user",
            ],
            "items": [
                {
                    "title": _("User Details"),
                    "link": reverse_lazy("admin:users_user_changelist"),
                },
                {
                    "title": _("Groups"),
                    "link": reverse_lazy("admin:auth_group_changelist"),
                },
            ],
        },
    ],
}

# Sentry Error Tracking (Optional)
# -----------------------------------------------------------------------------
SENTRY_DSN = env('SENTRY_DSN', default=None)

if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[DjangoIntegration()],
            environment=env('SENTRY_ENVIRONMENT', default='production'),
            traces_sample_rate=env.float('SENTRY_TRACES_SAMPLE_RATE', default=0.1),
            send_default_pii=False,  # Don't send personal data
        )
    except ImportError:
        # Sentry SDK not installed - skip initialization
        pass
