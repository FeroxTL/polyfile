from django.core.exceptions import SuspiciousFileOperation, ValidationError


class ProviderException(SuspiciousFileOperation):
    pass


class ProviderOptionError(ValidationError):
    pass
