from io import StringIO

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase

from flake8.api import legacy as flake8


class TestAnimal(TestCase):
    def test_pep8(self):
        style_guide = flake8.get_style_guide(
            exclude=['migrations'],
            max_line_length=120,
            verbose=True
        )
        file_list = [
            settings.BASE_DIR / path
            for path in ['', 'manage.py']
        ]
        for file in file_list:
            self.assertTrue(file.exists(), f'Path {file} does not exist')

        report = style_guide.check_files(list(map(str, file_list)))
        self.assertEqual(report.total_errors, 0)

    def test_new_migrations(self):
        out = StringIO()
        call_command('makemigrations', '--dry-run', '-v3', stdout=out)
        self.assertIn(
            'No changes detected\n',
            out.getvalue(),
            'Found not created migrations: \n{}'.format(out.getvalue()))
