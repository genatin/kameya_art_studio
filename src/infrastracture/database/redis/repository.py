from __future__ import annotations

from typing import Any
from typing import TypeVar

from pydantic import BaseModel
from pydantic import TypeAdapter
from redis.asyncio import Redis
from redis.typing import ExpiryT

from src.application.models import UserDTO
from src.application.utils import mjson
from src.infrastracture.database.redis.key_builder import StorageKey
from src.infrastracture.database.redis.keys import UserKey

T = TypeVar('T', bound=Any)


class RedisRepository:
    def __init__(self, client: Redis) -> None:
        self.client = client

    async def get(self, key: StorageKey | str, validator: type[T]) -> T | None:
        key = key if isinstance(key, str) else key.pack()
        value: Any | None = await self.client.get(key)
        if value is None:
            return None
        value = mjson.decode(value)
        return TypeAdapter[T](validator).validate_python(value)

    async def hgetall(self, key: str) -> dict:
        return await self.client.hgetall(key)

    async def getdel(self, key: StorageKey | str, validator: type[T]) -> Any:
        key = key if isinstance(key, str) else key.pack()
        value: Any | None = await self.client.getdel(key)
        if value is None:
            return None
        value = mjson.decode(value)
        return TypeAdapter[T](validator).validate_python(value)

    async def set(
        self, key: StorageKey | str, value: Any, ex: ExpiryT | None = None
    ) -> None:
        if isinstance(value, BaseModel):
            value = value.model_dump(exclude_defaults=True)
        if isinstance(value, UserDTO):
            value = value.to_dict()
        key = key if isinstance(key, str) else key.pack()
        await self.client.set(name=key, value=mjson.encode(value), ex=ex)

    async def hset(
        self,
        name: str,
        key: str | None = None,
        value: str | None = None,
        mapping: dict | None = None,
        ex: ExpiryT | None = None,
    ) -> None:
        await self.client.hset(name, key, value, mapping)
        if ex:
            await self.client.expire(name, ex)

    async def delete(self, key: StorageKey | str) -> None:
        key = key if isinstance(key, str) else key.pack()
        await self.client.delete(key)

    async def close(self) -> None:
        await self.client.aclose(close_connection_pool=True)

    async def save_user(
        self, key: Any, value: UserDTO, cache_time: int | None = None
    ) -> None:
        user_key: UserKey = UserKey(key=key)
        await self.set(key=user_key, value=value, ex=cache_time)

    async def get_user(self, key: Any) -> UserDTO | None:
        user_key: UserKey = UserKey(key=key)
        return await self.get(key=user_key, validator=UserDTO)

    async def delete_user(self, key: Any) -> None:
        user_key: UserKey = UserKey(key=key)
        await self.delete(user_key)
