from django.core.exceptions import SuspiciousFileOperation


class ProviderException(SuspiciousFileOperation):
    pass
