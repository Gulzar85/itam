"""
Security settings for ITAM project
Import this in base.py or production.py
"""

# Security headers
X_FRAME_OPTIONS = 'DENY'  # Prevent clickjacking
X_CONTENT_TYPE_OPTIONS = 'nosniff'  # Prevent MIME type sniffing
X_XSS_PROTECTION = '1; mode=block'  # XSS protection

# Cookie security
SESSION_COOKIE_SECURE = True  # Only send cookies over HTTPS
CSRF_COOKIE_SECURE = True  # Only send CSRF token over HTTPS
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to cookies
CSRF_COOKIE_HTTPONLY = True

# SSL/HTTPS settings
SECURE_SSL_REDIRECT = True  # Redirect all HTTP to HTTPS
SECURE_HSTS_SECONDS = 31536000  # HSTS for 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Referrer policy
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Content Security Policy (basic)
# Uncomment and customize for your needs
# CONTENT_SECURITY_POLICY = {
#     'default-src': ["'self'"],
#     'script-src': ["'self'", "'unsafe-inline'"],  # Consider removing unsafe-inline
#     'style-src': ["'self'", "'unsafe-inline'"],
# }

# CORS settings (if API endpoints exist)
# CORS_ALLOW_ALL_ORIGINS = False
# CORS_ALLOWED_ORIGINS = ['https://yourdomain.com']
