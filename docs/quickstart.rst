Quickstart
===========

See :doc:`installation` for dependencies


Loading settings
------------------------------

You can pass settings using environment variables, for example

.. code-block:: console

    (.venv)$ DEBUG=False SECRET_KEY=foo_bar_baz ./manage.py runserver


You can also make :code:`.env` file in root project directory:

.. code-block:: text

    DEBUG=False
    SECRET_KEY=foo_bar_baz

.. code-block:: console

    (.venv)$ source .env
    (.venv)$ ./manage.py runserver


:code:`.env` file in root directory is loaded by :code:`./manage.py` automatically


Settings
------------------------------

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
    :default: None

    The absolute path to the directory where :code:`collectstatic` will collect static files for deployment.
    Example: `/var/www/example.com/static/`

..  confval:: ENABLE_DEBUG_TOOLBAR
    :type: bool
    :default: DEBUG

    Enable Debug Toolbar, always enabled in DEBUG mode


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
    (.venv)$ make test TEST=app.tests.TestAccounts
    (.venv)$ make coverage
