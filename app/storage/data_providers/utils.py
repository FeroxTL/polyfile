from storage.data_providers.base import BaseProvider, provider_register
from storage.models import DataSourceOption, DataLibrary


def get_data_provider(library: DataLibrary) -> BaseProvider:
    options = dict(DataSourceOption.objects.filter(data_source=library.data_source).values_list('key', 'value'))
    return provider_register.get_provider(library.data_source.data_provider_id)(library=library, options=options)
