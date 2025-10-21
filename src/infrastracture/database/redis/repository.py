from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

from pydantic import BaseModel, TypeAdapter
from redis.asyncio import Redis
from redis.typing import ExpiryT

from src.application.models import UserDTO
from src.application.utils import mjson
from src.infrastracture.database.redis.key_builder import StorageKey
from src.infrastracture.database.redis.keys import UserKey

T = TypeVar('T', bound=Any)

_MINUTE = 60
_HOUR = _MINUTE * 60
_DAY = _HOUR * 24
_MONTH = _DAY * 30


def auto_pack_key_async(func: Callable[..., T]) -> Callable[..., T]:
    @wraps(func)
    async def wrapper(self, key: StorageKey | str, *args: Any, **kwargs: Any) -> T:
        processed_key = key.pack() if isinstance(key, StorageKey) else key
        return await func(self, processed_key, *args, **kwargs)

    return cast(Callable[..., T], wrapper)


class RedisRepository:
    def __init__(self, client: Redis) -> None:
        self.client = client

    @auto_pack_key_async
    async def get(self, key: StorageKey | str, validator: type[T]) -> T | None:
        value: Any | None = await self.client.get(key)
        if value is None:
            return None
        value = mjson.decode(value)
        return TypeAdapter[T](validator).validate_python(value)

    async def hgetall(self, key: str) -> dict:
        return await self.client.hgetall(key)

    @auto_pack_key_async
    async def getdel(self, key: StorageKey | str, validator: type[T]) -> Any:
        value: Any | None = await self.client.getdel(key)
        if value is None:
            return None
        value = mjson.decode(value)
        return TypeAdapter[T](validator).validate_python(value)

    @auto_pack_key_async
    async def rpush(self, key: StorageKey | str, *values: list[str]) -> None:
        await self.client.rpush(key, *values)

    @auto_pack_key_async
    async def lrem(self, key: StorageKey | str, *values: list[str]) -> None:
        await self.client.lrem(key, *values)

    @auto_pack_key_async
    async def set(
        self, key: StorageKey | str, value: Any, ex: ExpiryT | None = _MONTH
    ) -> None:
        if isinstance(value, BaseModel):
            value = value.model_dump(exclude_defaults=True)
        if isinstance(value, UserDTO):
            value = value.to_dict()
        await self.client.set(name=key, value=mjson.encode(value), ex=ex)

    async def hset(
        self,
        name: str,
        key: str | None = None,
        value: str | None = None,
        mapping: dict | None = None,
        ex: ExpiryT | None = _MONTH,
    ) -> None:
        await self.client.hset(name, key, value, mapping)
        if ex:
            await self.client.expire(name, ex)

    @auto_pack_key_async
    async def delete(self, key: StorageKey | str) -> None:
        await self.client.delete(key)

    async def close(self) -> None:
        await self.client.aclose(close_connection_pool=True)

    async def save_user(self, key: Any, value: UserDTO, ex: int | None = _MONTH) -> None:
        user_key: UserKey = UserKey(key=key)
        await self.set(key=user_key, value=value, ex=ex)

    async def get_user(self, key: Any) -> UserDTO | None:
        user_key: UserKey = UserKey(key=key)
        return await self.get(key=user_key, validator=UserDTO)

    async def delete_user(self, key: Any) -> None:
        user_key: UserKey = UserKey(key=key)
        await self.delete(user_key)
