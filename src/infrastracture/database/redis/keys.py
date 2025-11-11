from typing import Any

from .key_builder import StorageKey


class UserKey(StorageKey, prefix='users'):
    key: Any


class AdminKey(StorageKey, prefix='admin'):
    key: Any


class ActivityKey(StorageKey, prefix='activity'):
    key: Any


class AdminGetSingUps(StorageKey, prefix='signups'):
    key: Any


class BaseMenuImage(StorageKey, prefix='base_menu_image'):
    key: Any
