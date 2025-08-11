# oapi_canteen/settings/base.py
import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default="'django-insecure-2+)!4h!2@sz+e%mbqmd14v9kh=6myj#83o%j9lfavepjd53&@('")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,0.0.0.0', cast=lambda v: [s.strip() for s in v.split(',')])

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'crispy_forms',
    'crispy_bootstrap5',
    'django_extensions',
]

LOCAL_APPS = [
    'apps.accounts',
    'apps.menu',
    'apps.orders',
    'apps.payments',
    'apps.notifications',
    'apps.dashboard',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'oapi_canteen.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
        },
    },
]

WSGI_APPLICATION = 'oapi_canteen.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME', default='oapi_canteen'),
        'USER': config('DB_USER', default='canteen_user'),
        'PASSWORD': config('DB_PASSWORD', default='SecurePassword123!'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

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

# Authentication
LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/auth/login/'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Douala'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# Email Configuration
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='ndjodongouhs@gmail.com')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='s0ule3m4n')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@oapi-canteen.cm')

# Site Configuration
SITE_NAME = 'OAPI Canteen'
SITE_URL = config('SITE_URL', default='http://localhost:8000')

# Payment Gateway Settings
ORANGE_MONEY = {
    'BASE_URL': config('ORANGE_BASE_URL', default='https://api.orange.com'),
    'API_KEY': config('ORANGE_API_KEY', default=''),
    'API_SECRET': config('ORANGE_API_SECRET', default=''),
    'MERCHANT_KEY': config('ORANGE_MERCHANT_KEY', default=''),
    'SANDBOX': config('ORANGE_SANDBOX', default=True, cast=bool),
}

MTN_MONEY = {
    'BASE_URL': config('MTN_BASE_URL', default='https://sandbox.momodeveloper.mtn.com'),
    'API_KEY': config('MTN_API_KEY', default=''),
    'API_SECRET': config('MTN_API_SECRET', default=''),
    'SUBSCRIPTION_KEY': config('MTN_SUBSCRIPTION_KEY', default=''),
    'SANDBOX': config('MTN_SANDBOX', default=True, cast=bool),
}

# Logging Configuration
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
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Create logs directory
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'oapi-canteen-cache',
    }
}

# Session Configuration
SESSION_COOKIE_AGE = 3600 * 4  # 4 hours
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

# Application Settings
CANTEEN_SETTINGS = {
    'ORDER_EXPIRY_MINUTES': 30,
    'MAX_CART_ITEMS': 50,
    'DEFAULT_TAX_RATE': 0.05,  # 5% VAT
    'DELIVERY_FEE': 500,  # 500 XAF
    'MIN_ORDER_AMOUNT': 1000,  # 1000 XAF
    'MAX_ORDER_AMOUNT': 100000,  # 100,000 XAF
}