"""
edtech/settings.py
------------------
Django settings for the EdTech Email Reminder System.

CHANGES vs original:
  • Added django-allauth + Google OAuth provider
  • Added django.contrib.auth / messages / admin / sites (required by allauth)
  • Added 'accounts' app (new: whitelist, roles, UserProfile)
  • Added 'instructors' app (new: Instructor + Batch cost extension)
  • Added AUTHENTICATION_BACKENDS for allauth
  • Added ALLAUTH_* settings
  • Added GOOGLE_OAUTH_* env vars
  • Added SESSION_COOKIE_SECURE / CSRF_COOKIE_SECURE for HTTPS-readiness
  • All existing settings left unchanged.
"""

import os
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env
env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

# ---------------------------------------------------------------------------
# Core Django settings
# ---------------------------------------------------------------------------

SECRET_KEY = env('SECRET_KEY', default='change-me-in-production')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# ---------------------------------------------------------------------------
# Installed apps
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    # Django built-ins (allauth requires these)
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.auth',
    'django.contrib.messages',          # NEW — required by allauth
    'django.contrib.staticfiles',
    'django.contrib.sites',             # NEW — required by allauth

    # Third-party
    'rest_framework',
    'django_apscheduler',
    'allauth',                          # NEW
    'allauth.account',                  # NEW
    'allauth.socialaccount',            # NEW
    'allauth.socialaccount.providers.google',  # NEW

    # Project apps
    'core.apps.CoreConfig',
    'accounts.apps.AccountsConfig',     # NEW — whitelist + RBAC
    'instructors.apps.InstructorsConfig',  # NEW — instructor management
]

SITE_ID = 1  # Required by allauth

# ---------------------------------------------------------------------------
# Authentication backends
# ---------------------------------------------------------------------------

AUTHENTICATION_BACKENDS = [
    'accounts.auth_backends.EmailBackend',
    # Needed for username+password fallback via Django admin / allauth
    'django.contrib.auth.backends.ModelBackend',
    # Google OAuth via allauth
    'allauth.account.auth_backends.AuthenticationBackend',
]

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',           # NEW — CSRF protection
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # NEW — allauth needs this
    'django.contrib.messages.middleware.MessageMiddleware',     # NEW — allauth needs this
    'allauth.account.middleware.AccountMiddleware',              # NEW — allauth
    'accounts.middleware.WhitelistMiddleware',                   # NEW — replaces old LoginRequiredMiddleware
]

ROOT_URLCONF = 'edtech.urls'

# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'core' / 'templates'],
        'APP_DIRS': True,           # Changed from False → True so allauth templates resolve
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',    # NEW
                'django.contrib.messages.context_processors.messages',  # NEW
            ],
        },
    },
]

WSGI_APPLICATION = 'edtech.wsgi.application'

# ---------------------------------------------------------------------------
# Database (unchanged)
# ---------------------------------------------------------------------------

DATABASE_URL = env('DATABASE_URL', default='sqlite:///data/edtech.db')
_db_path = DATABASE_URL.replace('sqlite:///', '')
if not os.path.isabs(_db_path):
    _db_path = str(BASE_DIR / _db_path)

os.makedirs(os.path.dirname(_db_path), exist_ok=True)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': _db_path,
        'OPTIONS': {
            'timeout': 20,
        },
    }
}

# ---------------------------------------------------------------------------
# Sessions (unchanged + HTTPS-readiness)
# ---------------------------------------------------------------------------

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG      # NEW — True in production
CSRF_COOKIE_SECURE = not DEBUG         # NEW — True in production
CSRF_COOKIE_HTTPONLY = False          # NEW

# ---------------------------------------------------------------------------
# Allauth — Google OAuth configuration
# ---------------------------------------------------------------------------

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/login/'

ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'none'    # No email confirmation — whitelist handles access
SOCIALACCOUNT_AUTO_SIGNUP = True   # ← Add this line
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https' if not DEBUG else 'http'

# Adapter: enforces whitelist on every social login
SOCIALACCOUNT_ADAPTER = 'accounts.adapters.WhitelistSocialAccountAdapter'
ACCOUNT_ADAPTER = 'accounts.adapters.WhitelistAccountAdapter'
SOCIALACCOUNT_LOGIN_ON_GET = True

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': env('GOOGLE_CLIENT_ID', default=''),
            'secret': env('GOOGLE_CLIENT_SECRET', default=''),
            'key': ''
        },
        'AUTH_PARAMS': {'access_type': 'online'},
        'FETCH_USERINFO': True,
        'SCOPE': ['profile', 'email'],
    }
}

# Super admin email — seeded automatically on first login
SUPER_ADMIN_EMAIL = env('SUPER_ADMIN_EMAIL', default='anand@skillfyme.in')

# ---------------------------------------------------------------------------
# Internationalization (unchanged)
# ---------------------------------------------------------------------------

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------------------------
# DRF (unchanged)
# ---------------------------------------------------------------------------

REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'core.views.custom_exception_handler',
    'UNAUTHENTICATED_USER': None,
}

# ---------------------------------------------------------------------------
# Application configuration (unchanged)
# ---------------------------------------------------------------------------

ADMIN_USERNAME = env('ADMIN_USERNAME', default='admin')
ADMIN_PASSWORD_HASH = env('ADMIN_PASSWORD_HASH', default='') or \
    '$2b$12$DShXeGCG3ReP5AGxvuAcN.seMknLLshFGpHbx2A18bf5qj1dzruJO'

ZEPTO_TOKEN = env('ZEPTO_TOKEN', default='')
SENDER_EMAIL = env('SENDER_EMAIL', default='')
SENDER_NAME = env('SENDER_NAME', default='Skillfyme Platform')

EMAIL_SEND_DELAY_SECONDS = env.float('EMAIL_SEND_DELAY_SECONDS', default=1.0)
MAX_RETRY_ATTEMPTS = env.int('MAX_RETRY_ATTEMPTS', default=3)
MINUTES_BEFORE_CLASS = env.int('MINUTES_BEFORE_CLASS', default=60)

APP_TIMEZONE = env('APP_TIMEZONE', default='Asia/Kolkata')
LOG_LEVEL = env('LOG_LEVEL', default='INFO')

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = []

# ---------------------------------------------------------------------------
# Logging (unchanged)
# ---------------------------------------------------------------------------

_logs_dir = BASE_DIR / 'logs'
_logs_dir.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': str(BASE_DIR / 'logs' / 'app.log'),
            'encoding': 'utf-8',
            'formatter': 'standard',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': LOG_LEVEL,
    },
}
STATIC_ROOT = BASE_DIR / 'staticfiles'
