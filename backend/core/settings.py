"""Core settings for the agriculture modular monolith."""

from datetime import timedelta
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_env_file(env_file_path):
    """Load KEY=VALUE entries from environment file into process environment."""
    if not env_file_path.exists():
        return
    for raw_line in env_file_path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith('#'):
            continue
        if '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(key, value)


def _env_required(name):
    """Return required environment variable or raise configuration error."""
    value = os.environ.get(name, '').strip()
    if not value:
        raise ImproperlyConfigured(f'Missing required environment variable: {name}')
    return value


def _env_bool(name, default=False):
    """Return boolean value parsed from environment variable."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {'1', 'true', 'yes', 'on'}


def _env_int(name, default):
    """Return integer value parsed from environment variable."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    return int(raw.strip())


def _env_list(name, default=''):
    """Return comma-separated list parsed from environment variable."""
    raw = os.environ.get(name, default)
    return [item.strip() for item in raw.split(',') if item.strip()]


def _configure_postgres_driver():
    """Validate configured PostgreSQL driver dependency."""
    driver = os.environ.get('POSTGRES_DRIVER', 'psycopg2').strip().lower()
    if driver != 'psycopg2':
        raise ImproperlyConfigured('POSTGRES_DRIVER must be set to psycopg2.')
    try:
        import psycopg2
    except ImportError as exc:
        raise ImproperlyConfigured(
            'psycopg2-binary is required. Install it with: pip install psycopg2-binary'
        ) from exc
    return driver


_load_env_file(BASE_DIR / '.env')
POSTGRES_DRIVER = _configure_postgres_driver()

SECRET_KEY = _env_required('DJANGO_SECRET_KEY')
DEBUG = _env_bool('DJANGO_DEBUG', False)
ALLOWED_HOSTS = _env_list('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'users.apps.UsersConfig',
    'verification.apps.VerificationConfig',
    'listings.apps.ListingsConfig',
    'discovery.apps.DiscoveryConfig',
    'orders.apps.OrdersConfig',
    'payments.apps.PaymentsConfig',
    'logistics.apps.LogisticsConfig',
    'reputation.apps.ReputationConfig',
    'audit.apps.AuditConfig',
    'dashboard.apps.DashboardConfig',
    'corsheaders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'audit.middleware.AuditContextMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'core.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': _env_required('POSTGRES_DB'),
        'USER': _env_required('POSTGRES_USER'),
        'PASSWORD': _env_required('POSTGRES_PASSWORD'),
        'HOST': _env_required('POSTGRES_HOST'),
        'PORT': _env_required('POSTGRES_PORT'),
        'CONN_MAX_AGE': _env_int('POSTGRES_CONN_MAX_AGE', 60),
    }
}

if os.environ.get('POSTGRES_SSLMODE'):
    DATABASES['default']['OPTIONS'] = {'sslmode': os.environ['POSTGRES_SSLMODE']}

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

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'users.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=_env_int('JWT_ACCESS_MINUTES', 15)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=_env_int('JWT_REFRESH_DAYS', 7)),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
