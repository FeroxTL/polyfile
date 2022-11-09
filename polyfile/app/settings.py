import sys
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
PROJECT_DIR = Path(__file__).resolve().parent
BASE_DIR = PROJECT_DIR.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-=y=ppfyl*gza@hbw)bxfe^p)rik%t_+7@4f6vv%9e=1$lu8y#m'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
TESTING = 'test' in sys.argv
ALLOWED_HOSTS = []
INTERNAL_IPS = [
    '127.0.0.1',
]

# Application definition

AUTH_USER_MODEL = 'accounts.User'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'webpack_loader',
    'djcelery_email',
    'axes',

    'app',
    'accounts',
    'storage',

    # Registered storages
    'contrib.storages.filesystem_storage',
    'contrib.storages.s3_storage',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # AxesMiddleware should be the last middleware in the MIDDLEWARE list.
    'axes.middleware.AxesMiddleware',
]

ROOT_URLCONF = 'app.urls'
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
APPEND_SLASH = False
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

EMAIL_BACKEND = 'djcelery_email.backends.CeleryEmailBackend'
# CELERY_EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
CELERY_EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
# EMAIL_HOST = ''
# EMAIL_PORT = ''
# EMAIL_HOST_USER = ''
# EMAIL_HOST_PASSWORD = ''
# EMAIL_USE_TLS = ''
# EMAIL_USE_SSL = ''
# EMAIL_TIMEOUT = ''

EMAIL_FILE_PATH = '/tmp/app-messages'


# Celery
CELERY_BROKER_URL = 'redis://localhost/0'
CELERY_RESULT_BACKEND = 'redis://localhost/0'


# Axes
AXES_ENABLED = True
AXES_FAILURE_LIMIT = 3
AXES_LOCKOUT_TEMPLATE = 'accounts/account_is_locked.html'


# Webpack

WEBPACK_LOADER = {
  'DEFAULT': {
    'CACHE': not DEBUG,
    'BUNDLE_DIR_NAME': 'bundles/',
    'STATS_FILE': PROJECT_DIR.parent / 'webpack-stats.json',
    'POLL_INTERVAL': 0.3,
    'IGNORE': [r'.+\.hot-update.js', r'.+\.map'],
  }
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [PROJECT_DIR / 'templates'],
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

WSGI_APPLICATION = 'app.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
STATICFILES_DIRS = (
    PROJECT_DIR / 'static',
    BASE_DIR / 'web_dev_assets',
)
STATIC_ROOT = BASE_DIR / 'collected_static'


# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Debug toolbar
ENABLE_DEBUG_TOOLBAR = DEBUG and not TESTING
if ENABLE_DEBUG_TOOLBAR:
    INSTALLED_APPS.append('debug_toolbar')
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_COLLAPSED': True,
}
