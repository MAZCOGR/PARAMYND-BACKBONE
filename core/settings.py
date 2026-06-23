"""
Paramynd Admin — core/settings.py
Même architecture que paramynd, avec ajout des SDKs GCP pour le control plane.
"""
import os
from pathlib import Path
from datetime import timedelta
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# ==============================================================================
# SÉCURITÉ
# ==============================================================================
SECRET_KEY = env('SECRET_KEY', default='changeme-in-production')
DEBUG = env('DEBUG', default=True)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[]) + [
    'localhost',
    '127.0.0.1',
    'paramynd.com',
    'www.paramynd.com',
    'paramynd.web.app',
    'paramynd-admin-343192497073.europe-west9.run.app',
    'paramynd-admin.com',
    'admin.paramynd.com',
]

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8001',
    'http://localhost:8002',
    'http://127.0.0.1:8001',
    'http://127.0.0.1:8002',
    'https://paramynd.com',
    'https://www.paramynd.com',
    'https://paramynd.web.app',
    'https://paramynd-admin-343192497073.europe-west9.run.app',
    'https://admin.paramynd.com',
]

# ==============================================================================
# APPLICATIONS
# ==============================================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'oauth2_provider',

    # Paramynd Admin apps
    'accounts',
    'tenants',
    'monitoring',
]

MIDDLEWARE = [
    'core.middleware.ProxyFixMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# ==============================================================================
# DÉTECTION ENVIRONNEMENT
# ==============================================================================
IS_CLOUD_RUN = os.getenv('K_SERVICE') is not None or os.getenv('CLOUD_RUN_JOB') is not None

# ==============================================================================
# BASE DE DONNÉES
# Cloud Run  → Unix socket vers Cloud SQL (pas de proxy, pas de réseau)
# Local dev  → Cloud SQL Proxy sur 127.0.0.1:5433
# ==============================================================================
CLOUD_SQL_INSTANCE = os.getenv('CLOUD_SQL_INSTANCE', 'yellow-455523:europe-west9:yellow-db-paris')

if IS_CLOUD_RUN:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'paramynd_admin'),
            'USER': os.getenv('DB_USER', 'admin'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'HOST': f'/cloudsql/{CLOUD_SQL_INSTANCE}',
            'PORT': '5432',
            'CONN_MAX_AGE': 60,
        }
    }
    USE_X_FORWARDED_HOST = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'Lax'
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env('DB_NAME', default='paramynd_admin'),
            'USER': env('DB_USER', default='admin'),
            'PASSWORD': env('DB_PASSWORD', default='admin123'),
            'HOST': env('DB_HOST', default='127.0.0.1'),
            'PORT': env('DB_PORT', default='5433'),
            'CONN_MAX_AGE': 60,
        }
    }

# ==============================================================================
# GCP CONFIGURATION
# ==============================================================================
GCP_PROJECT_ID = env('GCP_PROJECT_ID', default='yellow-455523')
GCP_REGION = env('GCP_REGION', default='europe-west9')
ARTIFACT_REGISTRY_REPO = env('ARTIFACT_REGISTRY_REPO', default='paramynd')
PARAMYND_IMAGE_NAME = env('PARAMYND_IMAGE_NAME', default='app')

# URI de base pour Artifact Registry
ARTIFACT_REGISTRY_BASE = f"{GCP_REGION}-docker.pkg.dev/{GCP_PROJECT_ID}/{ARTIFACT_REGISTRY_REPO}"

# ==============================================================================
# AUTHENTIFICATION
# ==============================================================================
AUTH_USER_MODEL = 'accounts.User'

AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/tenants/'
LOGOUT_REDIRECT_URL = '/auth/login/'

# ==============================================================================
# JWT
# ==============================================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
        'login_attempt': '10/min',
    },
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# ==============================================================================
# CORS
# ==============================================================================
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    'http://localhost:3000',
    'http://127.0.0.1:3000',
])
CORS_ALLOW_CREDENTIALS = True

# ==============================================================================
# INTERNATIONALISATION
# ==============================================================================
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

# ==============================================================================
# FICHIERS STATIQUES & MÉDIAS
# ==============================================================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================================================================
# EMAIL (POSTMARK / SMTP)
# ==============================================================================
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='smtp.postmarkapp.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@paramynd.com')

# ==============================================================================
# SMS (TWILIO)
# ==============================================================================
TWILIO_ACCOUNT_SID = env('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = env('TWILIO_AUTH_TOKEN', default='')
TWILIO_FROM_NUMBER = env('TWILIO_FROM_NUMBER', default='')

# ==============================================================================
# SESSION
# ==============================================================================
SESSION_COOKIE_AGE = 86400 * 7  # 7 jours
SESSION_COOKIE_HTTPONLY = True

# ==============================================================================
# LOGGING
# ==============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '{levelname} {asctime} {module}: {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        '': {'handlers': ['console'], 'level': 'INFO'},
        'django': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
    },
}
