from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware, types

from src.cache.user_collector import user_collector


class CheckIsUserReg(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]],
        event: types.Message,
        data: Dict[str, Any],
    ) -> Any:
        user = user_collector.get_user(event.from_user.id)
        data["user"] = user
        await handler(event, data)
