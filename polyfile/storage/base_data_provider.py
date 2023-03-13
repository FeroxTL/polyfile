import typing
from abc import abstractmethod, ABC

from django.core.exceptions import ValidationError
from django.core.files.storage import Storage
from django.forms import forms
from django.utils.timezone import now

if typing.TYPE_CHECKING:
    from polyfile.storage.models import Node, DataLibrary, AbstractNode


class BaseProvider(ABC):
    """Base class for all data providers."""
    validation_class: forms.Form = forms.Form

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Return some unique identifier."""
        pass

    @property
    @abstractmethod
    def verbose_name(self) -> str:
        """Return public name."""
        pass

    @abstractmethod
    def get_storage(self) -> Storage:
        """Return an instance of storage."""
        pass

    def __init__(self, options: dict, node: typing.Optional['Node'] = None):
        super().__init__()
        self.options = options
        self.node = node
        self.storage = self.get_storage()

    def __str__(self):
        return self.verbose_name

    def init_library(self, library: 'DataLibrary'):
        """Initialize DataLibrary."""
        pass

    @staticmethod
    def get_upload_to(instance: 'AbstractNode', filename: str) -> str:
        """Target upload path."""
        if instance.is_node_cls():
            path = 'lib_{lib_id}/{dt}/{filename}'
        else:
            path = 'lib_{lib_id}/alt/{dt}/{filename}'
        return path.format(
            lib_id=instance.data_library_id,
            dt=now().strftime('%Y.%m'),
            filename=filename,
        )

    @classmethod
    def transform_options(cls, options: dict):
        """Transform options from k:v of strings to required types."""
        form = cls.validation_class(data=options)
        if not form.is_valid():
            raise ValidationError(form.errors)
        return form.cleaned_data


class ProviderRegister:
    """Stores all providers in one place."""
    TypeBaseProvider = typing.Type[BaseProvider]

    def __init__(self):
        self._registry = {}

    def has_provider(self, provider_id: str):
        """Check if register has provider."""
        return provider_id in self._registry

    def register(self, provider: TypeBaseProvider):
        """Register provider in register."""
        self._registry[provider.provider_id] = provider

    def get_provider(self, provider_id: str) -> TypeBaseProvider:
        """Retrieve provider."""
        return self._registry[provider_id]

    @property
    def providers(self) -> typing.Iterable[TypeBaseProvider]:
        """Return all registered data providers."""
        return self._registry.values()


provider_registry = ProviderRegister()
