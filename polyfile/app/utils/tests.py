import json
import tempfile
from functools import wraps
from pathlib import Path

from django.core.files.storage import Storage, FileSystemStorage
from django.test import TestCase
from rest_framework.fields import DateTimeField
from webpack_loader.loader import WebpackLoader

from accounts.factories import SuperuserFactory
from storage.base_data_provider import BaseProvider, provider_registry


def drf_dt(dt) -> str:
    return DateTimeField().to_representation(dt)


class TestWebpackLoader(WebpackLoader):
    def get_bundle(self, bundle_name):
        """
        Return a non-existent JS bundle for each one requested.

        Django webpack loader expects a bundle to exist for each one
        that is requested via the 'render_bundle' template tag. Since we
        don't want to store generated bundles in our repo, we need to
        override this so that the template tags will still resolve to
        something when we're running tests.

        The name and URL here don't matter, this file doesn't need to exist.
        """
        return [{'name': bundle_name, 'url': '{}.js'.format(bundle_name)}]


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
