import typing

from django.db import models


def get_field(model: typing.Type[models.Model], name: str):
    return getattr(model, '_meta').get_field(name)
