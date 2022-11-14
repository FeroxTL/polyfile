from io import StringIO

from django.core.management import call_command, CommandError
from django.test import TestCase, override_settings


class GenConfigTest(TestCase):
    maxDiff = None

    @override_settings(STATIC_ROOT=None)
    def test_gen_nginx_config(self):
        with self.assertRaises(CommandError):
            call_command('gen_config')

        with self.assertRaises(CommandError):
            call_command('gen_config', 'nginx')

        result1 = StringIO()
        with override_settings(STATIC_ROOT='/tmp/'):
            call_command('gen_config', 'nginx', stdout=result1)
        result1.seek(0)
        self.assertTrue(len(result1.read()) > 100)

    def test_gen_gunicorn_config(self):
        result1 = StringIO()
        call_command('gen_config', 'gunicorn', stdout=result1)
        result1.seek(0)
        self.assertTrue(len(result1.read()) > 100)
