from .base import *

DEBUG = False
ALLOWED_HOSTS = config('ALLOWED_HOSTS').split(',')

# Security settings for production
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# Static files for production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'