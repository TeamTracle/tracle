import requests
import os

from django.conf import settings
from django.core.files.base import File
from django.core.files.storage import FileSystemStorage, Storage
from django.utils.module_loading import import_string
from django.utils.deconstruct import deconstructible
from django.utils.functional import SimpleLazyObject, cached_property
from django.core.cache import cache

from bunnycdn_storage import bunnycdn_storage


class LazyBackend(SimpleLazyObject):

    def __init__(self, import_path, options):
        backend = import_string(import_path)
        super().__init__(lambda: backend(**options))


@deconstructible
class WrappedStorage(object):

    local = None
    local_options = None
    remote = None
    remote_options = None

    def __init__(self, local=None, remote=None, local_options=None, remote_options=None, cache_prefix='ws'):
        self.local_path = local or self.local
        self.local_options = local_options or self.local_options or {}
        self.local = self._load_backend(self.local_path, self.local_options)

        self.remote_path = remote or self.remote
        self.remote_options = remote_options or self.remote_options or {}
        self.remote = self._load_backend(self.remote_path, self.remote_options)

        self.cache_prefix = cache_prefix

    def _load_backend(self, backend, options):
        return LazyBackend(backend, options)

    def get_storage(self, name):
        cache_result = cache.get(self.get_cache_key(name))
        if cache_result:
            return self.remote
        elif cache_result is None and self.remote.exists(name):
            cache.set(self.get_cache_key(name), True)
            return self.remote
        else:
            return self.local

    def get_cache_key(self, name):
        return f'{self.cache_prefix}_{name}'

    def using_local(self, name):
        return self.get_storage(name) is self.local

    def using_remote(self, name):
        return self.get_storage(name) is self.remote

    def open(self, name, mode='rb'):
        return self.get_storage(name).open(name, mode)

    def save(self, name, content, max_length=None):
        cache_key = self.get_cache_key(name)
        cache.set(cache_key, False)

        name = self.get_available_name(name)
        name = self.local.save(name, content, max_length=max_length)
        return name

    def transfer(self, name, cache_key=None):
        if cache_key is None:
            cache_key = self.get_cache_key(name)
        local_path = self.local.path(name)
        self.remote.transfer(local_path, name)
        cache.set(cache_key, True)

    def get_valid_name(self, name):
        return self.get_storage(name).get_valid_name(name)

    def get_available_name(self, name):
        local_available_name = self.local.get_available_name(name)
        remote_available_name = self.remote.get_available_name(name)

        if remote_available_name > local_available_name:
            return remote_available_name
        return local_available_name

    def path(self, name):
        return self.get_storage(name).path(name)

    def delete(self, name):
        # self.get_storage(name).delete(name)
        self.local.delete(name)
        self.remote.delete(name)
        if self.using_remote(name):
            cache.set(self.get_cache_key(name), False)

    def exists(self, name):
        return self.get_storage(name).exists(name)

    def listdir(self, name):
        return self.get_storage(name).listdir(name)

    def size(self, name):
        return self.get_storage(name).size(name)

    def url(self, name):
        return self.get_storage(name).url(name)

    def generate_filename(self, filename):
        return self.get_storage(filename).generate_filename(filename)

@deconstructible
class WrappedFileSystemStorage(WrappedStorage):
    def __init__(self, local='backend.storage.CustomFileSystemStorage', *args, **kwargs):
        super().__init__(local=local, *args, **kwargs)

@deconstructible
class WrappedBCDNStorage(WrappedFileSystemStorage):
    def __init__(self, remote='backend.storage.BCDNStorage', *args, **kwargs):
        super().__init__(remote=remote, *args, **kwargs)

class CustomFileSystemStorage(FileSystemStorage):
    @cached_property
    def location(self):
        if callable(self._location):
            return os.path.abspath(self._location())
        else:
            return os.path.abspath(self.base_location)

@deconstructible
class BCDNStorage(Storage):
    def __init__(self, storage_zone_name=None, access_token=None, account_token=None, pullzone_url=None, debug=False):
        self._access_token = access_token if access_token else settings.BUNNYCDN.get('access_token')
        self._storage_zone_name = storage_zone_name if storage_zone_name else settings.BUNNYCDN.get('storage_zone_name')
        self._account_token = account_token if account_token else settings.BUNNYCDN.get('account_token')
        self._pullzone_url = pullzone_url if pullzone_url else settings.BUNNYCDN.get('pullzone_url')
        self._DEBUG = debug if debug else settings.BUNNYCDN.get('debug')
        self._bcdn = bunnycdn_storage.BunnyCDNStorage(self._storage_zone_name, self._access_token, self._pullzone_url, self._account_token, debug=debug)

    def _open(self, name, mode='rb'):
        pass

    def get_available_name(self, name):
        return name

    def transfer(self, full_path, name):
        self._bcdn.upload_file(full_path, name)

    def delete(self, name):
        try:
            self._bcdn.delete_object(name)
        except requests.exceptions.HTTPError as e:
            print(e)

    def exists(self, name):
        return self._bcdn.object_exists(name)

    def url(self, name):
        return '{}{}'.format(self._pullzone_url, name)

    def listdir(self, name):
        return self._bcdn.get_storage_objects(name)

