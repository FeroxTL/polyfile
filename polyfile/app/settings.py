import os
import sys
from pathlib import Path

from environ import environ

PROJECT_DIR = Path(__file__).resolve().parent
BASE_DIR = PROJECT_DIR.parent
ROOT_DIR = BASE_DIR.parent

env = environ.Env(
    DEBUG=(bool, True),
    ENVFILE=(str, Path.cwd() / '.env'),
    ALLOWED_HOSTS=(list, ['localhost']),
    INTERNAL_IPS=(list, ['127.0.0.1'])
)

# SECURITY WARNING: don't run with debug turned on in production!
TESTING = 'test' in sys.argv
NORMAL_RUNNING = os.getenv('WSGI_SERVER') or 'runserver' in sys.argv
if not TESTING:
    environ.Env.read_env(env('ENVFILE'))
DEBUG = env.bool('DEBUG')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str('SECRET_KEY', 'django-insecure-=y=ppfyl*gza@hbw)bxfe^p)rik%t_+7@4f6vv%9e=1$lu8y#m')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')
INTERNAL_IPS = env.list('INTERNAL_IPS')
DISABLE_CACHE = env.bool('DISABLE_CACHE', False)

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

    'polyfile.app',
    'polyfile.accounts',
    'polyfile.storage',

    # Registered storages
    'polyfile.contrib.storages.filesystem_storage',
    'polyfile.contrib.storages.s3_storage',
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

ROOT_URLCONF = 'polyfile.app.urls'
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
APPEND_SLASH = True
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]
# When reset password form can be submitted again for user
PASSWORD_RESET_FORM_TIMEOUT = env.int(
    'PASSWORD_RESET_FORM_TIMEOUT',
    10 * 24 * 60 * 60  # 3 days
)

DEFAULT_EMAIL_BACKEND = \
    'django.core.mail.backends.filebased.EmailBackend' if DEBUG else 'djcelery_email.backends.CeleryEmailBackend'
EMAIL_BACKEND = env.str('EMAIL_BACKEND', DEFAULT_EMAIL_BACKEND)
DEFAULT_CELERY_EMAIL_BACKEND = \
    'django.core.mail.backends.filebased.EmailBackend' if DEBUG else 'django.core.mail.backends.smtp.EmailBackend'
CELERY_EMAIL_BACKEND = env.str('CELERY_EMAIL_BACKEND', DEFAULT_CELERY_EMAIL_BACKEND)

# smtp.EmailBackend
EMAIL_HOST = env.str('EMAIL_HOST', 'localhost')
EMAIL_HOST_PASSWORD = env.str('EMAIL_HOST_PASSWORD', '')
EMAIL_HOST_USER = env.str('EMAIL_HOST_USER', '')
EMAIL_PORT = env.int('EMAIL_PORT', 25)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', False)
EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL', False)
EMAIL_TIMEOUT = env.int('EMAIL_TIMEOUT', None)

# filebased.EmailBackend
EMAIL_FILE_PATH = env.str('EMAIL_FILE_PATH', '/tmp/app-messages')


# Celery
CELERY_BROKER_URL = env.str('CELERY_BROKER_URL', 'redis://localhost/0')
CELERY_RESULT_BACKEND = env.str('CELERY_RESULT_BACKEND', 'redis://localhost/0')


# Axes
AXES_ENABLED = env.bool('LOGIN_PROTECTION_ENABLED', True)
AXES_FAILURE_LIMIT = env.int('LOGIN_PROTECTION_FAILURE_LIMIT', 3)
AXES_LOCKOUT_TEMPLATE = 'accounts/errors/account_is_locked.html'


# Webpack loader
DEFAULT_WEBPACK_STATS_FILE = ROOT_DIR / 'webpack-dev-stats.json' if DEBUG else BASE_DIR / 'webpack-stats.json'
WEBPACK_STATS_FILE = env.str('WEBPACK_STATS_FILE', DEFAULT_WEBPACK_STATS_FILE)
WEBPACK_LOADER = {
  'DEFAULT': {
    'BUNDLE_DIR_NAME': 'bundles/',
    'STATS_FILE': WEBPACK_STATS_FILE,
    'POLL_INTERVAL': 0.3,
    'IGNORE': [r'.+\.hot-update.js', r'.+\.map'],
  }
}
DEFAULT_WEBPACK_ASSETS_DIR = ROOT_DIR / 'web_dev_assets' if DEBUG else BASE_DIR / 'web_assets'
WEBPACK_ASSETS_DIR = env.str('WEBPACK_ASSETS_DIR', DEFAULT_WEBPACK_ASSETS_DIR)

# Rest framework api
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'polyfile.app.utils.handlers.api_exception_handler',
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

WSGI_APPLICATION = 'polyfile.app.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases
DEFAULT_DATABASE = 'sqlite:///{}'.format(Path.cwd() / 'db.sqlite3')
DATABASES = {
    'default': env.db('DATABASE_URL', DEFAULT_DATABASE),
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

STATIC_URL = env.str('STATIC_URL', '/static/')
MEDIA_URL = '/media/'
STATICFILES_DIRS = (
    WEBPACK_ASSETS_DIR,
)
STATIC_ROOT = env.str('STATIC_ROOT', Path.cwd() / 'collected_static')
GUNICORN_BIND = env.str('GUNICORN_BIND', 'unix:/tmp/gunicorn.sock')
NGINX_MAX_BODY_SIZE = env.str('NGINX_MAX_BODY_SIZE', '100m')
NGINX_PROXY_PASS = env.str('NGINX_PROXY_PASS', 'http://{}'.format(GUNICORN_BIND))

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Debug toolbar
ENABLE_DEBUG_TOOLBAR = env.bool('ENABLE_DEBUG_TOOLBAR', DEBUG and not TESTING)
if ENABLE_DEBUG_TOOLBAR:
    try:
        import debug_toolbar
        print(f'Using debug_toolbar version {debug_toolbar.VERSION}')
    except ImportError:
        ENABLE_DEBUG_TOOLBAR = False
    else:
        INSTALLED_APPS.append('debug_toolbar')
        MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_COLLAPSED': True,
}

if TESTING:
    WEBPACK_LOADER = {
        'DEFAULT': {
            'CACHE': False,
            'LOADER_CLASS': 'webpack_loader.loader.FakeWebpackLoader',
        },
    }

if TESTING or DISABLE_CACHE:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'CRITICAL' if TESTING else 'INFO',
        },
    }
}
