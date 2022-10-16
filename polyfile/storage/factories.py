import typing

import factory
from factory import fuzzy
from factory.django import DjangoModelFactory

from accounts.factories import UserFactory
from app.utils.tests import TestProvider
from storage.models import DataSource, DataLibrary, Mimetype, Node, DataSourceOption


class DataSourceOptionFactory(DjangoModelFactory):
    class Meta:
        model = DataSourceOption


class DataSourceFactory(DjangoModelFactory):
    class Meta:
        model = DataSource

    data_provider_id = TestProvider.provider_id

    @factory.post_generation
    def options(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for key, value in extracted.items():
                DataSourceOptionFactory(data_source=self, key=key, value=value)


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


class DirectoryFactory(FileFactory):
    file_type = Node.FileTypeChoices.DIRECTORY
    mimetype = None
    size = 0


class DataLibraryFactory(DjangoModelFactory):
    class Meta:
        model = DataLibrary

    name = factory.Faker('file_name')
    owner = factory.SubFactory(UserFactory)
    data_source = factory.SubFactory(DataSourceFactory)