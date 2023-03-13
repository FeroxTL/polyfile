===================
Installation
===================


Overview
###################

Polyfile is written in Python, it supports Python 3.7 and newer.

Dependencies
****************************

These dependencies are required:

* `Python <https://python.org/>`__
* `Pillow <https://pillow.readthedocs.io/>`__ --
  The Python Imaging Library adds image processing capabilities to your Python interpreter
* `Redis <https://redis.io/>`__ -- in-memory data store
* `nodejs 12+ <https://nodejs.org/>`__ -- cross-platform JavaScript runtime environment (only for frontend development)
* `Pip <https://packaging.python.org/en/latest/key_projects/#pip>`__ --
  tool for installing Python packages
* `Venv <https://docs.python.org/3/library/venv.html>`__ --
  tool for creating lightweight “virtual environments”, could be usable for development
* `Nginx <https://nginx.org/>`__ -- TCP/UDP proxy server


Linux
###################

Python packages (examples for Debian/Ubuntu)
********************************************

Install dependencies

.. code-block:: console

    $ apt install python3 python3-pip redis python3-pil nginx

Create separate user

.. code-block:: console

    # useradd polyfile --home-dir /var/www/polyfile
    # mkdir /var/www/polyfile -p
    # chown polyfile:polyfile /var/www/polyfile

Next command should be executed under `polyfile` user:

.. code-block:: console

    # su - polyfile
    $ pip install polyfile.tar.gz
    $ python3 -m polyfile check  # checks if everything is ok

todo: Installation via pip is not ready yet.

Create `.env` file and setup it according :ref:`settings`

Run following commands to prepare environment:

.. code-block:: console

    $ python3 -m polyfile migrate  # Migrate database
    $ python3 -m polyfile createsuperuser  # Create superuser for yourself
    $ python3 -m polyfile gen_config gunicorn > ./gunicorn.conf.py  # Generate gunicorn config
    $ python3 -m polyfile gen_config nginx > ./polyfile.conf  # Generate nginx config
    $ python3 -m polyfile collectstatic  # Collect static files
    $ python3 -m gunicorn --config ./gunicorn.conf.py  # Run gunicorn server just for test -- this must run in background

You can leave this running for testing, we need to setup nginx. Login as root user:

.. code-block:: console

    $ mv /var/www/polyfile/polyfile.conf /etc/nginx/conf.d/  # Tell nginx that we have new site here
    $ systemctl reload nginx.service  # reload nginx configuration

That's it -- now open http://localhost and polyfile must be there

Installation from source
****************************

You can install Polyfile directly from a clone of the Git repository.
This can be done either by cloning the repo and installing from the local clone, on simply installing directly via git.

.. code-block:: console

    $ apt install python3 redis python3-pil nodejs npm make nginx
    $ git clone https://github.com/FeroxTL/polyfile
    $ cd polyfile

Create virtual env and setup requirements

.. code-block:: console

    $ python3 -m venv ./env --system-site-packages
    $ source ./env/bin/activate
    $ pip install -r requirements.txt

Setup `.env` file (see :ref:`settings`)

Migrate database

.. code-block:: console

    $ ./manage.py migrate

Build frontend (only for development):

.. code-block:: console

    $ cd frontend
    $ make build_dev

Run development server:

.. code-block:: console

    $ ./manage.py runserver
