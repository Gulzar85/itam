import os
from pathlib import Path

from .base import *

DEBUG = False

# SQLite for production (Windows Server - no PostgreSQL required)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 30,
        }
    }
}

# Security settings for production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_SSL_REDIRECT = False  # Set to True if using HTTPS/SSL on server
SESSION_COOKIE_SECURE = False  # Set to True if using HTTPS
CSRF_COOKIE_SECURE = False  # Set to True if using HTTPS
SECURE_HSTS_SECONDS = 0  # Enable if using HTTPS
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Allowed hosts - update with your server IP/domain
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])  # Update with your server IP/domain for production

# Logging for production
logs_dir = BASE_DIR / 'logs'
logs_dir.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': logs_dir / 'error.log',
            'formatter': 'verbose',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
