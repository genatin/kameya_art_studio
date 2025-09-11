from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiogram_dialog import DialogManager

from src.infrastracture.adapters.repositories.repo import UsersRepository
from src.presentation.dialogs.states import FirstSeen


class RegistrationMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Проверяем, зарегистрирован ли пользователь
        dialog_manager: DialogManager = data['dialog_manager']
        repository: UsersRepository = data['repository']
        user = await repository.user.get_user(event.from_user.id)
        if not user:
            await event.answer(
                'Звёзды ждут, чтобы их нарисовали… Но сначала — возьмите кисть в руки.'
            )
            return await dialog_manager.start(FirstSeen.START)
        elif user.reg_is_complete():
            await event.answer('Ой, кажется регистрация не была завершена')
            await repository.user.remove_user(event.from_user.id)
            return await dialog_manager.start(FirstSeen.START)
        return await handler(event, data)
