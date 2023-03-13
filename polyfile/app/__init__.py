from .celery import app as celery_app
from . import checks  # noqa

__all__ = ('celery_app',)
