from aiogram import Dispatcher
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage
from redis.asyncio.client import Redis

from src.application.utils import mjson


def create_dispatcher(redis: Redis, **handlers) -> Dispatcher:
    """
    :return: Configured ``Dispatcher`` with installed middlewares and included routers
    """
    storage = RedisStorage(
        redis,
        key_builder=DefaultKeyBuilder(with_destiny=True),
        json_dumps=mjson.encode,
        json_loads=mjson.decode,
    )
    dispatcher = Dispatcher(storage=storage, **handlers)
    return dispatcher
