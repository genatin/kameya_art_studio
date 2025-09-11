import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import Message, TelegramObject

logger = logging.getLogger(__name__)


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, storage: RedisStorage) -> None:
        self.storage = storage

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        user = f'user{event.from_user.id}'

        check_user = await self.storage.redis.get(name=user)

        if check_user:
            if int(check_user) == 1:
                await self.storage.redis.set(name=user, value=0, ex=1)
                return await event.answer(
                    'ой ой, не так быстро...\n\n'
                    '<i>повторите действие через пару секунд</i>',
                    parse_mode=ParseMode.HTML,
                )
            return
        await self.storage.redis.set(name=user, value=1, ex=1)

        return await handler(event, data)
