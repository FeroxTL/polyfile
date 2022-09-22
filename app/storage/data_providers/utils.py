import typing

from storage.data_providers.base import BaseProvider, provider_registry


def get_data_provider_class(data_provider_id) -> typing.Type[BaseProvider]:
    return provider_registry.get_provider(data_provider_id)
