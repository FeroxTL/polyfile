import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'polyfile.app.settings')

app = Celery('polyfile')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
