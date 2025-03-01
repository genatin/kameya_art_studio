from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware, types

from src.infrastracture import users_repository


class CheckIsUserReg(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]],
        event: types.Message,
        data: Dict[str, Any],
    ) -> Any:
        data["user"] = users_repository.collector.get_user(event.from_user.id)
        await handler(event, data)
