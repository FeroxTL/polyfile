import json
import tempfile
from functools import wraps
from pathlib import Path

from django.core.files.storage import Storage, FileSystemStorage
from django.test import TestCase
from rest_framework.fields import DateTimeField

from polyfile.accounts.factories import SuperuserFactory
from polyfile.storage.base_data_provider import BaseProvider, provider_registry


def drf_dt(dt) -> str:
    return DateTimeField().to_representation(dt)


def with_tempdir(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        with tempfile.TemporaryDirectory() as temp_dir:
            return f(*args, temp_dir, **kwargs)
    return wrapper


class TestProvider(BaseProvider):
    provider_id = 'test_provider'
    verbose_name = 'Test provider'

    def get_storage(self) -> Storage:
        assert 'location' in self.options
        root_dir = Path(self.options['location'])
        return FileSystemStorage(location=root_dir)


provider_registry.register(TestProvider)


class AdminTestCase(TestCase):
    def setUp(self) -> None:
        self.user = SuperuserFactory()
        self.client.force_login(self.user, backend='django.contrib.auth.backends.ModelBackend')

    @staticmethod
    def get_options(options: dict):
        return json.dumps(options)
