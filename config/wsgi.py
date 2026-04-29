"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

# Default to production settings for WSGI deployment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

# Allow overriding via environment variable
if os.environ.get('DJANGO_SETTINGS_MODULE'):
    pass  # Already set
elif os.environ.get('ENV_NAME'):
    os.environ['DJANGO_SETTINGS_MODULE'] = f"config.settings.{os.environ.get('ENV_NAME')}"

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
