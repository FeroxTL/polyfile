import typing

import factory
from factory import fuzzy
from factory.django import DjangoModelFactory

from accounts.factories import UserFactory
from app.utils.tests import TestProvider
from storage.models import DataSource, DataLibrary, Mimetype, Node, AltNode


class DataSourceFactory(DjangoModelFactory):
    class Meta:
        model = DataSource

    data_provider_id = TestProvider.provider_id


class MimeTypeFactory(DjangoModelFactory):
    class Meta:
        model = Mimetype
        django_get_or_create = ('name',)

    name = factory.Faker('mime_type')


class FileFactory(DjangoModelFactory):
    class Meta:
        model = Node

    name = factory.Faker('file_name')
    size = fuzzy.FuzzyInteger(0, 15000)
    file_type = Node.FileTypeChoices.FILE
    mimetype = factory.SubFactory(MimeTypeFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        parent: typing.Optional[Node] = kwargs.pop('parent', None)
        if parent is not None:
            kwargs.setdefault('data_library', parent.data_library)
            return Node.objects.create(parent=parent, **kwargs)

        return Node.objects.create(**kwargs)


class ImageFactory(FileFactory):
    name = factory.Faker('file_name', category='image')
    mimetype__name = factory.Faker('mime_type', category='image')


class DirectoryFactory(FileFactory):
    file_type = Node.FileTypeChoices.DIRECTORY
    mimetype = None
    size = 0


class AltNodeFactory(DjangoModelFactory):
    class Meta:
        model = AltNode

    node = factory.SubFactory(
        ImageFactory,
        data_library=factory.SelfAttribute('..data_library')
    )
    version = factory.Sequence(lambda n: '{0}x{0}'.format(n))


class DataLibraryFactory(DjangoModelFactory):
    class Meta:
        model = DataLibrary

    name = factory.Faker('file_name')
    owner = factory.SubFactory(UserFactory)
    data_source = factory.SubFactory(DataSourceFactory)
