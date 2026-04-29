"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

# Default to production settings for ASGI deployment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

# Allow overriding via environment variable
if os.environ.get('DJANGO_SETTINGS_MODULE'):
    pass  # Already set
elif os.environ.get('ENV_NAME'):
    os.environ['DJANGO_SETTINGS_MODULE'] = f"config.settings.{os.environ.get('ENV_NAME')}"

from django.core.asgi import get_asgi_application
application = get_asgi_application()
