===================
Installation
===================


Overview
###################

Polyfile is written in Python, it supports Python 3.7 and newer.
We recommend using the latest version of Python.

Dependencies
****************************

These dependencies are required:

* `Python <https://python.org/>`__
* `Pillow <https://pillow.readthedocs.io/>`__ --
  The Python Imaging Library adds image processing capabilities to your Python interpreter
* `Redis <https://redis.io/>`__ -- in-memory data store
* `nodejs 12+ <https://nodejs.org/>`__ -- cross-platform JavaScript runtime environment

These dependencies are optional:

* `python-venv <https://docs.python.org/3/library/venv.html>`__ --
  tool for creating lightweight “virtual environments”, could be usable for development


Linux
###################

Debian/Ubuntu
****************************

Install dependencies

.. code-block:: console

   $ apt install python3 python3-venv redis python3-pil nodejs npm make

todo: this block is upcoming

Installation from source
****************************

You can install Polyfile directly from a clone of the Git repository.
This can be done either by cloning the repo and installing from the local clone, on simply installing directly via git.

.. code-block:: console

    $ git clone https://github.com/FeroxTL/polyfile
    $ cd polyfile
    $ pip install -r requirements.txt

todo: Installation via pip is not ready yet.
