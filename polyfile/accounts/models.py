from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.timezone import now
from django.utils.translation import gettext as _

from app.utils.managers import CacheManager


class UserManager(CacheManager, DjangoUserManager):
    pass


class User(AbstractUser):
    objects = UserManager()

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip() or self.username


@receiver([post_save, post_delete], sender=User)
def save_profile(instance, **kwargs):
    User.objects.invalidate_cache_instance(instance.pk)


def default_reset_expire_date():
    return now() + timedelta(seconds=settings.PASSWORD_RESET_FORM_TIMEOUT)


class ResetPasswordAttempt(models.Model):
    id = models.BigAutoField(primary_key=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    attempt_date = models.DateTimeField(_('Attempt date'), auto_now_add=True)
    expire_date = models.DateTimeField(_('Expire date'), default=default_reset_expire_date, db_index=True)

    objects = models.Manager()
