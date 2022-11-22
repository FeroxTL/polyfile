from rest_framework import exceptions
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    """
    Handle api exception.

    Always return list instead of {detail: ...} dict
    """
    if isinstance(exc, exceptions.APIException) and not isinstance(exc.detail, (list, dict)):
        exc.detail = [exc.detail]

    return exception_handler(exc, context)
