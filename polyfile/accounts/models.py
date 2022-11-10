from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext as _


class User(AbstractUser):
    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip() or self.username


def default_reset_expire_date():
    return now() + timedelta(seconds=settings.PASSWORD_RESET_FORM_TIMEOUT)


class ResetPasswordAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    attempt_date = models.DateTimeField(_('Attempt date'), auto_now_add=True)
    expire_date = models.DateTimeField(_('Expire date'), default=default_reset_expire_date)

    objects = models.Manager()
