"""
Production settings for HunarMitra project on Render.
"""

import os
import dj_database_url
from .base import *

DEBUG = True

# For testing: use fixed OTP 1234 (remove this in production!)
USE_FIXED_OTP = True

# Allow Render subdomain
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['.onrender.com', 'localhost'])

# Database - use DATABASE_URL from Render
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }

# Whitenoise for static files
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Security settings - relaxed for free tier (no custom domain/SSL)
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=False)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Disable S3 on Render free tier (use local/whitenoise)
USE_S3 = False

# CORS - Allow all origins for development/testing
CORS_ALLOW_ALL_ORIGINS = env.bool('CORS_ALLOW_ALL_ORIGINS', default=True)
CORS_ALLOWED_ORIGINS = []  # Clear to avoid validation errors when CORS_ALLOW_ALL_ORIGINS is True

# Disable Celery/Redis on free tier (no free Redis available)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Use local memory cache instead of Redis on free tier
# NOTE: This works for single-instance deployments. For multi-instance, use Redis.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'hunarmitra-cache',
        'OPTIONS': {
            'MAX_ENTRIES': 1000,  # Limit memory usage
        }
    }
}

# Disable channels (no WebSocket on free tier)
if 'channels' in INSTALLED_APPS:
    INSTALLED_APPS.remove('channels')

# Logging - use stdout for Render
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
