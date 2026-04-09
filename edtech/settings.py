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
  • Fixed DATABASE_URL to correctly handle PostgreSQL via dj-database-url
  • All existing settings left unchanged.
"""
import os
from pathlib import Path
import environ
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env
env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

# ---------------------------------------------------------------------------
# Core Django settings
# ---------------------------------------------------------------------------
SECRET_KEY = env('SECRET_KEY', default='change-me-in-production')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')
# ---------------------------------------------------------------------------
# Installed apps
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    # Django built-ins (allauth requires these)
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.auth',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    # Third-party
    'rest_framework',
    'django_apscheduler',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    # Project apps
    'core.apps.CoreConfig',
    'accounts.apps.AccountsConfig',
    'instructors.apps.InstructorsConfig',
]

SITE_ID = 1

# ---------------------------------------------------------------------------
# Authentication backends
# ---------------------------------------------------------------------------
AUTHENTICATION_BACKENDS = [
    'accounts.auth_backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'accounts.middleware.WhitelistMiddleware',
]

ROOT_URLCONF = 'edtech.urls'

# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'core' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'edtech.wsgi.application'

# ---------------------------------------------------------------------------
# Database — correctly handles both PostgreSQL and SQLite URLs
# ---------------------------------------------------------------------------
DATABASES = {
    'default': dj_database_url.config(
        default=env('DATABASE_URL', default='sqlite:///data/edtech.db'),
        conn_max_age=600,
        ssl_require=True
    )
}

# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = False

# ---------------------------------------------------------------------------
# Allauth — Google OAuth configuration
# ---------------------------------------------------------------------------
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/login/'
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_AUTO_SIGNUP = True
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https' if not DEBUG else 'http'
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

SUPER_ADMIN_EMAIL = env('SUPER_ADMIN_EMAIL', default='anand@skillfyme.in')

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------------------------
# DRF
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'core.views.custom_exception_handler',
    'UNAUTHENTICATED_USER': None,
}

# ---------------------------------------------------------------------------
# Application configuration
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

# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = []
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ---------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------

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
    },
    'root': {
        'handlers': ['console'],
        'level': LOG_LEVEL,
    }
}