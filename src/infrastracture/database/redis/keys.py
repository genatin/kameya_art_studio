from typing import Any

from .key_builder import StorageKey


class UserKey(StorageKey, prefix="users"):
    key: Any
