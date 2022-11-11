# File storge project
## Purpose
* Store files in centralized project
* Web/application access to files
* Different backend storages (disk, s3, etc..)
* Share/public upload directories

## Status
Deep alpha version.

## Running project
### Global requirements:
```
python 3.6+
pillow
nodejs 12+
```

### Installing and running:

#### Dependencies
`Pillow` is imaging library. Can be installed via package
(`apt install python3-pil` in ubuntu/debian) or
pip (`pip install Pillow`, but it requires `python3-dev`).
See https://pillow.readthedocs.io/en/stable/installation.html for details

##### Backend:
```
# Setting up environment, run in project root directory
python3 -m venv ./env --system-site-packages
source ./env/bin/activate
pip install -r requirements.txt

cd app

# Create super user
python ./manage.py createsuperuser

# Running dev server
python ./manage.py runserver

# Running background celery worker
celery -A app worker -l INFO
```

##### Frontend:
```
# Setting up environment, run in frontend directory
cd frontend
npm install

# running dev build
npm run watch
```


# Testing
```
# Set up environment
pip install -r dev-requirements.txt

# Running tests
make test

# Coverage
make coverage
```


# Setting up environment

Pass desired values in environment or create a .env file in project root directory.

* `DEBUG` (`True`) -- set `False` on production
* `ENVFILE` (`BASEDIR / .env`) -- Mostly used in development environment -- the env file to load
* `SECRET_KEY` (`django-insecure`) -- set to unique string on production, do not use default value
* `ALLOWED_HOSTS` (`[]`) -- list of allowed hosts, set your host for production
* `INTERNAL_IPS` (`[127.0.0.1]`) -- internal ips for development (DEBUG_TOOLBAR)
* `PASSWORD_RESET_FORM_TIMEOUT` (in seconds, 3 days) -- When reset password form can be submitted again for user
* `EMAIL_BACKEND` (`filebased.EmailBackend` if DEBUG else `CeleryEmailBackend`)  -- do not change if not necessary
* `CELERY_EMAIL_BACKEND` (`filebased.EmailBackend` if DEBUG else `smtp.EmailBackend`) -- do not change if not necessary
* `EMAIL_FILE_PATH` (`/tmp/app-messages`) -- default directory for `filebased.EmailBackend`. Only for development
* `EMAIL_HOST` (`localhost`) -- The host to use for sending email
* `EMAIL_HOST_PASSWORD` (`''` (empty string)) -- Password to use for the SMTP server
* `EMAIL_HOST_USER` (`''` (empty string)) -- Username to use for the SMTP server
* `EMAIL_PORT` (`25`) -- Port to use for the SMTP server
* `EMAIL_USE_TLS` (`False`) -- Whether to use a TLS (secure) connection when talking to the SMTP server
* `EMAIL_USE_SSL` (`False`) -- Whether to use an implicit TLS (secure) connection when talking to the SMTP server
* `EMAIL_TIMEOUT` (`None`) -- Specifies a timeout in seconds for blocking operations like the connection attempt
* `CELERY_BROKER_URL` (`redis://localhost/0`) -- Celery broker url
* `CELERY_RESULT_BACKEND` (`redis://localhost/0`) -- Celery result backend url
* `LOGIN_PROTECTION_ENABLED` (`True`) -- Login protection. Incorrect attempts are logged and user is banned by ip
* `LOGIN_PROTECTION_FAILURE_LIMIT` (3) -- Number of failed
* `DATABASE_URL` (`'sqlite:///polyfile/db.sqlite3'`) -- Database URL
* `STATIC_URL` (`'/static/'`) -- URL to use when referring to static files located in STATIC_ROOT.
* `STATIC_ROOT` (`None`) -- The absolute path to the directory where collectstatic will collect static files for deployment.
  Example: `/var/www/example.com/static/`
* `ENABLE_DEBUG_TOOLBAR` (DEBUG) -- Enable Debug Toolbar, always enabled in DEBUG mode
