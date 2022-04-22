import factory
from factory.django import DjangoModelFactory

from accounts.models import User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker('user_name')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.pop('password', None)
        instance = super()._create(model_class, *args, **kwargs)
        if password is not None:
            instance.set_password(password)
            instance.save(update_fields=['password'])
        return instance
