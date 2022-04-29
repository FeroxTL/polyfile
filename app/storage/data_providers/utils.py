import typing

from storage.data_providers.base import BaseProvider, provider_registry
from storage.models import DataSourceOption, DataLibrary


def get_data_provider_class(data_provider_id) -> typing.Type[BaseProvider]:
    return provider_registry.get_provider(data_provider_id)


def get_data_provider(library: DataLibrary) -> BaseProvider:
    provider_class = get_data_provider_class(library.data_source.data_provider_id)
    options = dict(DataSourceOption.objects.filter(data_source=library.data_source).values_list('key', 'value'))
    return provider_class(library=library, options=options)
