import os
DEBUG = os.getenv("DJANGO_DEBUG","false").strip().lower() in ("1","true","yes","on")

"""
Django settings for org_management project.
"""

from pathlib import Path
import os
import importlib.util

# Load environment variables from .env if available (without hard import for linters)
try:
    _dotenv_spec = importlib.util.find_spec('dotenv')
    if _dotenv_spec and _dotenv_spec.loader:
        _dotenv = importlib.util.module_from_spec(_dotenv_spec)
        _dotenv_spec.loader.exec_module(_dotenv)
        _dotenv.load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / '.env')
except Exception:
    # Proceed without .env if python-dotenv isn't installed or file missing
    pass

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
# Prefer SECRET_KEY, fallback to legacy DJANGO_SECRET_KEY for compatibility
SECRET_KEY = os.getenv('SECRET_KEY') or os.getenv('DJANGO_SECRET_KEY', 'django-insecure-your-secret-key-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
# Toggleable via env; defaults to True for local dev

_env_allowed_hosts = os.getenv('ALLOWED_HOSTS', '') or os.getenv('DJANGO_ALLOWED_HOSTS', '')
if _env_allowed_hosts.strip():
    ALLOWED_HOSTS = [h.strip() for h in _env_allowed_hosts.split(',') if h.strip()]
else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

# Allow binding to 0.0.0.0 during local development (useful when running runserver 0.0.0.0:8000)
try:
    _is_debug = DEBUG  # may be defined below; if not, fallback in except
except NameError:
    _is_debug = True

if _is_debug and '0.0.0.0' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('0.0.0.0')

# CSRF trusted origins
# In development, trust common local origins to avoid CSRF failures when accessing via IP/host variants.
# In production, set CSRF_TRUSTED_ORIGINS via env as a comma-separated list of full origins (scheme://host[:port]).
_env_csrf_origins = (
    os.getenv('CSRF_TRUSTED_ORIGINS')
    or os.getenv('DJANGO_CSRF_TRUSTED_ORIGINS')
    or ''
)
if _env_csrf_origins:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in _env_csrf_origins.split(',') if o.strip()]
elif DEBUG:
    CSRF_TRUSTED_ORIGINS = [
        'http://localhost',
        'http://localhost:8000',
        'http://localhost:8001',
        'http://localhost:8002',
        'http://127.0.0.1',
        'http://127.0.0.1:8000',
        'http://127.0.0.1:8001',
        'http://127.0.0.1:8002',
        'http://0.0.0.0',
        'http://0.0.0.0:8000',
        'http://0.0.0.0:8001',
        'http://0.0.0.0:8002',
	'http://fashionexpress.ciphertextlabs.com'
    ]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',  # Our main application
    'accounts', # Custom user application
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Enable WhiteNoise only when running in production (DEBUG=False) and package is installed
_HAS_WHITENOISE = importlib.util.find_spec('whitenoise') is not None
if not DEBUG and _HAS_WHITENOISE:
    # Insert after SecurityMiddleware
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

ROOT_URLCONF = 'org_management.urls'

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
                'core.context_processors.branding',
                'core.context_processors.alerts',
            ],
        },
    },
]

WSGI_APPLICATION = 'org_management.wsgi.application'


# Database
# Default: use SQLite for local development. If Postgres env vars are provided,
# configure the default database to use Postgres so the app works under Docker.
if os.getenv('POSTGRES_DB'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('POSTGRES_DB', 'postgres'),
            'USER': os.getenv('POSTGRES_USER', 'postgres'),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'postgres'),
            'HOST': os.getenv('POSTGRES_HOST', 'db'),
            'PORT': os.getenv('POSTGRES_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


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

# Set default timezone to Dhaka, Bangladesh
TIME_ZONE = 'Asia/Dhaka'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Use compressed manifest storage only in production when WhiteNoise is available
if not DEBUG and _HAS_WHITENOISE:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login URL
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

AUTH_USER_MODEL = 'accounts.CustomUser'

# Branding (used in UI + printable documents)
BRAND_NAME = os.getenv('BRAND_NAME', 'Fashion Express')
# Path under static/ e.g., 'logo.png' (optional)
BRAND_LOGO_FILE = os.getenv('BRAND_LOGO_FILE', '')
BRAND_ADDRESS = os.getenv('BRAND_ADDRESS', '')
BRAND_PHONE = os.getenv('BRAND_PHONE', '')
BRAND_EMAIL = os.getenv('BRAND_EMAIL', '')


SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
USE_X_FORWARDED_HOST = True

DEBUG = False
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000300
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = False
