Quickstart
===========

See :doc:`installation` for installing dependencies


Loading settings
------------------------------

You can pass settings using environment variables, for example

.. code-block:: console

    (.venv)$ DEBUG=False SECRET_KEY=foo_bar_baz ./manage.py runserver


You can also create :code:`.env` file in :code:`BASEDIR` directory:

.. code-block:: text

    DEBUG=False
    SECRET_KEY=foo_bar_baz
    ALLOWED_HOSTS=localhost,example.com

.. code-block:: console

    (.venv)$ source .env
    (.venv)$ ./manage.py runserver


:code:`.env` file in current directory is loaded automatically

.. _settings:

Settings
------------------------------

:code:`BASEDIR` is directory, that contains :code:`manage.py` file

..  confval:: DEBUG
    :type: bool
    :default: True

    Enable debugging tools (debug templates and development server). Never set to True production

..  confval:: SECRET_KEY
    :type: str
    :default: django-insecure

    Set to unique string on production, do not use default value. Keep it secret, do not store in public repositories

..  confval:: ENVFILE
    :type: str
    :default: BASEDIR / .env

    Mostly used in development environment -- the env file to load

..  confval:: ALLOWED_HOSTS
    :type: list
    :default: [localhost]

    List of allowed hosts, set your host for production

..  confval:: INTERNAL_IPS
    :type: list
    :default: [127.0.0.1]

    Internal ips for development (DEBUG_TOOLBAR)

..  confval:: DISABLE_CACHE
    :type: list
    :default: False

    Disable django cache

..  confval:: PASSWORD_RESET_FORM_TIMEOUT
    :type: int
    :default: (3 days)

    When reset password form can be submitted again for user

..  confval:: EMAIL_BACKEND
    :type: str
    :default: :code:`filebased.EmailBackend` if DEBUG else :code:`CeleryEmailBackend`

    Email backend for sending emails. Do not change if not necessary

..  confval:: CELERY_EMAIL_BACKEND
    :type: str
    :default: :code:`filebased.EmailBackend` if DEBUG else :code:`smtp.EmailBackend`

    Email backend for background sending emails. Do not change if not necessary

..  confval:: EMAIL_FILE_PATH
    :type: str
    :default: :code:`/tmp/app-messages`

    Default directory for :code:`filebased.EmailBackend`. Only for development

..  confval:: EMAIL_HOST
    :type: str
    :default: localhost

    The host to use for sending email

..  confval:: EMAIL_HOST_PASSWORD
    :type: str
    :default: :code:`''` (empty string)

    Password to use for the SMTP server

..  confval:: EMAIL_HOST_USER
    :type: str
    :default: :code:`''` (empty string)

    Username to use for the SMTP server

..  confval:: EMAIL_PORT
    :type: int
    :default: 25

    Port to use for the SMTP server

..  confval:: EMAIL_USE_TLS
    :type: bool
    :default: False

    Whether to use a TLS (secure) connection when talking to the SMTP server

..  confval:: EMAIL_USE_SSL
    :type: bool
    :default: False

    Whether to use an implicit TLS (secure) connection when talking to the SMTP server

..  confval:: EMAIL_TIMEOUT
    :type: int
    :default: None

    Specifies a timeout in seconds for blocking operations like the connection attempt

..  confval:: CELERY_BROKER_URL
    :type: str
    :default: redis://localhost/0

    Celery broker url

..  confval:: CELERY_RESULT_BACKEND
    :type: str
    :default: redis://localhost/0

    Celery result backend url

..  confval:: LOGIN_PROTECTION_ENABLED
    :type: bool
    :default: True

    Login protection. Incorrect attempts are logged and user is banned by ip

..  confval:: LOGIN_PROTECTION_FAILURE_LIMIT
    :type: int
    :default: 3

    Number of failed login attempts

..  confval:: DATABASE_URL
    :type: str
    :default: :code:`sqlite:///polyfile/db.sqlite3`

    Database URL

..  confval:: STATIC_URL
    :type: str
    :default: :code:`/static/`

    URL to use when referring to static files located in STATIC_ROOT

..  confval:: STATIC_ROOT
    :type: str
    :default: <cwd> / collected_static

    The absolute path to the directory where :code:`collectstatic` will collect static files for deployment.
    Example: `/var/www/example.com/static/`

..  confval:: ENABLE_DEBUG_TOOLBAR
    :type: bool
    :default: DEBUG

    Enable Debug Toolbar, always enabled in DEBUG mode

..  confval:: GUNICORN_BIND
    :type: str
    :default: unix:/tmp/gunicorn.sock

    Maximum allowed size of the client request body
..  confval:: NGINX_MAX_BODY_SIZE
    :type: str
    :default: 100m

    Maximum allowed size of the client request body

..  confval:: NGINX_PROXY_PASS
    :type: str
    :default: http:// + GUNICORN_BIND

    Protocol and address of a proxied server and an optional URI to which a location should be mapped


Running development server
------------------------------

Virtual environment is helpful for development or while installing from source.

Create a :code:`env` directory within :code:`polyfile` directory, then activate it:

.. code-block:: console

    $ python3 -m venv env --system-site-packages
    $ source env/bin/activate
    (.venv) $ pip install -r requirements.txt


Build dev frontend with nodejs:

.. code-block:: console

    $ cd frontend
    $ npm install
    $ npm run watch


Setup database, run development server and celery worker (optional for development):

.. code-block:: console

    (.venv)$ cd polyfile
    (.venv)$ ./manage.py migrate
    (.venv)$ ./manage.py runserver
    (.venv)$ celery -A app worker -l INFO


Create superuser

.. code-block:: console

    (.venv)$ python ./manage.py createsuperuser


Running tests and coverage
------------------------------

There is requirements file for testing and coverage. Then run test or coverage:

.. code-block:: console

    (.venv)$ pip install -r dev-requirements.txt
    (.venv)$ make test
    (.venv)$ make test TEST=accounts.tests.TestAccounts
    (.venv)$ make coverage


Deploying to production
------------------------------

The recommended way is to use nginx and gunicorn:

.. code-block:: console

    install packages

    # apt install nginx python3-gunicorn

    Generate default configuration for nginx

    (.venv)$ python ./manage.py gen_config nginx > /etc/nginx/conf.d/polyfile.conf
    (.venv)$ systemctl nginx reload


Set :code:`STATIC_ROOT` (for example :code:`/var/www/static/`) setting and collect static files

.. code-block:: console

    (.venv)$ python ./manage.py collectstatic

Set up gunicorn server:

.. code-block:: console

    (.venv)$ python ./manage.py gen_config gunicorn > /var/www/gunicorn.conf.py
    (.venv)$ python3 -m gunicorn --conf=/var/www/gunicorn.conf.py

Navigate to http://localhost
