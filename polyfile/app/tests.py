from io import StringIO
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from flake8.api import legacy as flake8
from pydocstyle import check


class TestAnimal(TestCase):
    maxDiff = None

    def test_pep8(self):
        style_guide = flake8.get_style_guide(
            exclude=['migrations'],
            max_line_length=120,
            verbose=True
        )
        file_list = [
            settings.BASE_DIR / path
            for path in ['', '__main__.py']
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

    def test_pydocstyle(self):
        file_list = []
        exclude_names = ['__init__.py', 'gunicorn.conf.py', 'admin.py', 'apps.py', 'factories.py', 'tests.py']
        pep_ignore = {
            'D204',
            'D203',
            'D100',
            'D106',  # Meta classes
            'D212',  # Multi-line docstring summary should start at the first line
            'D105',  # Missing docstring in magic method
            'D107',  # Missing docstring in __init__
        }

        for file in settings.BASE_DIR.rglob('*.py'):
            if file.name not in exclude_names and 'migrations' not in str(file):
                file_list.append(str(file.relative_to(Path.cwd())))

        check_result = list(check(file_list, ignore=pep_ignore))
        self.assertListEqual(check_result, [])
