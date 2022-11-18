from django.core.cache import cache
from django.db import models


class CacheManager(models.Manager):
    def __init__(self, cache_fields=None, cache_time=300, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache_fields = cache_fields or ['pk']
        self.cache_time = cache_time

    def _get_cache_key(self, pk):
        return '{}:{}'.format(self.model.__name__, pk)

    def _get_cache_value(self, kwargs: dict):
        if len(kwargs) != 1:
            return

        for key in self.cache_fields:
            if key in kwargs:
                return kwargs[key]

    def get(self, *args, **kwargs):
        pk = self._get_cache_value(kwargs)
        key = self._get_cache_key(pk)

        if pk is None:
            return super().get(*args, **kwargs)

        instance = cache.get(key)
        if not instance:
            instance = super().get(*args, **kwargs)
            cache.set(key, instance, self.cache_time)

        return instance

    def get_or_create(self, *args, **kwargs):
        pk = self._get_cache_value(kwargs)
        key = self._get_cache_key(pk)

        if pk is None:
            return super().get_or_create(*args, **kwargs)

        instance, created = cache.get(key), False
        if instance is None:
            instance, created = super().get_or_create(*args, **kwargs)
            cache.set(key, instance, self.cache_time)
        return instance, created

    def invalidate_cache_instance(self, pk):
        key = self._get_cache_key(pk)
        cache.delete(key)
