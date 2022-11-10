import re
from datetime import timedelta
from io import StringIO

from django.conf import settings
from django.contrib import auth
from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now
from flake8.api import legacy as flake8
from rest_framework import status

from accounts.factories import UserFactory
from accounts.models import ResetPasswordAttempt


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


class TestAccounts(TestCase):
    """Test login and logout, password reset and so on"""
    def setUp(self) -> None:
        self.password = 'foobar'
        self.user = UserFactory(password=self.password, email='foo@example.com')
        mail.outbox = []

    def _get_url_from_email(self, message: str):
        regex = r'(\/accounts\/reset_password\/[\w\/\-]+)'
        match = re.search(regex, message)
        self.assertIsNotNone(match)
        return match.groups()[0]

    def test_user_login(self):
        """Ensure we can log in."""
        url = reverse('accounts-login')
        data = {'username': self.user.username, 'password': self.password}

        # login form
        response = self.client.get(url, follow=False)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.context.get('form'))

        # send login form
        response = self.client.post(url, data, follow=False)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.headers['Location'], '/')
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        # already authenticated
        response = self.client.get(url, follow=False)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('username' in response.context)

    def test_user_reset_password(self):
        url = reverse('password_reset')
        data_reset_password = {'email': self.user.email}
        data_new_password = {'new_password1': 'TestFooBar166', 'new_password2': 'TestFooBar166'}

        # login form
        response = self.client.get(url, follow=False)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.context.get('form'))

        # send login form
        # invalid data
        response = self.client.post(url, {}, follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.context.get('form'))
        self.assertTrue(len(response.context.get('form').errors))

        # valid data
        response = self.client.post(url, data_reset_password)
        url = reverse('password_reset_done')
        self.assertRedirects(response, url)

        # "Message sent" page
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.context.get('form'))
        self.assertEqual(len(mail.outbox), 1)

        # Url from message
        url = self._get_url_from_email(str(mail.outbox[0].message()))

        # Navigate to link from message
        response = self.client.get(url)
        url = reverse('password_reset_confirm', args=['MQ', 'set-password'])
        self.assertRedirects(response, url)
        response = self.client.get(url)
        self.assertIsNotNone(response.context.get('form'))

        # Send new password data
        response = self.client.post(url, data_new_password)
        url = reverse('password_reset_complete')
        self.assertRedirects(response, url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_reset_password_max_attempts(self):
        """Ensure we do not send too many emails."""
        url = reverse('password_reset')
        data_reset_password = {'email': self.user.email}

        # send reset form
        response = self.client.post(url, data_reset_password)
        r_url = reverse('password_reset_done')
        self.assertRedirects(response, r_url)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(ResetPasswordAttempt.objects.count(), 1)

        # send again form
        response = self.client.post(url, data_reset_password)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(ResetPasswordAttempt.objects.count(), 1)

        # make attempts older
        ResetPasswordAttempt.objects.all().update(
            expire_date=now() - timedelta(seconds=settings.PASSWORD_RESET_FORM_TIMEOUT)
        )
        response = self.client.post(url, data_reset_password)
        self.assertRedirects(response, r_url)
        self.assertEqual(len(mail.outbox), 2)
