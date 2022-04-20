from storage.data_providers.base import BaseProvider, provider_register
from storage.models import DataSource, DataSourceOption


def get_data_provider(data_source: DataSource) -> BaseProvider:
    options = dict(DataSourceOption.objects.filter(data_source=data_source).values_list('key', 'value'))
    return provider_register.get_provider(data_source.data_provider_id)(options)
